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
    dmg = compute_judgment_damage(res)
    check("Base judgment = 100", dmg == 100)

    res["PHYSICAL"] = 80
    dmg = compute_judgment_damage(res)
    check("Burst judgment (res > 60) = 350", dmg == 350)


def test_episode_termination():
    print("\n--- Test: Episode Termination ---")
    env = MahoragaEnv()
    env.reset()

    # Run 25 turns with heal to survive
    done = False
    for _ in range(25):
        _, _, done, info = env.step(4)  # Regeneration
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
    state_before = env._get_state()
    state, _, _, _ = env.step(3)  # Judgment Strike
    check("Judgment resets resistances", state["resistances"]["physical"] == 0)
    check("Judgment damages enemy", state["enemy_hp"] < 1000)

    # Regeneration heals and resets
    env.reset()
    env.step(0)  # Take a hit, build resistance
    hp_before = env.agent_hp
    state, _, _, _ = env.step(4)  # Regeneration
    check("Regeneration heals agent", state["agent_hp"] > hp_before - 120)
    check("Regeneration resets resistances", state["resistances"]["physical"] == 0)


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


if __name__ == "__main__":
    print("=" * 50)
    print("  MahoragaEnv Phase 1 Tests")
    print("=" * 50)

    test_resistance_update()
    test_clamp_logic()
    test_damage_formula()
    test_judgment_damage()
    test_episode_termination()
    test_actions_behave_correctly()
    test_adaptation_stack()
    test_invalid_action()

    print("\n" + "=" * 50)
    print(f"  Results: {PASS} passed, {FAIL} failed")
    print("=" * 50)

    if FAIL > 0:
        sys.exit(1)
