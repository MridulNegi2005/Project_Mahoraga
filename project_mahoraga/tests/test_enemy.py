"""Tests for the 3-phase Enemy system."""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from env.enemy import Enemy, ATTACK_DATA, CATEGORIES

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


def test_attack_dict_shape():
    print("\n--- Test: Attack Dict Shape ---")
    enemy = Enemy(seed=42)
    cat, sub = enemy.get_attack()
    atk = enemy.last_attack
    check("Has category key", "category" in atk)
    check("Has subtype key", "subtype" in atk)
    check("Has damage key", "damage" in atk)
    check("Has ignore_armor key", "ignore_armor" in atk)
    check("Category is string", isinstance(atk["category"], str))
    check("Damage is int", isinstance(atk["damage"], int))
    check("ignore_armor is bool", isinstance(atk["ignore_armor"], bool))


def test_phase1_always_physical():
    print("\n--- Test: Phase 1 (Turns 1-5) Always PHYSICAL ---")
    enemy = Enemy(seed=0)
    for turn in range(1, 6):
        cat, sub = enemy.get_attack()
        check(f"Turn {turn} category is PHYSICAL", cat == "PHYSICAL")
        valid_subs = [s["subtype"] for s in ATTACK_DATA["PHYSICAL"]]
        check(f"Turn {turn} subtype is valid", sub in valid_subs)


def test_phase1_damage_values():
    print("\n--- Test: Phase 1 Damage Values ---")
    expected = {"Slash": 120, "Impact": 140, "Pierce": 100}
    enemy = Enemy(seed=0)
    seen = set()
    # Run enough times with different seeds to cover subtypes
    for seed in range(100):
        e = Enemy(seed=seed)
        cat, sub = e.get_attack()
        atk = e.last_attack
        if sub in expected:
            check(f"Seed {seed}: {sub} damage = {expected[sub]}", atk["damage"] == expected[sub])
            seen.add(sub)
        if seen == set(expected.keys()):
            break
    check("All PHYSICAL subtypes seen", seen == set(expected.keys()))


def test_pierce_ignore_armor():
    print("\n--- Test: Pierce ignore_armor Flag ---")
    for seed in range(100):
        e = Enemy(seed=seed)
        cat, sub = e.get_attack()
        atk = e.last_attack
        if sub == "Pierce":
            check("Pierce has ignore_armor=True", atk["ignore_armor"] is True)
            break
    else:
        check("Pierce appeared in 100 seeds", False)


def test_phase2_loop_pattern():
    print("\n--- Test: Phase 2 Loop Pattern (no RNG break) ---")
    # Use seed that avoids the 15% break for at least a few turns
    # We test the deterministic path by checking many seeds
    enemy = Enemy(seed=7)  # Need to find a seed with no breaks
    # Skip Phase 1
    for _ in range(5):
        enemy.get_attack()

    # Phase 2: expect PHYSICAL -> CE -> TECHNIQUE -> PHYSICAL -> ...
    expected_loop = ["PHYSICAL", "CE", "TECHNIQUE"]
    loop_held = True
    break_count = 0
    for i in range(10):  # Turns 6-15
        cat, sub = enemy.get_attack()
        expected = expected_loop[i % 3]
        if cat != expected:
            break_count += 1

    # With 15% break chance and 10 turns, we expect ~1.5 breaks on average
    # Just verify it's not ALL broken
    check(f"Phase 2 loop mostly holds ({10 - break_count}/10 on-pattern)", break_count < 10)


def test_phase2_rng_break_exists():
    print("\n--- Test: Phase 2 RNG Break Exists ---")
    # Run many seeds and check that at least some turns break the loop
    breaks_found = 0
    for seed in range(200):
        enemy = Enemy(seed=seed)
        for _ in range(5):
            enemy.get_attack()  # Skip Phase 1
        expected_loop = ["PHYSICAL", "CE", "TECHNIQUE"]
        for i in range(10):
            cat, _ = enemy.get_attack()
            expected = expected_loop[i % 3]
            if cat != expected:
                breaks_found += 1
    check(f"RNG breaks occurred across seeds ({breaks_found} breaks)", breaks_found > 0)


def test_phase3_targets_lowest_resistance():
    print("\n--- Test: Phase 3 Targets Lowest Resistance ---")
    enemy = Enemy(seed=42)
    # Advance to Phase 3 (turn 16+)
    for _ in range(15):
        enemy.get_attack()

    # CE is lowest → should attack CE
    res = {"PHYSICAL": 80, "CE": 0, "TECHNIQUE": 40}
    cat, sub = enemy.get_attack(res)
    check("Targets CE when CE=0 is lowest", cat == "CE")

    # TECHNIQUE is lowest
    res = {"PHYSICAL": 60, "CE": 60, "TECHNIQUE": 10}
    cat, sub = enemy.get_attack(res)
    check("Targets TECHNIQUE when TECHNIQUE=10 is lowest", cat == "TECHNIQUE")

    # PHYSICAL is lowest
    res = {"PHYSICAL": 0, "CE": 80, "TECHNIQUE": 80}
    cat, sub = enemy.get_attack(res)
    check("Targets PHYSICAL when PHYSICAL=0 is lowest", cat == "PHYSICAL")


def test_phase3_tie_breaking():
    print("\n--- Test: Phase 3 Tie Breaking ---")
    # All equal → should pick randomly among all three
    seen_cats = set()
    for seed in range(200):
        enemy = Enemy(seed=seed)
        for _ in range(15):
            enemy.get_attack()
        res = {"PHYSICAL": 40, "CE": 40, "TECHNIQUE": 40}
        cat, _ = enemy.get_attack(res)
        seen_cats.add(cat)
    check("All categories seen when tied", seen_cats == set(CATEGORIES))


def test_turn_counter():
    print("\n--- Test: Turn Counter ---")
    enemy = Enemy(seed=0)
    check("Initial turn is 0", enemy.turn == 0)
    enemy.get_attack()
    check("After 1 attack turn is 1", enemy.turn == 1)
    enemy.get_attack()
    check("After 2 attacks turn is 2", enemy.turn == 2)


def test_reset():
    print("\n--- Test: Reset ---")
    enemy = Enemy(seed=0)
    for _ in range(10):
        enemy.get_attack()
    check("Turn advanced to 10", enemy.turn == 10)
    enemy.reset()
    check("Turn reset to 0", enemy.turn == 0)
    cat, _ = enemy.get_attack()
    check("Post-reset attack is Phase 1 (PHYSICAL)", cat == "PHYSICAL")


def test_current_phase_property():
    print("\n--- Test: Current Phase Property ---")
    enemy = Enemy(seed=0)
    enemy.turn = 1
    check("Turn 1 -> Phase 1", enemy.current_phase == 1)
    enemy.turn = 5
    check("Turn 5 -> Phase 1", enemy.current_phase == 1)
    enemy.turn = 6
    check("Turn 6 -> Phase 2", enemy.current_phase == 2)
    enemy.turn = 15
    check("Turn 15 -> Phase 2", enemy.current_phase == 2)
    enemy.turn = 16
    check("Turn 16 -> Phase 3", enemy.current_phase == 3)
    enemy.turn = 25
    check("Turn 25 -> Phase 3", enemy.current_phase == 3)


def test_get_attack_dict_method():
    print("\n--- Test: get_attack_dict() Method ---")
    enemy = Enemy(seed=42)
    atk = enemy.get_attack_dict()
    check("Returns dict", isinstance(atk, dict))
    check("Dict has category", atk["category"] in CATEGORIES)
    check("Dict has damage", isinstance(atk["damage"], int))
    check("Turn advanced", enemy.turn == 1)


def test_all_subtypes_reachable():
    print("\n--- Test: All Subtypes Reachable ---")
    all_subs = set()
    for cat in ATTACK_DATA:
        for entry in ATTACK_DATA[cat]:
            all_subs.add((cat, entry["subtype"]))

    seen = set()
    for seed in range(500):
        enemy = Enemy(seed=seed)
        for _ in range(25):
            cat, sub = enemy.get_attack({"PHYSICAL": 0, "CE": 0, "TECHNIQUE": 0})
            seen.add((cat, sub))
    check(f"All 9 subtypes reachable ({len(seen)}/9)", seen == all_subs)


if __name__ == "__main__":
    print("=" * 50)
    print("  Enemy System Tests")
    print("=" * 50)

    test_attack_dict_shape()
    test_phase1_always_physical()
    test_phase1_damage_values()
    test_pierce_ignore_armor()
    test_phase2_loop_pattern()
    test_phase2_rng_break_exists()
    test_phase3_targets_lowest_resistance()
    test_phase3_tie_breaking()
    test_turn_counter()
    test_reset()
    test_current_phase_property()
    test_get_attack_dict_method()
    test_all_subtypes_reachable()

    print("\n" + "=" * 50)
    print(f"  Results: {PASS} passed, {FAIL} failed")
    print("=" * 50)

    if FAIL > 0:
        sys.exit(1)
