"""Trace a medium-difficulty game step by step."""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from env.mahoraga_env import MahoragaEnv, ACTION_NAMES
from utils.constants import MAX_TURNS

print("=" * 60)
print("  Mahoraga Trace — Medium Difficulty")
print("=" * 60)

env = MahoragaEnv(difficulty="medium", debug=False)
state = env.reset()
cycle = [0, 1, 2]
domain_used = False

for t in range(MAX_TURNS):
    player_hp = state.get("player_hp", 0)
    boss_res = state.get("boss_resistances", {"PHYSICAL": 0, "CE": 0, "TECHNIQUE": 0})

    if player_hp < 400 and env.heal_cooldown_counter == 0:
        action = 4
    elif not domain_used and t >= 6 and sum(1 for v in boss_res.values() if v >= 25) >= 1:
        action = 3
        domain_used = True
    else:
        action = cycle[t % 3]

    state, reward, done, info = env.step(action)

    boss_res = state.get("boss_resistances", {})
    print(f"  T{t+1:2d}: {ACTION_NAMES.get(action, '?'):24s} "
          f"dealt={info['damage_dealt']:3d} taken={info['damage_taken']:3d} | "
          f"PlayerHP={state['player_hp']:5d} BossHP={state['boss_hp']:5d} | "
          f"Res: P={boss_res.get('PHYSICAL',0):2d} CE={boss_res.get('CE',0):2d} "
          f"T={boss_res.get('TECHNIQUE',0):2d} | "
          f"Wheels={state.get('boss_wheel_turns', 0)} | "
          f"R={reward:+.2f}")

    if done:
        won = state["boss_hp"] <= 0
        print(f"\n  RESULT: {'VICTORY' if won else 'DEFEAT'} — {info.get('reason')}")
        break
