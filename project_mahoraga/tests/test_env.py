import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from env.mahoraga_env import MahoragaEnv
from env.mechanics import (
    new_resistances, apply_resistance_change, compute_enemy_damage,
    compute_judgment_damage
)

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


if __name__ == "__main__":
    print("=" * 50)
    print("  MahoragaEnv Phase 1 Tests (Patched)")
    print("=" * 50)

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

    print("\n" + "=" * 50)
    print(f"  Results: {PASS} passed, {FAIL} failed")
    print("=" * 50)

    if FAIL > 0:
        sys.exit(1)
