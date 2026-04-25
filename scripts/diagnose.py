from env.mahoraga_env import MahoragaEnv

# Simulate: adapt-only agent (always action 0)
env = MahoragaEnv()
state = env.reset()
total_reward = 0
for t in range(25):
    s, r, d, info = env.step(0)
    total_reward += r
    if d:
        break
ahp = s["agent_hp"]
ehp = s["enemy_hp"]
print(f"ADAPT-ONLY: reward={total_reward:.2f}, turns={t+1}, won={ahp > ehp}, enemy_hp={ehp}")

# Simulate: smart agent (adapt 2x then strike, repeat)
env2 = MahoragaEnv()
state = env2.reset()
total_reward2 = 0
for t in range(25):
    turn = t % 3
    if turn < 2:
        a = 0  # adapt PHYSICAL
    else:
        a = 3  # judgment strike
    s, r, d, info = env2.step(a)
    total_reward2 += r
    if d:
        break
ahp2 = s["agent_hp"]
ehp2 = s["enemy_hp"]
print(f"ADAPT+STRIKE: reward={total_reward2:.2f}, turns={t+1}, won={ahp2 > ehp2}, enemy_hp={ehp2}")

# Simulate: random agent (5 episodes)
import random
for ep in range(5):
    env3 = MahoragaEnv()
    env3.reset()
    total = 0
    attacks = 0
    adapts = 0
    for t in range(25):
        a = random.randint(0, 4)
        if a == 3:
            attacks += 1
        if a in [0, 1, 2]:
            adapts += 1
        s, r, d, info = env3.step(a)
        total += r
        if d:
            break
    ahp = s["agent_hp"]
    ehp = s["enemy_hp"]
    print(f"  RANDOM ep{ep+1}: reward={total:.2f}, turns={t+1}, won={ahp>ehp}, attacks={attacks}, adapts={adapts}")
