"""Diagnostic script: run different strategies against Mahoraga and compare results."""
import sys
import os
import random
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from env.mahoraga_env import MahoragaEnv, ACTION_NAMES
from utils.constants import MAX_TURNS

print("=" * 60)
print("  Mahoraga Diagnostics — Strategy Comparison")
print("=" * 60)

# 1) Spam single attack type
print("\n--- Strategy: Spam Physical (action 0 only) ---")
env = MahoragaEnv()
state = env.reset()
total_reward = 0
for t in range(MAX_TURNS):
    state, r, done, info = env.step(0)
    total_reward += r
    if done:
        break
print(f"  reward={total_reward:.2f}, turns={t+1}, "
      f"player_hp={state['player_hp']}, boss_hp={state['boss_hp']}, "
      f"reason={info.get('reason', 'ongoing')}")

# 2) Cycle attacks: 0 -> 1 -> 2 -> 0 -> ...
print("\n--- Strategy: Cycle Attacks (0->1->2) ---")
env2 = MahoragaEnv()
state = env2.reset()
total_reward2 = 0
for t in range(MAX_TURNS):
    action = t % 3
    state, r, done, info = env2.step(action)
    total_reward2 += r
    if done:
        break
print(f"  reward={total_reward2:.2f}, turns={t+1}, "
      f"player_hp={state['player_hp']}, boss_hp={state['boss_hp']}, "
      f"reason={info.get('reason', 'ongoing')}")

# 3) Smart: cycle + domain when resistances high + heal when low
print("\n--- Strategy: Smart (cycle + domain + heal) ---")
env3 = MahoragaEnv()
state = env3.reset()
total_reward3 = 0
domain_used = False
cycle = [0, 1, 2]
for t in range(MAX_TURNS):
    player_hp = state.get("player_hp", 0)
    boss_res = state.get("boss_resistances", {})
    if player_hp < 400 and env3.heal_cooldown_counter == 0:
        action = 4
    elif not domain_used and t >= 4 and sum(1 for v in boss_res.values() if v >= 20) >= 1:
        action = 3
        domain_used = True
    else:
        action = cycle[t % 3]
    state, r, done, info = env3.step(action)
    total_reward3 += r
    if done:
        break
print(f"  reward={total_reward3:.2f}, turns={t+1}, "
      f"player_hp={state['player_hp']}, boss_hp={state['boss_hp']}, "
      f"reason={info.get('reason', 'ongoing')}")

# 4) Random agent (5 episodes)
print("\n--- Strategy: Random Agent (5 episodes) ---")
for ep in range(5):
    env4 = MahoragaEnv()
    env4.reset()
    total = 0
    for t in range(MAX_TURNS):
        a = random.randint(0, 4)
        state, r, done, info = env4.step(a)
        total += r
        if done:
            break
    print(f"  ep{ep+1}: reward={total:.2f}, turns={t+1}, "
          f"player_hp={state['player_hp']}, boss_hp={state['boss_hp']}, "
          f"won={state['boss_hp'] <= 0}")
