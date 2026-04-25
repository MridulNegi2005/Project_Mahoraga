import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from env.mahoraga_env import MahoragaEnv
from env.mechanics import (
    new_resistances, apply_resistance_change, compute_enemy_damage,
    compute_judgment_damage, check_correct_adaptation
)
from env.enemy import CurriculumEnemy
from env.rewards import compute_rewards
from utils.constants import SUBTYPES, ATTACK_TYPES, MAX_HP, ENEMY_HP

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


# ========== PHASE 1 CORE TESTS ==========

def test_resistance_update():
    print("\n--- Test: Resistance Update ---")
    res = new_resistances()
    res = apply_resistance_change(res, "PHYSICAL")
    check("PHYSICAL +40", res["PHYSICAL"] == 40)
    check("CE -20 clamped to 0", res["CE"] == 0)
    check("TECHNIQUE -20 clamped to 0", res["TECHNIQUE"] == 0)

    res = apply_resistance_change(res, "PHYSICAL")
    check("PHYSICAL +40 again = 80", res["PHYSICAL"] == 80)
    check("CE stays 0", res["CE"] == 0)
    check("TECHNIQUE stays 0", res["TECHNIQUE"] == 0)


def test_clamp_logic():
    print("\n--- Test: Clamp Logic ---")
    res = {"PHYSICAL": 70, "CE": 10, "TECHNIQUE": 10}
    res = apply_resistance_change(res, "PHYSICAL")
    check("PHYSICAL clamped to 80 (70+40)", res["PHYSICAL"] == 80)
    check("CE clamped to 0 (10-20)", res["CE"] == 0)
    check("TECHNIQUE clamped to 0 (10-20)", res["TECHNIQUE"] == 0)


def test_damage_formula():
    print("\n--- Test: Damage Formula ---")
    res = new_resistances()
    dmg = compute_enemy_damage("PHYSICAL", res)
    check("PHYSICAL full damage = 120", dmg == 120)

    dmg = compute_enemy_damage("CE", res)
    check("CE full damage = 150", dmg == 150)

    dmg = compute_enemy_damage("TECHNIQUE", res)
    check("TECHNIQUE full damage = 220", dmg == 220)

    res["PHYSICAL"] = 50
    dmg = compute_enemy_damage("PHYSICAL", res)
    check("PHYSICAL with 50 res = 60", dmg == 60)


def test_judgment_damage():
    print("\n--- Test: Judgment Damage (Adaptation-Match) ---")
    # No adaptation — base damage
    dmg = compute_judgment_damage(None, "PHYSICAL")
    check("Base judgment (no adapt) = 100", dmg == 100)

    # Matching adaptation — burst
    dmg = compute_judgment_damage("PHYSICAL", "PHYSICAL")
    check("Burst judgment (matching adapt) = 350", dmg == 350)

    # Non-matching adaptation — no burst
    dmg = compute_judgment_damage("CE", "PHYSICAL")
    check("No burst when non-matching adapt = 100", dmg == 100)


def test_episode_termination():
    print("\n--- Test: Episode Termination ---")
    env = MahoragaEnv()
    env.reset()
    # Ensure agent survives all 25 turns by giving it massive HP
    env.agent_hp = 99999
    # Also prevent accidental enemy death by giving enemy massive HP
    env.enemy_hp = 99999

    done = False
    info = {}
    for i in range(25):
        if not done:
            _, _, done, info = env.step(0)  # Only adapt, never attack
    check("Episode ends at turn 25", done is True)
    check("Reason is turn limit", info.get("reason") == "Turn limit reached")


def test_actions_behave_correctly():
    print("\n--- Test: Action Behavior ---")

    env = MahoragaEnv()
    env.reset()
    state, _, _, _ = env.step(0)
    check("Adapt PHYSICAL sets res to 40", state["resistances"]["physical"] == 40)

    # Judgment Strike resets resistances
    env.reset()
    env.step(0)
    env.step(0)
    state, _, _, _ = env.step(3)
    check("Judgment resets resistances", state["resistances"]["physical"] == 0)
    check("Judgment damages enemy", state["enemy_hp"] < ENEMY_HP)

    # Regeneration heals but does NOT reset resistances
    env.reset()
    env.step(0)
    hp_before = env.agent_hp
    res_before = env.resistances["PHYSICAL"]
    state, _, _, _ = env.step(4)
    check("Regeneration heals agent", state["agent_hp"] > hp_before - 120)
    check("Regeneration does NOT reset resistances", state["resistances"]["physical"] == res_before)


def test_adaptation_stack():
    print("\n--- Test: Adaptation Stack ---")
    env = MahoragaEnv()
    env.reset()

    # Phase 1 enemy always attacks PHYSICAL
    env.step(0)
    check("Stack +1 on correct adapt", env.adaptation_stack == 1)
    env.step(0)
    check("Stack +2 on second correct adapt", env.adaptation_stack == 2)

    env.reset()
    env.step(1)  # CE adapt vs PHYSICAL enemy
    check("Stack stays 0 on wrong adapt", env.adaptation_stack == 0)

    env.reset()
    env.step(0)
    env.step(0)
    env.step(3)
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

    state, _, _, info = env.step(4)
    check("First heal works", info["heal_on_cooldown"] is False)
    check("Cooldown set to 3", env.heal_cooldown_counter == 3)

    _, _, _, info2 = env.step(4)
    check("Heal blocked on turn 2 (cooldown)", info2["heal_on_cooldown"] is True)

    _, _, _, info3 = env.step(4)
    check("Heal blocked on turn 3 (cooldown)", info3["heal_on_cooldown"] is True)

    _, _, _, info4 = env.step(4)
    check("Heal available on turn 4 (cooldown expired)", info4["heal_on_cooldown"] is False)


def test_heal_preserves_resistances():
    print("\n--- Test: Heal Preserves Resistances ---")
    env = MahoragaEnv()
    env.reset()

    env.step(0)
    env.step(0)
    res_before = env.resistances.copy()
    env.step(4)
    check("PHYSICAL res preserved after heal", env.resistances["PHYSICAL"] == res_before["PHYSICAL"])
    check("CE res preserved after heal", env.resistances["CE"] == res_before["CE"])
    check("TECHNIQUE res preserved after heal", env.resistances["TECHNIQUE"] == res_before["TECHNIQUE"])


def test_judgment_burst_adaptation_match():
    print("\n--- Test: Judgment Burst Via Adaptation Match ---")
    env = MahoragaEnv()
    env.reset()

    # Adapt PHYSICAL (correct for Phase 1 enemy) then Judgment
    env.step(0)  # Adapt PHYSICAL, correct, stack=1, last_adapted=PHYSICAL
    env.step(0)  # Adapt PHYSICAL, correct, stack=2, last_adapted=PHYSICAL
    enemy_hp_before = env.enemy_hp
    env.step(3)  # Judgment — last_adapted=PHYSICAL, enemy=PHYSICAL → BURST
    damage_dealt = enemy_hp_before - env.enemy_hp
    # burst 350 + stack 2*50 = 450
    check("Burst when adapted to matching category (dmg=450)", damage_dealt == 450)

    # Wrong adaptation — should NOT burst
    env.reset()
    env.step(1)  # Adapt CE, but enemy is PHYSICAL
    env.step(1)  # Adapt CE again
    enemy_hp_before = env.enemy_hp
    env.step(3)  # Judgment — last_adapted=CE, enemy=PHYSICAL → NO BURST
    damage_dealt = enemy_hp_before - env.enemy_hp
    # base 100 + stack 0*50 = 100
    check("No burst when adapted to wrong category (dmg=100)", damage_dealt == 100)


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


def test_hp_configuration():
    print("\n--- Test: HP Configuration ---")
    env = MahoragaEnv()
    state = env.reset()
    check("Agent HP = 1200", state["agent_hp"] == 1200)
    check("Enemy HP = 1000", state["enemy_hp"] == 1000)


# ========== ENEMY TESTS ==========

def test_subtype_mapping():
    print("\n--- Test: Subtype Mapping ---")
    for attack_type in ATTACK_TYPES:
        check(f"{attack_type} has subtypes", attack_type in SUBTYPES)
        check(f"{attack_type} has 3 subtypes", len(SUBTYPES[attack_type]) == 3)
    check("PHYSICAL has PIERCE", "PIERCE" in SUBTYPES["PHYSICAL"])
    check("CE has BEAM", "BEAM" in SUBTYPES["CE"])
    check("TECHNIQUE has DELAYED", "DELAYED" in SUBTYPES["TECHNIQUE"])


def test_ignore_armor_bypass():
    print("\n--- Test: Ignore Armor Bypass ---")
    res = new_resistances()
    res["PHYSICAL"] = 50

    normal_dmg = compute_enemy_damage("PHYSICAL", res, ignore_armor=False)
    pierce_dmg = compute_enemy_damage("PHYSICAL", res, ignore_armor=True)

    check("Ignore armor does more damage than normal at 50 res", pierce_dmg > normal_dmg)
    check("Normal damage = 60", normal_dmg == 60)
    check("Armor bypass damage = 72", pierce_dmg == 72)

    res_zero = new_resistances()
    normal_zero = compute_enemy_damage("PHYSICAL", res_zero, ignore_armor=False)
    pierce_zero = compute_enemy_damage("PHYSICAL", res_zero, ignore_armor=True)
    check("Same damage at 0 resistance", normal_zero == pierce_zero)


def test_curriculum_phase_1():
    print("\n--- Test: Curriculum Phase 1 (Turns 1-5) ---")
    enemy = CurriculumEnemy()
    for turn in range(1, 6):
        attack = enemy.get_attack(turn_number=turn)
        check(f"Turn {turn} is PHYSICAL", attack["category"] == "PHYSICAL")
        check(f"Turn {turn} has damage", attack["damage"] == 120)
        check(f"Turn {turn} has ignore_armor field", "ignore_armor" in attack)
        check(f"Turn {turn} subtype valid", attack["subtype"] in SUBTYPES["PHYSICAL"])


def test_curriculum_phase_2():
    print("\n--- Test: Curriculum Phase 2 (Cycle, No Deviation) ---")
    # Use a fresh enemy and go directly to Phase 2 turns
    enemy = CurriculumEnemy()
    import utils.constants as c
    old_dev = c.PHASE_2_DEVIATION
    c.PHASE_2_DEVIATION = 0  # Temporarily disable randomness

    a6 = enemy.get_attack(turn_number=6)
    check("Phase 2 step 1 = PHYSICAL", a6["category"] == "PHYSICAL")
    a7 = enemy.get_attack(turn_number=7)
    check("Phase 2 step 2 = CE", a7["category"] == "CE")
    a8 = enemy.get_attack(turn_number=8)
    check("Phase 2 step 3 = TECHNIQUE", a8["category"] == "TECHNIQUE")
    a9 = enemy.get_attack(turn_number=9)
    check("Phase 2 step 4 = PHYSICAL (cycle)", a9["category"] == "PHYSICAL")

    c.PHASE_2_DEVIATION = old_dev  # Restore


def test_curriculum_phase_3():
    print("\n--- Test: Curriculum Phase 3 (Target Lowest) ---")
    enemy = CurriculumEnemy()
    # Phase 3 starts at turn 16
    resistances = {"PHYSICAL": 80, "CE": 40, "TECHNIQUE": 0}
    attack = enemy.get_attack(turn_number=16, resistances=resistances)
    check("Phase 3 targets lowest resistance (TECHNIQUE)", attack["category"] == "TECHNIQUE")

    resistances2 = {"PHYSICAL": 0, "CE": 80, "TECHNIQUE": 40}
    attack2 = enemy.get_attack(turn_number=17, resistances=resistances2)
    check("Phase 3 targets lowest (PHYSICAL)", attack2["category"] == "PHYSICAL")


def test_enemy_dict_format():
    print("\n--- Test: Enemy Dict Format ---")
    enemy = CurriculumEnemy()
    attack = enemy.get_attack(turn_number=1)
    check("Returns dict", isinstance(attack, dict))
    check("Has 'category'", "category" in attack)
    check("Has 'subtype'", "subtype" in attack)
    check("Has 'damage'", "damage" in attack)
    check("Has 'ignore_armor'", "ignore_armor" in attack)
    check("category is PHYSICAL", attack["category"] == "PHYSICAL")
    check("subtype is valid", attack["subtype"] in SUBTYPES["PHYSICAL"])


def test_rl_observation_uses_3_types_only():
    print("\n--- Test: RL Observation Uses Only 3 Types ---")
    env = MahoragaEnv()
    env.reset()
    state, _, _, _ = env.step(0)
    check("last_enemy_attack_type is a valid RL type",
          state["last_enemy_attack_type"] in ATTACK_TYPES)
    check("Resistances use 3 keys only",
          set(state["resistances"].keys()) == {"physical", "ce", "technique"})


# ========== REWARD TESTS ==========

def test_adaptation_reward():
    print("\n--- Test: Adaptation Reward ---")
    env = MahoragaEnv()
    env.reset()
    _, reward, _, info = env.step(0)
    breakdown = info["reward_breakdown"]
    check("Correct adapt gives +0.8", breakdown["adaptation"] == 0.8)

    env.reset()
    _, reward, _, info = env.step(1)
    breakdown = info["reward_breakdown"]
    check("Wrong adapt gives 0.0", breakdown["adaptation"] == 0.0)


def test_damage_rewards():
    print("\n--- Test: Damage Rewards ---")
    env = MahoragaEnv()
    env.reset()
    _, _, _, info = env.step(0)
    breakdown = info["reward_breakdown"]
    check("Survival reward is negative (took damage)", breakdown["survival"] < 0)

    env.reset()
    _, _, _, info = env.step(3)
    breakdown = info["reward_breakdown"]
    check("Combat reward is positive (dealt damage)", breakdown["combat"] > 0)

    env.reset()
    _, _, _, info = env.step(0)
    breakdown = info["reward_breakdown"]
    check("Combat reward is 0 for adapt action", breakdown["combat"] == 0.0)


def test_heal_penalty():
    print("\n--- Test: Heal Penalty (Anti-Cowardice) ---")
    env = MahoragaEnv()
    env.reset()
    _, _, _, info = env.step(4)
    breakdown = info["reward_breakdown"]
    check("Heal at high HP penalized (-1.0)", breakdown["anti_cowardice"] == -1.0)

    env.reset()
    for _ in range(7):
        env.step(1)
    check("Agent HP is low enough", env.agent_hp < 0.7 * MAX_HP)
    _, _, _, info = env.step(4)
    breakdown = info["reward_breakdown"]
    check("Heal at low HP NOT penalized (0.0)", breakdown["anti_cowardice"] == 0.0)


def test_terminal_reward():
    print("\n--- Test: Terminal Reward ---")
    info_win = {"damage_taken": 0, "damage_dealt": 100, "correct_adaptation": False}
    state_win = {"agent_hp": 500, "enemy_hp": 0}
    rewards = compute_rewards(info_win, state_win, 3, done=True)
    check("Win terminal = +10.0", rewards["terminal"] == 10.0)

    info_loss = {"damage_taken": 100, "damage_dealt": 0, "correct_adaptation": False}
    state_loss = {"agent_hp": 0, "enemy_hp": 500}
    rewards = compute_rewards(info_loss, state_loss, 0, done=True)
    check("Loss terminal = -8.0", rewards["terminal"] == -8.0)

    rewards_nd = compute_rewards(info_win, state_win, 0, done=False)
    check("Not done terminal = 0.0", rewards_nd["terminal"] == 0.0)


def test_reward_breakdown_in_info():
    print("\n--- Test: Reward Breakdown In Info ---")
    env = MahoragaEnv()
    env.reset()
    _, reward, _, info = env.step(0)
    check("Info has reward_breakdown", "reward_breakdown" in info)
    breakdown = info["reward_breakdown"]
    expected_keys = {"survival", "combat", "adaptation", "anti_cowardice", "efficiency", "terminal", "opportunity"}
    check("Breakdown has all 7 components", set(breakdown.keys()) == expected_keys)
    total = sum(breakdown.values())
    check("Total reward = sum of components", abs(reward - total) < 1e-9)


def test_opportunity_penalty():
    print("\n--- Test: Opportunity Penalty ---")
    env = MahoragaEnv()
    env.reset()
    # Build 2 stacks via correct adaptation
    env.step(0)  # stack=1
    _, _, _, info = env.step(0)  # stack=2
    breakdown = info["reward_breakdown"]
    check("Opportunity penalty when stack>=2 and not striking (-0.5)", breakdown["opportunity"] == -0.5)

    # Now strike — no penalty
    env.reset()
    env.step(0)  # stack=1
    env.step(0)  # stack=2
    _, _, _, info3 = env.step(3)  # Judgment Strike
    breakdown3 = info3["reward_breakdown"]
    check("No opportunity penalty when striking", breakdown3["opportunity"] == 0.0)


def test_no_reward_for_nothing():
    print("\n--- Test: No Free Rewards ---")
    env = MahoragaEnv()
    env.reset()
    env.step(4)
    _, reward, _, info = env.step(4)
    breakdown = info["reward_breakdown"]
    check("No adaptation reward on wasted turn", breakdown["adaptation"] == 0.0)
    check("No combat reward on wasted turn", breakdown["combat"] == 0.0)
    check("No efficiency bonus on wasted turn", breakdown["efficiency"] == 0.0)


if __name__ == "__main__":
    print("=" * 50)
    print("  MahoragaEnv Merged System Tests")
    print("=" * 50)

    # Core mechanics
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
    test_judgment_burst_adaptation_match()
    test_info_dict_fields()
    test_hp_configuration()

    # Enemy system
    test_subtype_mapping()
    test_ignore_armor_bypass()
    test_curriculum_phase_1()
    test_curriculum_phase_2()
    test_curriculum_phase_3()
    test_enemy_dict_format()
    test_rl_observation_uses_3_types_only()

    # Rewards
    test_adaptation_reward()
    test_damage_rewards()
    test_heal_penalty()
    test_terminal_reward()
    test_reward_breakdown_in_info()
    test_opportunity_penalty()
    test_no_reward_for_nothing()

    print("\n" + "=" * 50)
    print(f"  Results: {PASS} passed, {FAIL} failed")
    print("=" * 50)

    if FAIL > 0:
        sys.exit(1)
