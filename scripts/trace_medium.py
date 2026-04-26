from env.mahoraga_env import MahoragaEnv
from env.enemy import DifficultyEnemy

TYPE_MAP = {"PHYSICAL": 0, "CE": 1, "TECHNIQUE": 2}

# Trace a medium episode with reactive adaptation
env = MahoragaEnv(enemy=DifficultyEnemy("medium"), debug=True)
s = env.reset()
cycle = 0
for t in range(12):
    last = s.get("last_enemy_attack_type", "PHYSICAL")
    if cycle < 2:
        a = TYPE_MAP.get(last, 0)
        cycle += 1
    else:
        a = 3
        cycle = 0
    s, r, d, info = env.step(a)
    ahp = s["agent_hp"]
    ehp = s["enemy_hp"]
    res = s["resistances"]
    atk = s["last_enemy_attack_type"]
    correct = info["correct_adaptation"]
    print(f"  HP: {ahp}/{ehp} | Res: p={res['physical']} c={res['ce']} t={res['technique']} | EnemyAtk={atk} | Correct={correct}")
    if d:
        print(f"DONE: {info['reason']}")
        break

print("\n\n--- Now try: always adapt to CURRENT enemy attack (impossible but let's see damage) ---")
env2 = MahoragaEnv(enemy=DifficultyEnemy("medium"))
s2 = env2.reset()
cycle2 = 0
for t in range(15):
    # Cheat: look at what enemy will do this turn by peeking
    # We can't actually do this, but let's manually check damage
    if cycle2 < 2:
        # Just always adapt PHYSICAL for now
        a = 0
        cycle2 += 1
    else:
        a = 3
        cycle2 = 0
    s2, r2, d2, info2 = env2.step(a)
    ahp = s2["agent_hp"]
    ehp = s2["enemy_hp"]
    atk = s2["last_enemy_attack_type"]
    dmg = info2["damage_taken"]
    dealt = info2["damage_dealt"]
    print(f"  T{t+1}: EnemyAtk={atk} dmg_taken={dmg} | Action={a} dmg_dealt={dealt} | HP: {ahp}/{ehp}")
    if d2:
        print(f"DONE: {info2['reason']}")
        break
