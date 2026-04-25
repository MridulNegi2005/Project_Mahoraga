"""
Mahoraga Adaptation Engine — FastAPI Bridge
Wraps MahoragaEnv with REST endpoints for the React combat dashboard.
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

from env.mahoraga_env import MahoragaEnv
from utils.constants import MAX_HP, ENEMY_HP, MAX_TURNS

# ── Action lookup ──
ACTION_NAMES = {
    0: "Adapt PHYSICAL",
    1: "Adapt CE",
    2: "Adapt TECHNIQUE",
    3: "Judgment Strike",
    4: "Regeneration",
    None: "Wasted Turn",
}

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
    """Build instruction prompt from environment state."""
    res = state_dict["resistances"]
    return f"""You are Mahoraga, an adaptive combat agent in a turn-based RL environment.

Current State:
- Your HP: {state_dict['agent_hp']}
- Enemy HP: {state_dict['enemy_hp']}
- Resistances: Physical={res['physical']}, CE={res['ce']}, Technique={res['technique']}
- Last Enemy Attack: {state_dict['last_enemy_attack_type']}
- Last Action Taken: {state_dict['last_action']}
- Turn: {state_dict['turn_number']}

Available Actions:
0 = Adapt Physical Resistance (+40 Physical, -20 others)
1 = Adapt CE Resistance (+40 CE, -20 others)
2 = Adapt Technique Resistance (+40 Technique, -20 others)
3 = Judgment Strike (burst if you adapted to enemy's type, resets resistances)
4 = Regeneration (heal 300 HP, 3-turn cooldown)

WINNING STRATEGY:
1. Adapt to enemy attack type 2 times to build resistance + stacks
2. Use Judgment Strike for burst damage (350 + 50 per stack)
3. Repeat: Adapt → Adapt → Strike
4. Heal ONLY when HP is critically low

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


# ── Helper ──
def make_combat_state(state, env_instance, turn_log=None, llm_raw=None):
    return CombatState(
        enemy_hp=state["enemy_hp"],
        enemy_hp_max=ENEMY_HP,
        mahoraga_hp=state["agent_hp"],
        mahoraga_hp_max=MAX_HP,
        resistances=Resistances(
            Physical=state["resistances"]["physical"],
            CE=state["resistances"]["ce"],
            Technique=state["resistances"]["technique"],
        ),
        adaptation_stack=env_instance.adaptation_stack if hasattr(env_instance, 'adaptation_stack') else 0,
        heal_cooldown=env_instance.heal_cooldown_counter,
        turn_number=state["turn_number"],
        max_turns=MAX_TURNS,
        done=False,
        done_reason=None,
        turn_log=turn_log,
        difficulty=current_difficulty,
        llm_raw=llm_raw,
    )


# ── Endpoints ──

@app.post("/api/reset", response_model=CombatState)
def reset(req: ResetRequest = ResetRequest()):
    """Reset the environment to initial state with specified difficulty."""
    global env, current_difficulty
    current_difficulty = req.difficulty
    env = MahoragaEnv(difficulty=current_difficulty)
    env.reset()

    return CombatState(
        enemy_hp=ENEMY_HP,
        enemy_hp_max=ENEMY_HP,
        mahoraga_hp=MAX_HP,
        mahoraga_hp_max=MAX_HP,
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
        correct_adaptation=info["correct_adaptation"],
        reward=round(reward, 2),
        heal_blocked=info.get("heal_on_cooldown", False),
    )

    return CombatState(
        enemy_hp=state["enemy_hp"],
        enemy_hp_max=ENEMY_HP,
        mahoraga_hp=state["agent_hp"],
        mahoraga_hp_max=MAX_HP,
        resistances=Resistances(
            Physical=state["resistances"]["physical"],
            CE=state["resistances"]["ce"],
            Technique=state["resistances"]["technique"],
        ),
        adaptation_stack=info["adaptation_stack"],
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
    """Rule-based fallback agent mimicking the trained LLM's strategy."""
    if env is None:
        return 0

    state = env._get_state()
    agent_hp = state["agent_hp"]
    res = state["resistances"]

    # Heal if critical HP and cooldown ready
    if agent_hp < 300 and env.heal_cooldown_counter == 0:
        return 4

    # Judgment Strike if stacks >= 3 (or >= 2 and adapted to right type)
    if env.adaptation_stack >= 3:
        return 3
    if env.adaptation_stack >= 2 and env.last_adapted_category == state.get("last_enemy_attack_type"):
        return 3

    # Adapt to last enemy attack type
    last_attack = state.get("last_enemy_attack_type")
    adapt_map = {"PHYSICAL": 0, "CE": 1, "TECHNIQUE": 2}
    if last_attack and last_attack in adapt_map:
        return adapt_map[last_attack]

    # Default: adapt to weakest resistance
    weakest = min(res, key=res.get)
    return adapt_map.get(weakest.upper(), 0)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
