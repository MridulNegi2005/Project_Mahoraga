"""
Mahoraga Adaptation Engine — FastAPI Bridge
Wraps MahoragaEnv with REST endpoints for the React combat dashboard.
"""
import sys
import os

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

app = FastAPI(title="Mahoraga Adaptation Engine API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Global env instance ──
env: Optional[MahoragaEnv] = None


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


class StepRequest(BaseModel):
    action: int  # 0-4


# ── Endpoints ──

@app.post("/api/reset", response_model=CombatState)
def reset():
    """Reset the environment to initial state."""
    global env
    env = MahoragaEnv()
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
    )


@app.post("/api/step", response_model=CombatState)
def step(req: StepRequest):
    """Execute one turn of combat."""
    global env
    if env is None:
        env = MahoragaEnv()
        env.reset()

    state, reward, done, info = env.step(req.action)

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
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
