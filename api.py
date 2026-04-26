"""
Mahoraga Boss Fight — FastAPI Bridge
Wraps MahoragaEnv with REST endpoints for the React combat dashboard.
The RL agent is the PLAYER (sorcerer) fighting Mahoraga (adaptive boss).
Includes LLM auto-play via trained Qwen 2.5 3B LoRA model.
"""
import sys
import os
import re

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

from env.mahoraga_env import MahoragaEnv, ACTION_NAMES
from utils.constants import PLAYER_HP, MAHORAGA_HP, MAX_TURNS

app = FastAPI(title="Mahoraga Adaptation Engine API", version="3.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Global state ──
env: Optional[MahoragaEnv] = None
current_difficulty: str = "hard"

# ── LLM Model (lazy loaded) ──
llm_model = None
llm_tokenizer = None
llm_loaded = False
llm_error: Optional[str] = None


def load_llm():
    """Load Qwen 2.5 3B + LoRA for auto-play. Called once on first use."""
    global llm_model, llm_tokenizer, llm_loaded, llm_error

    if llm_loaded:
        return True
    if llm_error:
        return False

    model_path = os.path.join(os.path.dirname(__file__), "mahoraga_loral_final")

    if not os.path.exists(os.path.join(model_path, "adapter_config.json")):
        llm_error = f"LoRA weights not found at {model_path}"
        print(f"[LLM] ERROR: {llm_error}")
        return False

    try:
        print("[LLM] Loading Qwen 2.5 3B + LoRA (4-bit)... This may take 30-60s.")

        # Try unsloth first (faster), fall back to transformers+peft
        try:
            from unsloth import FastLanguageModel
            import torch

            llm_model, llm_tokenizer = FastLanguageModel.from_pretrained(
                model_name=model_path,
                max_seq_length=1024,
                dtype=None,
                load_in_4bit=True,
            )
            FastLanguageModel.for_inference(llm_model)
            print("[LLM] Model loaded via Unsloth.")

        except ImportError:
            print("[LLM] Unsloth not found, using transformers + peft...")
            import torch
            from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
            from peft import PeftModel

            base_model_name = "Qwen/Qwen2.5-3B-Instruct"
            bnb_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.float16,
                bnb_4bit_use_double_quant=True,
            )

            base_model = AutoModelForCausalLM.from_pretrained(
                base_model_name,
                quantization_config=bnb_config,
                device_map="auto",
                trust_remote_code=True,
            )
            llm_model = PeftModel.from_pretrained(base_model, model_path)
            llm_tokenizer = AutoTokenizer.from_pretrained(model_path)
            llm_model.eval()
            print("[LLM] Model loaded via transformers + peft.")

        llm_loaded = True
        return True

    except Exception as e:
        llm_error = str(e)
        print(f"[LLM] Failed to load model: {llm_error}")
        return False


def build_prompt(state_dict):
    """Build instruction prompt for the player (sorcerer) fighting Mahoraga."""
    boss_res = state_dict.get("boss_resistances", {
        "PHYSICAL": state_dict["resistances"]["physical"],
        "CE": state_dict["resistances"]["ce"],
        "TECHNIQUE": state_dict["resistances"]["technique"],
    })
    history = state_dict.get("attack_history", [])
    crit_stack = state_dict.get("crit_stack", 0)
    domain_used = state_dict.get("domain_used", False)
    domain_active = state_dict.get("domain_active", False)
    heal_cd = state_dict.get("heal_cooldown", 0)
    wheel_turns = state_dict.get("boss_wheel_turns", 0)

    history_str = " -> ".join(history) if len(history) >= 2 else "Not enough data yet"
    highest_key = max(boss_res, key=boss_res.get)
    highest_val = boss_res[highest_key]
    domain_str = "ACTIVE (+75% DMG)" if domain_active else ("USED" if domain_used else "AVAILABLE")
    heal_str = f"COOLDOWN ({heal_cd} turns)" if heal_cd > 0 else "READY"

    return f"""You are a sorcerer fighting Mahoraga, an adaptive boss that passively gains resistance to attack types you repeat.

Current State:
- Your HP: {state_dict.get('player_hp', state_dict.get('agent_hp', 0))}
- Mahoraga HP: {state_dict.get('boss_hp', state_dict.get('enemy_hp', 0))}
- Mahoraga Resistances: Physical={boss_res['PHYSICAL']}%, CE={boss_res['CE']}%, Technique={boss_res['TECHNIQUE']}%
- Mahoraga Wheel Turns: {wheel_turns} (more = stronger boss attacks)
- Last Boss Attack: {state_dict.get('last_boss_attack', 'None')}
- Turn: {state_dict['turn_number']}/30

Your Status:
- Crit Stack: {crit_stack}/3 (3 = next same-type hit does 1.5x)
- Domain Expansion: {domain_str}
- Heal: {heal_str}

Your Attack History: {history_str}

WARNING: Mahoraga's Highest Resistance: {highest_key} ({highest_val}%) — AVOID this type!

Available Actions:
0 = Physical Strike (130 base dmg, reduced by boss Physical resistance)
1 = CE Blast (150 base dmg, 15% chance for BLACK FLASH = 2.5x dmg!)
2 = Technique Strike (190 base dmg, highest risk/reward)
3 = Domain Expansion (ONCE per fight: resets boss resistances, +75% dmg for 3 turns)
4 = Reversed Cursed Technique (heal 250 HP, 4-turn cooldown)

STRATEGY GUIDE:
1. VARY your attacks — if you spam one type, Mahoraga adapts and becomes resistant
2. Use CE attacks for chance of Black Flash (2.5x damage!)
3. Save Domain Expansion for when Mahoraga has high resistances
4. Kill Mahoraga FAST — the longer the fight, the stronger it gets
5. Heal ONLY when HP is critically low

Choose the best action. Return ONLY a single integer (0-4)."""


def parse_action(text):
    """Extract integer action 0-4 from model output."""
    text = text.strip()
    if text in ['0', '1', '2', '3', '4']:
        return int(text)
    match = re.search(r'[0-4]', text)
    if match:
        return int(match.group())
    return 0


def llm_choose_action(state_dict):
    """Use the trained LLM to pick an action given the current state."""
    import torch

    prompt = build_prompt(state_dict)
    messages = [
        {"role": "system", "content": "You are a combat AI. Respond with ONLY a single integer 0-4."},
        {"role": "user", "content": prompt}
    ]

    input_text = llm_tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = llm_tokenizer(input_text, return_tensors="pt").to(llm_model.device)

    with torch.no_grad():
        outputs = llm_model.generate(
            **inputs,
            max_new_tokens=8,
            temperature=0.7,
            do_sample=True,
            pad_token_id=llm_tokenizer.eos_token_id
        )

    response = llm_tokenizer.decode(outputs[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True)
    action = parse_action(response)
    return action, response.strip()


# ── Response schemas ──
class TurnLog(BaseModel):
    turn: int
    enemy_attack_type: str
    enemy_subtype: str
    mahoraga_action: str
    damage_taken: int
    damage_dealt: int
    correct_adaptation: bool
    reward: float
    heal_blocked: bool


class Resistances(BaseModel):
    Physical: int
    CE: int
    Technique: int


class CombatState(BaseModel):
    player_hp: int
    player_hp_max: int
    boss_hp: int
    boss_hp_max: int
    # Legacy aliases for frontend compat
    enemy_hp: int
    enemy_hp_max: int
    mahoraga_hp: int
    mahoraga_hp_max: int
    resistances: Resistances
    adaptation_stack: int
    heal_cooldown: int
    turn_number: int
    max_turns: int
    done: bool
    done_reason: Optional[str] = None
    turn_log: Optional[TurnLog] = None
    difficulty: str = "hard"
    llm_raw: Optional[str] = None


class StepRequest(BaseModel):
    action: int  # 0-4


class ResetRequest(BaseModel):
    difficulty: str = "hard"


def _make_resistances(state):
    res = state["resistances"]
    return Resistances(
        Physical=res["physical"], CE=res["ce"], Technique=res["technique"],
    )


# ── Endpoints ──

@app.post("/api/reset", response_model=CombatState)
def reset(req: ResetRequest = ResetRequest()):
    """Reset the environment to initial state with specified difficulty."""
    global env, current_difficulty
    current_difficulty = req.difficulty
    env = MahoragaEnv(difficulty=current_difficulty)
    env.reset()

    boss_hp = env.boss.max_hp
    return CombatState(
        player_hp=PLAYER_HP,
        player_hp_max=PLAYER_HP,
        boss_hp=boss_hp,
        boss_hp_max=boss_hp,
        enemy_hp=boss_hp,
        enemy_hp_max=boss_hp,
        mahoraga_hp=PLAYER_HP,
        mahoraga_hp_max=PLAYER_HP,
        resistances=Resistances(Physical=0, CE=0, Technique=0),
        adaptation_stack=0,
        heal_cooldown=0,
        turn_number=0,
        max_turns=MAX_TURNS,
        done=False,
        done_reason=None,
        turn_log=None,
        difficulty=current_difficulty,
    )


def _do_step(action, llm_raw=None):
    """Execute one turn of combat (shared by manual step and auto-step)."""
    global env
    if env is None:
        env = MahoragaEnv(difficulty=current_difficulty)
        env.reset()

    state, reward, done, info = env.step(action)
    action_name = ACTION_NAMES.get(env.last_action, "Unknown")

    turn_log = TurnLog(
        turn=state["turn_number"],
        enemy_attack_type=state["last_enemy_attack_type"] or "NONE",
        enemy_subtype=state["last_enemy_subtype"] or "NONE",
        mahoraga_action=action_name,
        damage_taken=info["damage_taken"],
        damage_dealt=info["damage_dealt"],
        correct_adaptation=info.get("correct_adaptation", info.get("adapted", False)),
        reward=round(reward, 2),
        heal_blocked=info.get("heal_on_cooldown", False),
    )

    boss_hp_max = env.boss.max_hp
    return CombatState(
        player_hp=state["player_hp"],
        player_hp_max=PLAYER_HP,
        boss_hp=state["boss_hp"],
        boss_hp_max=boss_hp_max,
        enemy_hp=state["enemy_hp"],
        enemy_hp_max=boss_hp_max,
        mahoraga_hp=state["agent_hp"],
        mahoraga_hp_max=PLAYER_HP,
        resistances=_make_resistances(state),
        adaptation_stack=info.get("adaptation_stack", env.boss.total_wheel_turns),
        heal_cooldown=env.heal_cooldown_counter,
        turn_number=state["turn_number"],
        max_turns=MAX_TURNS,
        done=done,
        done_reason=info.get("reason"),
        turn_log=turn_log,
        difficulty=current_difficulty,
        llm_raw=llm_raw,
    )


@app.post("/api/step", response_model=CombatState)
def step(req: StepRequest):
    """Execute one manual turn of combat."""
    return _do_step(req.action)


@app.post("/api/auto-step", response_model=CombatState)
def auto_step():
    """Execute one turn using the trained LLM to choose the action."""
    global env
    if env is None:
        env = MahoragaEnv(difficulty=current_difficulty)
        env.reset()

    # Load model on first call
    if not llm_loaded and not load_llm():
        # Fallback to smart rule-based agent
        action = _smart_agent_action()
        return _do_step(action, llm_raw="[FALLBACK] rule-based")

    # Get LLM's state observation
    state_dict = env._get_state()
    action, raw_output = llm_choose_action(state_dict)
    return _do_step(action, llm_raw=raw_output)


@app.get("/api/model-status")
def model_status():
    """Check if the LLM model is loaded."""
    return {
        "loaded": llm_loaded,
        "error": llm_error,
        "model_path": os.path.join(os.path.dirname(__file__), "mahoraga_loral_final"),
    }


def _smart_agent_action():
    """Rule-based fallback: sorcerer fighting Mahoraga.

    Strategy: cycle attacks to avoid adaptation, use domain when
    resistances are high, heal when low.
    """
    if env is None:
        return 0

    state = env._get_state()
    player_hp = state.get("player_hp", state.get("agent_hp", 0))
    boss_res = state.get("boss_resistances", {"PHYSICAL": 0, "CE": 0, "TECHNIQUE": 0})

    if player_hp < 400 and env.heal_cooldown_counter == 0:
        return 4

    if not env.domain_used:
        high = sum(1 for v in boss_res.values() if v >= 30)
        if high >= 2:
            return 3

    weakest = min(boss_res, key=boss_res.get)
    action_map = {"PHYSICAL": 0, "CE": 1, "TECHNIQUE": 2}
    return action_map.get(weakest, 0)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
