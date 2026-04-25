import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from env.mahoraga_env import MahoragaEnv
from env.mechanics import (
    new_resistances, apply_resistance_change, compute_enemy_damage,
    compute_judgment_damage
)
from env.enemy import Enemy, PatternEnemy
from env.rewards import compute_rewards
from utils.constants import SUBTYPES, ATTACK_TYPES, MAX_HP

PASS = 0
FAIL = 0


def check(name, condition):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  [PASS] {name}")
    else:
        FAIL += 1
        print(f"  [FAIL] {name}")


def test_resistance_update():
    print("\n--- Test: Resistance Update ---")
    res = new_resistances()
    res = apply_resistance_change(res, "PHYSICAL")
    check("PHYSICAL +40", res["PHYSICAL"] == 40)
    check("CE -20 clamped to 0", res["CE"] == 0)
    check("TECHNIQUE -20 clamped to 0", res["TECHNIQUE"] == 0)

    # Second adapt
    res = apply_resistance_change(res, "PHYSICAL")
    check("PHYSICAL +40 again = 80", res["PHYSICAL"] == 80)
    check("CE stays 0", res["CE"] == 0)
    check("TECHNIQUE stays 0", res["TECHNIQUE"] == 0)


def test_clamp_logic():
    print("\n--- Test: Clamp Logic ---")
    # Push beyond max
    res = {"PHYSICAL": 70, "CE": 10, "TECHNIQUE": 10}
    res = apply_resistance_change(res, "PHYSICAL")
    check("PHYSICAL clamped to 80 (70+40)", res["PHYSICAL"] == 80)
    check("CE clamped to 0 (10-20)", res["CE"] == 0)
    check("TECHNIQUE clamped to 0 (10-20)", res["TECHNIQUE"] == 0)


def test_damage_formula():
    print("\n--- Test: Damage Formula ---")
    res = new_resistances()  # all 0
    dmg = compute_enemy_damage("PHYSICAL", res)
    check("PHYSICAL full damage = 120", dmg == 120)

    dmg = compute_enemy_damage("CE", res)
    check("CE full damage = 150", dmg == 150)

    dmg = compute_enemy_damage("TECHNIQUE", res)
    check("TECHNIQUE full damage = 220", dmg == 220)

    # With 50 resistance
    res["PHYSICAL"] = 50
    dmg = compute_enemy_damage("PHYSICAL", res)
    check("PHYSICAL with 50 res = 60", dmg == 60)


def test_judgment_damage():
    print("\n--- Test: Judgment Damage ---")
    res = new_resistances()
    dmg = compute_judgment_damage(res, "PHYSICAL")
    check("Base judgment (0 res) = 100", dmg == 100)

    # Burst only when MATCHING type > 60
    res["PHYSICAL"] = 80
    dmg = compute_judgment_damage(res, "PHYSICAL")
    check("Burst judgment (matching res > 60) = 350", dmg == 350)

    # Non-matching type high resistance should NOT burst
    res2 = new_resistances()
    res2["CE"] = 80
    dmg = compute_judgment_damage(res2, "PHYSICAL")
    check("No burst when non-matching res > 60 = 100", dmg == 100)


def test_episode_termination():
    print("\n--- Test: Episode Termination ---")
    env = MahoragaEnv()
    env.reset()

    # Run 25 turns — alternate heal and adapt to survive (cooldown-safe)
    done = False
    for i in range(25):
        if env.heal_cooldown_counter == 0:
            _, _, done, info = env.step(4)  # Heal when available
        else:
            _, _, done, info = env.step(0)  # Adapt otherwise
    check("Episode ends at turn 25", done is True)
    check("Reason is turn limit", info.get("reason") == "Turn limit reached")


def test_actions_behave_correctly():
    print("\n--- Test: Action Behavior ---")

    # Adapt action
    env = MahoragaEnv()
    env.reset()
    state, _, _, _ = env.step(0)  # Adapt PHYSICAL
    check("Adapt PHYSICAL sets res to 40", state["resistances"]["physical"] == 40)

    # Judgment Strike resets resistances
    env.reset()
    env.step(0)  # Build resistance
    env.step(0)  # Build more
    state, _, _, _ = env.step(3)  # Judgment Strike
    check("Judgment resets resistances", state["resistances"]["physical"] == 0)
    check("Judgment damages enemy", state["enemy_hp"] < 1000)

    # Regeneration heals but does NOT reset resistances
    env.reset()
    env.step(0)  # Take a hit, build resistance
    hp_before = env.agent_hp
    res_before = env.resistances["PHYSICAL"]
    state, _, _, _ = env.step(4)  # Regeneration
    check("Regeneration heals agent", state["agent_hp"] > hp_before - 120)
    check("Regeneration does NOT reset resistances", state["resistances"]["physical"] == res_before)


def test_adaptation_stack():
    print("\n--- Test: Adaptation Stack ---")
    env = MahoragaEnv()
    env.reset()

    # Enemy always attacks PHYSICAL in Phase 1
    # Action 0 = Adapt PHYSICAL = correct adaptation
    env.step(0)
    check("Stack +1 on correct adapt", env.adaptation_stack == 1)
    env.step(0)
    check("Stack +2 on second correct adapt", env.adaptation_stack == 2)

    # Wrong adaptation
    env.reset()
    env.step(1)  # Adapt CE, but enemy attacks PHYSICAL
    check("Stack stays 0 on wrong adapt", env.adaptation_stack == 0)

    # Judgment consumes stack
    env.reset()
    env.step(0)  # correct adapt, stack = 1
    env.step(0)  # correct adapt, stack = 2
    env.step(3)  # Judgment Strike, consumes stack
    check("Stack reset to 0 after Judgment", env.adaptation_stack == 0)


def test_invalid_action():
    print("\n--- Test: Invalid Action ---")
    env = MahoragaEnv()
    env.reset()
    try:
        env.step(5)
        check("Rejects action 5", False)
    except ValueError:
        check("Rejects action 5", True)

    try:
        env.step(-1)
        check("Rejects action -1", False)
    except ValueError:
        check("Rejects action -1", True)


def test_heal_cooldown():
    print("\n--- Test: Heal Cooldown ---")
    env = MahoragaEnv()
    env.reset()

    # First heal should work
    state, _, _, info = env.step(4)
    check("First heal works", info["heal_on_cooldown"] is False)
    check("Cooldown set to 3", env.heal_cooldown_counter == 3)

    # Next 3 turns: heal should be blocked
    # Turn 2: cooldown was 3, decremented to 2 at start, still > 0
    _, _, _, info2 = env.step(4)
    check("Heal blocked on turn 2 (cooldown)", info2["heal_on_cooldown"] is True)

    # Turn 3: cooldown was 2, decremented to 1
    _, _, _, info3 = env.step(4)
    check("Heal blocked on turn 3 (cooldown)", info3["heal_on_cooldown"] is True)

    # Turn 4: cooldown was 1, decremented to 0 — heal should work now
    _, _, _, info4 = env.step(4)
    check("Heal available on turn 4 (cooldown expired)", info4["heal_on_cooldown"] is False)


def test_heal_preserves_resistances():
    print("\n--- Test: Heal Preserves Resistances ---")
    env = MahoragaEnv()
    env.reset()

    # Build up resistance first
    env.step(0)  # PHYSICAL +40
    env.step(0)  # PHYSICAL +80
    res_before = env.resistances.copy()

    # Heal should NOT reset
    env.step(4)
    # After heal, enemy attacks (PHYSICAL, 120 base, but with 80 res => 24 dmg)
    # Resistances should remain from before heal (no change from heal itself)
    # But enemy damage is applied before agent acts, so resistances at time of heal = res_before
    check("PHYSICAL res preserved after heal", env.resistances["PHYSICAL"] == res_before["PHYSICAL"])
    check("CE res preserved after heal", env.resistances["CE"] == res_before["CE"])
    check("TECHNIQUE res preserved after heal", env.resistances["TECHNIQUE"] == res_before["TECHNIQUE"])


def test_judgment_burst_only_matching():
    print("\n--- Test: Judgment Burst Only On Matching Type ---")
    env = MahoragaEnv()
    env.reset()

    # Build CE resistance high (enemy attacks PHYSICAL)
    env.step(1)  # CE +40
    env.step(1)  # CE +80
    # CE is 80 (> 60), but enemy attacks PHYSICAL — should NOT burst
    enemy_hp_before = env.enemy_hp
    env.step(3)  # Judgment Strike
    damage_dealt = enemy_hp_before - env.enemy_hp
    # No stack bonus (adapt CE != PHYSICAL), base judgment = 100
    check("No burst when wrong type has high res (dmg=100)", damage_dealt == 100)

    # Now build PHYSICAL resistance high and burst
    env.reset()
    env.step(0)  # PHYSICAL +40
    env.step(0)  # PHYSICAL +80, stack = 2
    enemy_hp_before = env.enemy_hp
    env.step(3)  # Judgment Strike — PHYSICAL > 60 and enemy attacks PHYSICAL
    damage_dealt = enemy_hp_before - env.enemy_hp
    # burst 350 + stack 2*50 = 450
    check("Burst when matching type has high res (dmg=450)", damage_dealt == 450)


def test_info_dict_fields():
    print("\n--- Test: Info Dict Fields ---")
    env = MahoragaEnv()
    env.reset()
    _, _, _, info = env.step(0)
    required_keys = ["damage_taken", "damage_dealt", "correct_adaptation", "adaptation_stack", "heal_on_cooldown"]
    all_present = all(k in info for k in required_keys)
    check("Info dict has all required fields", all_present)
    check("correct_adaptation is True for matching adapt", info["correct_adaptation"] is True)
    check("damage_taken > 0", info["damage_taken"] > 0)
    check("damage_dealt = 0 for adapt action", info["damage_dealt"] == 0)


# ========== PHASE 2 TESTS ==========

def test_subtype_mapping():
    print("\n--- Test: Subtype Mapping ---")
    for attack_type in ATTACK_TYPES:
        check(f"{attack_type} has subtypes", attack_type in SUBTYPES)
        check(f"{attack_type} has 3 subtypes", len(SUBTYPES[attack_type]) == 3)

    # Verify specific subtypes
    check("PHYSICAL has PIERCE", "PIERCE" in SUBTYPES["PHYSICAL"])
    check("CE has BEAM", "BEAM" in SUBTYPES["CE"])
    check("TECHNIQUE has DELAYED", "DELAYED" in SUBTYPES["TECHNIQUE"])


def test_pierce_bypass():
    print("\n--- Test: PIERCE Bypass ---")
    res = new_resistances()
    res["PHYSICAL"] = 50

    # Normal subtype
    normal_dmg = compute_enemy_damage("PHYSICAL", res, subtype="SLASH")
    # PIERCE bypasses 20% resistance: effective = 50 * 0.8 = 40
    pierce_dmg = compute_enemy_damage("PHYSICAL", res, subtype="PIERCE")

    check("PIERCE does more damage than SLASH at 50 res", pierce_dmg > normal_dmg)
    # Normal: 120 * (1 - 50/100) = 60
    check("Normal SLASH damage = 60", normal_dmg == 60)
    # Pierce: 120 * (1 - 40/100) = 72
    check("PIERCE damage = 72 (20% bypass)", pierce_dmg == 72)

    # At 0 resistance, PIERCE should be same as normal
    res_zero = new_resistances()
    normal_zero = compute_enemy_damage("PHYSICAL", res_zero, subtype="SLASH")
    pierce_zero = compute_enemy_damage("PHYSICAL", res_zero, subtype="PIERCE")
    check("PIERCE same as normal at 0 resistance", normal_zero == pierce_zero)


def test_pattern_enemy_cycle():
    print("\n--- Test: Pattern Enemy Cycle ---")
    enemy = PatternEnemy()
    enemy.deviation_chance = 0  # Disable randomness for deterministic test

    attack1 = enemy.get_attack()
    check("Pattern step 1 = PHYSICAL", attack1["type"] == "PHYSICAL")
    attack2 = enemy.get_attack()
    check("Pattern step 2 = CE", attack2["type"] == "CE")
    attack3 = enemy.get_attack()
    check("Pattern step 3 = TECHNIQUE", attack3["type"] == "TECHNIQUE")
    attack4 = enemy.get_attack()
    check("Pattern step 4 = PHYSICAL (cycle)", attack4["type"] == "PHYSICAL")

    # Verify dict format
    check("Attack has 'type' key", "type" in attack1)
    check("Attack has 'subtype' key", "subtype" in attack1)
    check("Attack has 'base_damage' key", "base_damage" in attack1)
    check("Subtype is valid for type", attack1["subtype"] in SUBTYPES[attack1["type"]])


def test_pattern_enemy_randomness():
    print("\n--- Test: Pattern Enemy Randomness ---")
    enemy = PatternEnemy()
    enemy.deviation_chance = 1.0  # Force full randomness

    # Run many attacks, should see variety
    types_seen = set()
    for _ in range(50):
        attack = enemy.get_attack()
        types_seen.add(attack["type"])
        # Verify subtype always valid for its type
        check_valid = attack["subtype"] in SUBTYPES[attack["type"]]
        if not check_valid:
            check(f"Subtype {attack['subtype']} valid for {attack['type']}", False)
            return

    check("Random mode produces multiple attack types", len(types_seen) > 1)


def test_enemy_dict_format():
    print("\n--- Test: Enemy Dict Format ---")
    enemy = Enemy()
    attack = enemy.get_attack()
    check("Phase 1 enemy returns dict", isinstance(attack, dict))
    check("Dict has 'type'", "type" in attack)
    check("Dict has 'subtype'", "subtype" in attack)
    check("Dict has 'base_damage'", "base_damage" in attack)
    check("Phase 1 type is PHYSICAL", attack["type"] == "PHYSICAL")
    check("Phase 1 subtype is valid", attack["subtype"] in SUBTYPES["PHYSICAL"])


def test_rl_observation_uses_3_types_only():
    print("\n--- Test: RL Observation Uses Only 3 Types ---")
    env = MahoragaEnv()
    env.reset()
    state, _, _, _ = env.step(0)

    # Observation should only expose top-level types
    check("last_enemy_attack_type is a valid RL type",
          state["last_enemy_attack_type"] in ATTACK_TYPES)
    check("Resistances use 3 keys only",
          set(state["resistances"].keys()) == {"physical", "ce", "technique"})


# ========== PHASE 3 TESTS ==========

def test_adaptation_reward():
    print("\n--- Test: Adaptation Reward ---")
    env = MahoragaEnv()
    env.reset()

    # Correct adaptation (action 0 = PHYSICAL, enemy = PHYSICAL)
    _, reward, _, info = env.step(0)
    breakdown = info["reward_breakdown"]
    check("Correct adapt gives +1.5", breakdown["adaptation"] == 1.5)

    # Wrong adaptation
    env.reset()
    _, reward, _, info = env.step(1)  # CE adapt vs PHYSICAL enemy
    breakdown = info["reward_breakdown"]
    check("Wrong adapt gives 0.0", breakdown["adaptation"] == 0.0)


def test_damage_rewards():
    print("\n--- Test: Damage Rewards ---")
    env = MahoragaEnv()
    env.reset()

    # Taking damage should produce negative survival reward
    _, _, _, info = env.step(0)
    breakdown = info["reward_breakdown"]
    check("Survival reward is negative (took damage)", breakdown["survival"] < 0)

    # Dealing damage should produce positive combat reward
    env.reset()
    _, _, _, info = env.step(3)  # Judgment Strike
    breakdown = info["reward_breakdown"]
    check("Combat reward is positive (dealt damage)", breakdown["combat"] > 0)

    # Adapt action = 0 damage dealt = 0 combat reward
    env.reset()
    _, _, _, info = env.step(0)
    breakdown = info["reward_breakdown"]
    check("Combat reward is 0 for adapt action", breakdown["combat"] == 0.0)


def test_heal_penalty():
    print("\n--- Test: Heal Penalty (Anti-Cowardice) ---")
    env = MahoragaEnv()
    env.reset()
    # Agent starts at 1200 HP, 0.7 * 1200 = 840
    # After 1 hit of ~120, HP ~1080 which is > 840 still
    _, _, _, info = env.step(4)  # Heal at high HP
    breakdown = info["reward_breakdown"]
    check("Heal at high HP penalized (-1.0)", breakdown["anti_cowardice"] == -1.0)

    # Heal at low HP should NOT be penalized
    env.reset()
    # Take lots of damage first
    for _ in range(7):
        env.step(1)  # Wrong adapt, take full damage each turn
    # Agent HP should be well below 0.7 * 1200 = 840
    check("Agent HP is low enough", env.agent_hp < 0.7 * MAX_HP)
    _, _, _, info = env.step(4)  # Heal at low HP
    breakdown = info["reward_breakdown"]
    check("Heal at low HP NOT penalized (0.0)", breakdown["anti_cowardice"] == 0.0)


def test_terminal_reward():
    print("\n--- Test: Terminal Reward ---")
    # Use reward function directly for cleaner testing
    # Win scenario: agent HP > enemy HP
    info_win = {"damage_taken": 0, "damage_dealt": 100, "correct_adaptation": False}
    state_win = {"agent_hp": 500, "enemy_hp": 0}
    rewards = compute_rewards(info_win, state_win, 3, done=True)
    check("Win terminal = +5.0", rewards["terminal"] == 5.0)

    # Loss scenario: agent HP <= enemy HP
    info_loss = {"damage_taken": 100, "damage_dealt": 0, "correct_adaptation": False}
    state_loss = {"agent_hp": 0, "enemy_hp": 500}
    rewards = compute_rewards(info_loss, state_loss, 0, done=True)
    check("Loss terminal = -5.0", rewards["terminal"] == -5.0)

    # Not done: no terminal reward
    rewards_nd = compute_rewards(info_win, state_win, 0, done=False)
    check("Not done terminal = 0.0", rewards_nd["terminal"] == 0.0)


def test_reward_breakdown_in_info():
    print("\n--- Test: Reward Breakdown In Info ---")
    env = MahoragaEnv()
    env.reset()
    _, reward, _, info = env.step(0)

    check("Info has reward_breakdown", "reward_breakdown" in info)
    breakdown = info["reward_breakdown"]
    expected_keys = {"survival", "combat", "adaptation", "anti_cowardice", "efficiency", "terminal"}
    check("Breakdown has all 6 components", set(breakdown.keys()) == expected_keys)

    # Total reward should equal sum of components
    total = sum(breakdown.values())
    check("Total reward = sum of components", abs(reward - total) < 1e-9)

    # Reward is no longer 0.0 placeholder
    check("Reward is not placeholder 0.0", reward != 0.0 or total == 0.0)


def test_no_reward_for_nothing():
    print("\n--- Test: No Free Rewards ---")
    env = MahoragaEnv()
    env.reset()

    # Heal on cooldown = wasted turn = should get no positive reward
    env.step(4)  # First heal (works)
    _, reward, _, info = env.step(4)  # Blocked heal (wasted)
    breakdown = info["reward_breakdown"]
    # No adaptation, no combat, no efficiency — only survival (negative)
    check("No adaptation reward on wasted turn", breakdown["adaptation"] == 0.0)
    check("No combat reward on wasted turn", breakdown["combat"] == 0.0)
    check("No efficiency bonus on wasted turn", breakdown["efficiency"] == 0.0)


if __name__ == "__main__":
    print("=" * 50)
    print("  MahoragaEnv Phase 1+2+3 Tests")
    print("=" * 50)

    # Phase 1 tests
    test_resistance_update()
    test_clamp_logic()
    test_damage_formula()
    test_judgment_damage()
    test_episode_termination()
    test_actions_behave_correctly()
    test_adaptation_stack()
    test_invalid_action()
    test_heal_cooldown()
    test_heal_preserves_resistances()
    test_judgment_burst_only_matching()
    test_info_dict_fields()

    # Phase 2 tests
    test_subtype_mapping()
    test_pierce_bypass()
    test_pattern_enemy_cycle()
    test_pattern_enemy_randomness()
    test_enemy_dict_format()
    test_rl_observation_uses_3_types_only()

    # Phase 3 tests
    test_adaptation_reward()
    test_damage_rewards()
    test_heal_penalty()
    test_terminal_reward()
    test_reward_breakdown_in_info()
    test_no_reward_for_nothing()

    print("\n" + "=" * 50)
    print(f"  Results: {PASS} passed, {FAIL} failed")
    print("=" * 50)

    if FAIL > 0:
        sys.exit(1)
