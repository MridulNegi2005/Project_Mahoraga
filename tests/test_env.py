import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import random
from env.mahoraga_env import MahoragaEnv
from env.mahoraga_boss import MahoragaBoss
from env.mechanics import (
    new_resistances, apply_resistance_change, compute_enemy_damage,
    compute_player_damage, check_correct_adaptation,
)
from env.rewards import compute_rewards
from utils.constants import (
    SUBTYPES, ATTACK_TYPES, PLAYER_HP, MAHORAGA_HP,
    MAX_TURNS, ADAPT_THRESHOLD, ADAPT_RESISTANCE_GAIN,
    HEAL_COOLDOWN, HEAL_AMOUNT, RESISTANCE_MAX,
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


# ========== CORE MECHANICS ==========

def test_resistance_update_legacy():
    """Legacy resistance change function still works."""
    print("\n--- Test: Legacy Resistance Update ---")
    res = new_resistances()
    res = apply_resistance_change(res, "PHYSICAL")
    check("PHYSICAL +40", res["PHYSICAL"] == 40)
    check("CE clamped to 0", res["CE"] == 0)
    check("TECHNIQUE clamped to 0", res["TECHNIQUE"] == 0)


def test_player_damage():
    """Player damage computation with resistance reduction."""
    from utils.constants import PLAYER_DAMAGE
    print("\n--- Test: Player Damage ---")
    res = {"PHYSICAL": 0, "CE": 0, "TECHNIQUE": 0}
    result = compute_player_damage("PHYSICAL", res)
    check(f"Full PHYSICAL damage = {PLAYER_DAMAGE['PHYSICAL']}", result["damage"] == PLAYER_DAMAGE["PHYSICAL"])

    result = compute_player_damage("CE", res)
    check(f"Full CE damage >= {PLAYER_DAMAGE['CE']} (may include BF)", result["damage"] >= PLAYER_DAMAGE["CE"])

    result = compute_player_damage("TECHNIQUE", res)
    check(f"Full TECHNIQUE damage = {PLAYER_DAMAGE['TECHNIQUE']}", result["damage"] == PLAYER_DAMAGE["TECHNIQUE"])

    res_50 = {"PHYSICAL": 50, "CE": 0, "TECHNIQUE": 0}
    result = compute_player_damage("PHYSICAL", res_50)
    expected = int(PLAYER_DAMAGE["PHYSICAL"] * 0.5)
    check(f"PHYSICAL with 50% res = {expected}", result["damage"] == expected)


def test_boss_adaptation():
    """Boss adapts after adapt_threshold same-type hits (difficulty-dependent)."""
    print("\n--- Test: Boss Adaptation ---")
    boss = MahoragaBoss(difficulty="medium")
    threshold = boss.adapt_threshold

    for i in range(threshold - 1):
        info = boss.receive_hit("PHYSICAL")
        check(f"No adapt after {i+1} hit(s)", info["adapted"] is False)

    info = boss.receive_hit("PHYSICAL")
    check(f"Adapts after {threshold} hits", info["adapted"] is True)
    check(f"Resistance increased by {ADAPT_RESISTANCE_GAIN}",
          info["new_resistance"] == ADAPT_RESISTANCE_GAIN)
    check("Wheel turn incremented", boss.total_wheel_turns == 1)


def test_boss_domain_blocks_adaptation():
    """Domain Expansion blocks boss adaptation."""
    print("\n--- Test: Domain Blocks Adaptation ---")
    boss = MahoragaBoss(difficulty="hard")
    boss.apply_domain_start(3)

    for _ in range(5):
        info = boss.receive_hit("PHYSICAL")
    check("No adaptation during domain", info["adapted"] is False)
    check("Resistance stays 0 during domain", boss.resistances["PHYSICAL"] == 0)


def test_episode_termination():
    """Episode ends at turn limit or HP depletion."""
    print("\n--- Test: Episode Termination ---")
    env = MahoragaEnv()
    env.reset()
    env.player_hp = 99999
    env.boss.hp = 99999

    done = False
    info = {}
    for i in range(MAX_TURNS):
        if not done:
            _, _, done, info = env.step(0)
    check(f"Episode ends at turn {MAX_TURNS}", done is True)
    check("Reason is turn limit", info.get("reason") == "Turn limit reached")


def test_boss_death_ends_episode():
    """Episode ends when boss HP reaches 0."""
    print("\n--- Test: Boss Death ---")
    env = MahoragaEnv()
    env.reset()
    env.boss.hp = 1
    _, _, done, info = env.step(0)
    check("Episode ends when boss dies", done is True)
    check("Reason is Mahoraga defeated", info.get("reason") == "Mahoraga defeated")


def test_player_death_ends_episode():
    """Episode ends when player HP reaches 0."""
    print("\n--- Test: Player Death ---")
    env = MahoragaEnv()
    env.reset()
    env.player_hp = 1
    _, _, done, info = env.step(0)
    check("Episode ends when player dies", done is True)
    check("Reason is Player defeated", info.get("reason") == "Player defeated")


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
    env.player_hp = 500

    state, _, _, info = env.step(4)
    check("First heal works", info["heal_on_cooldown"] is False)
    check(f"Cooldown set to {HEAL_COOLDOWN}", env.heal_cooldown_counter == HEAL_COOLDOWN)

    _, _, _, info2 = env.step(4)
    check("Heal blocked on turn 2", info2["heal_on_cooldown"] is True)

    for _ in range(HEAL_COOLDOWN - 2):
        env.step(0)

    _, _, _, info_after = env.step(4)
    check("Heal available after cooldown expires", info_after["heal_on_cooldown"] is False)


def test_domain_expansion():
    """Domain resets resistances, buffs damage, single use."""
    print("\n--- Test: Domain Expansion ---")
    env = MahoragaEnv()
    env.reset()
    env.boss.hp = 99999

    for _ in range(ADAPT_THRESHOLD):
        env.step(0)
    check("Boss has resistance before domain", env.boss.resistances["PHYSICAL"] > 0)

    _, _, _, info = env.step(3)
    check("Domain activated", info["domain_activated"] is True)
    check("Boss resistances reset to 0",
          all(v == 0 for v in env.boss.resistances.values()))
    check("Domain is active", env.domain_active is True)

    _, _, _, info2 = env.step(3)
    check("Second domain is wasted", info2["domain_activated"] is False)


def test_domain_damage_boost():
    """Domain gives damage multiplier for DURATION turns."""
    print("\n--- Test: Domain Damage Boost ---")
    env = MahoragaEnv()
    env.reset()
    env.boss.hp = 99999
    random.seed(100)

    _, _, _, info_normal = env.step(2)
    dmg_normal = info_normal["damage_dealt"]

    env.reset()
    env.boss.hp = 99999
    random.seed(100)
    env.step(3)

    _, _, _, info_domain = env.step(2)
    dmg_domain = info_domain["damage_dealt"]

    check("Domain-buffed damage > normal damage", dmg_domain > dmg_normal)


def test_variety_tracking():
    """Consecutive same-type tracking works."""
    print("\n--- Test: Variety Tracking ---")
    env = MahoragaEnv()
    env.reset()

    env.step(0)
    check("First attack: consecutive_same=1", env.consecutive_same == 1)
    env.step(0)
    check("Same type: consecutive_same=2", env.consecutive_same == 2)
    env.step(1)
    check("Different type: consecutive_same=1", env.consecutive_same == 1)


def test_attack_deals_damage():
    """All attack actions deal damage to boss."""
    print("\n--- Test: Attacks Deal Damage ---")
    for action in [0, 1, 2]:
        env = MahoragaEnv()
        env.reset()
        env.boss.hp = 99999
        _, _, _, info = env.step(action)
        check(f"Action {action} deals damage > 0", info["damage_dealt"] > 0)


def test_heal_restores_hp():
    """Heal action restores player HP."""
    print("\n--- Test: Heal Restores HP ---")
    env = MahoragaEnv()
    env.reset()
    env.player_hp = 500
    env.boss.hp = 99999

    hp_before = env.player_hp
    env.step(4)
    check(f"HP increased after heal", env.player_hp > hp_before)
    check(f"HP increased by up to {HEAL_AMOUNT}", env.player_hp <= hp_before + HEAL_AMOUNT)


def test_info_dict_fields():
    print("\n--- Test: Info Dict Fields ---")
    env = MahoragaEnv()
    env.reset()
    _, _, _, info = env.step(0)
    required_keys = [
        "damage_dealt", "damage_taken", "adapted", "boss_resistances",
        "boss_wheel_turns", "heal_on_cooldown", "reward_breakdown",
    ]
    all_present = all(k in info for k in required_keys)
    check("Info dict has all required fields", all_present)


def test_hp_configuration():
    print("\n--- Test: HP Configuration ---")
    env = MahoragaEnv()
    state = env.reset()
    check(f"Player HP = {PLAYER_HP}", state["player_hp"] == PLAYER_HP)
    check(f"Boss HP = {MAHORAGA_HP}", state["boss_hp"] == MAHORAGA_HP)


# ========== SUBTYPE & DAMAGE TESTS ==========

def test_subtype_mapping():
    print("\n--- Test: Subtype Mapping ---")
    for attack_type in ATTACK_TYPES:
        check(f"{attack_type} has subtypes", attack_type in SUBTYPES)
        check(f"{attack_type} has 3 subtypes", len(SUBTYPES[attack_type]) == 3)
    check("PHYSICAL has PIERCE", "PIERCE" in SUBTYPES["PHYSICAL"])
    check("CE has BEAM", "BEAM" in SUBTYPES["CE"])
    check("TECHNIQUE has DELAYED", "DELAYED" in SUBTYPES["TECHNIQUE"])


def test_pierce_armor_bypass():
    """PIERCE subtype bypasses 20% resistance."""
    print("\n--- Test: PIERCE Armor Bypass ---")
    res = {"PHYSICAL": 50, "CE": 0, "TECHNIQUE": 0}
    normal = compute_player_damage("PHYSICAL", res, subtype="SLASH")
    pierce = compute_player_damage("PHYSICAL", res, subtype="PIERCE")
    check("PIERCE does more damage than SLASH at 50% res", pierce["damage"] > normal["damage"])

    res_zero = {"PHYSICAL": 0, "CE": 0, "TECHNIQUE": 0}
    normal_0 = compute_player_damage("PHYSICAL", res_zero, subtype="SLASH")
    pierce_0 = compute_player_damage("PHYSICAL", res_zero, subtype="PIERCE")
    check("Same damage at 0 resistance", normal_0["damage"] == pierce_0["damage"])


def test_legacy_damage_formula():
    """Legacy compute_enemy_damage still works."""
    from utils.constants import PLAYER_DAMAGE
    print("\n--- Test: Legacy Damage Formula ---")
    res = new_resistances()
    dmg = compute_enemy_damage("PHYSICAL", res)
    check(f"PHYSICAL full damage = {PLAYER_DAMAGE['PHYSICAL']}", dmg == PLAYER_DAMAGE["PHYSICAL"])


# ========== REWARD TESTS ==========

def test_damage_dealt_reward():
    print("\n--- Test: Damage Dealt Reward ---")
    env = MahoragaEnv()
    env.reset()
    _, _, _, info = env.step(0)
    breakdown = info["reward_breakdown"]
    check("damage_dealt reward > 0 for attack", breakdown["damage_dealt"] > 0)


def test_variety_reward():
    print("\n--- Test: Variety Reward ---")
    env = MahoragaEnv()
    env.reset()
    env.boss.hp = 99999
    env.player_hp = 99999

    env.step(0)
    env.step(0)
    _, _, _, info = env.step(1)
    breakdown = info["reward_breakdown"]
    check("Variety reward for switching types = 0.5", breakdown["variety"] == 0.5)

    env.reset()
    env.boss.hp = 99999
    env.player_hp = 99999
    env.step(0)
    env.step(0)
    _, _, _, info2 = env.step(0)
    breakdown2 = info2["reward_breakdown"]
    check("No variety reward for same type = 0.0", breakdown2["variety"] == 0.0)


def test_heal_waste_penalty():
    print("\n--- Test: Heal Waste Penalty ---")
    env = MahoragaEnv()
    env.reset()
    _, _, _, info = env.step(4)
    breakdown = info["reward_breakdown"]
    check("Heal at high HP penalized", breakdown["heal_waste"] == -1.0)


def test_terminal_reward():
    print("\n--- Test: Terminal Reward ---")
    info_win = {
        "damage_taken": 0, "damage_dealt": 100, "adapted": False,
        "black_flash": False, "domain_activated": False,
        "domain_used_before": False, "category": "PHYSICAL",
        "last_category": None, "consecutive_same": 0,
        "boss_resistances": {"PHYSICAL": 0, "CE": 0, "TECHNIQUE": 0},
    }
    state_win = {"player_hp": 500, "boss_hp": 0, "agent_hp": 500, "enemy_hp": 0}
    rewards = compute_rewards(info_win, state_win, 0, done=True)
    check("Win terminal = +12.0", rewards["terminal"] == 12.0)

    state_loss = {"player_hp": 0, "boss_hp": 500, "agent_hp": 0, "enemy_hp": 500}
    rewards2 = compute_rewards(info_win, state_loss, 0, done=True)
    check("Loss terminal = -10.0", rewards2["terminal"] == -10.0)

    rewards_nd = compute_rewards(info_win, state_win, 0, done=False)
    check("Not done terminal = 0.0", rewards_nd["terminal"] == 0.0)


def test_reward_breakdown_in_info():
    print("\n--- Test: Reward Breakdown In Info ---")
    env = MahoragaEnv()
    env.reset()
    _, reward, _, info = env.step(0)
    check("Info has reward_breakdown", "reward_breakdown" in info)
    breakdown = info["reward_breakdown"]
    expected_keys = {
        "damage_dealt", "survival", "variety", "anti_spam",
        "domain_timing", "domain_waste", "black_flash",
        "wheel_turn", "heal_waste", "terminal",
    }
    check("Breakdown has all 10 components", set(breakdown.keys()) == expected_keys)
    total = sum(breakdown.values())
    check("Total reward = sum of components", abs(reward - total) < 1e-9)


def test_rl_observation_format():
    print("\n--- Test: RL Observation Format ---")
    env = MahoragaEnv()
    state = env.reset()
    check("State has player_hp", "player_hp" in state)
    check("State has boss_hp", "boss_hp" in state)
    check("State has boss_resistances", "boss_resistances" in state)
    check("State has turn_number", "turn_number" in state)
    check("State has legacy agent_hp", "agent_hp" in state)
    check("State has legacy enemy_hp", "enemy_hp" in state)
    check("Legacy resistances use lowercase",
          set(state["resistances"].keys()) == {"physical", "ce", "technique"})


def test_game_is_winnable():
    """A strategic agent should be able to win sometimes."""
    print("\n--- Test: Game Is Winnable ---")
    wins = 0
    random.seed(42)
    for _ in range(200):
        env = MahoragaEnv(difficulty="medium")
        state = env.reset()
        cycle = [0, 1, 2]
        domain_used = False
        for t in range(MAX_TURNS):
            player_hp = state.get("player_hp", 0)
            boss_res = state.get("boss_resistances", {})
            if player_hp < 400 and env.heal_cooldown_counter == 0:
                action = 4
            elif not domain_used and t >= 4:
                high = sum(1 for v in boss_res.values() if v >= 20)
                if high >= 1:
                    action = 3
                    domain_used = True
                else:
                    action = cycle[t % 3]
            else:
                action = cycle[t % 3]
            state, _, done, info = env.step(action)
            if done:
                if info.get("reason") == "Mahoraga defeated":
                    wins += 1
                break
    win_rate = wins / 200
    print(f"    Win rate: {win_rate:.1%} ({wins}/200)")
    check("Strategic agent wins > 10% on medium", win_rate > 0.10)


if __name__ == "__main__":
    print("=" * 50)
    print("  MahoragaEnv v2 System Tests")
    print("=" * 50)

    test_resistance_update_legacy()
    test_player_damage()
    test_boss_adaptation()
    test_boss_domain_blocks_adaptation()
    test_episode_termination()
    test_boss_death_ends_episode()
    test_player_death_ends_episode()
    test_invalid_action()
    test_heal_cooldown()
    test_domain_expansion()
    test_domain_damage_boost()
    test_variety_tracking()
    test_attack_deals_damage()
    test_heal_restores_hp()
    test_info_dict_fields()
    test_hp_configuration()

    test_subtype_mapping()
    test_pierce_armor_bypass()
    test_legacy_damage_formula()

    test_damage_dealt_reward()
    test_variety_reward()
    test_heal_waste_penalty()
    test_terminal_reward()
    test_reward_breakdown_in_info()
    test_rl_observation_format()
    test_game_is_winnable()

    print("\n" + "=" * 50)
    print(f"  Results: {PASS} passed, {FAIL} failed")
    print("=" * 50)

    if FAIL > 0:
        sys.exit(1)
