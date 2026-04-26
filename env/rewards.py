"""
Reward System (v2: Boss Redesign)

The RL agent is the PLAYER fighting against Mahoraga.
Rewards incentivize: dealing damage, staying alive, varying attacks,
using Domain at the right time, and killing the boss.
"""
from utils.constants import PLAYER_HP, ACTION_HEAL, ACTION_DOMAIN


def _damage_dealt_reward(damage_dealt):
    """Reward dealing damage to Mahoraga."""
    return damage_dealt / 80.0


def _survival_reward(damage_taken):
    """Penalize taking damage from Mahoraga."""
    return -(damage_taken / 100.0)


def _variety_reward(category, last_category):
    """Reward using a different attack category than last turn.
    Incentivizes mixing attacks to slow Mahoraga's adaptation."""
    if category is None or last_category is None:
        return 0.0
    if category != last_category:
        return 0.5
    return 0.0


def _anti_spam_penalty(consecutive_same):
    """Penalize using the same attack category 3+ times in a row.
    This lets Mahoraga fully adapt, which is very bad."""
    if consecutive_same >= 3:
        return -0.8
    return 0.0


def _domain_timing_reward(domain_activated, boss_resistances):
    """Reward using Domain Expansion when Mahoraga has high resistances.
    Good timing = using it when 2+ categories have resistance >= 40."""
    if not domain_activated:
        return 0.0
    high_res_count = sum(1 for v in boss_resistances.values() if v >= 40)
    if high_res_count >= 2:
        return 2.0
    elif high_res_count >= 1:
        return 1.0
    return -0.5  # Wasted domain on low resistances


def _domain_waste_penalty(action, domain_used):
    """Penalize trying to use Domain when it's already been used."""
    if action == ACTION_DOMAIN and domain_used:
        return -1.0
    return 0.0


def _black_flash_reward(black_flash):
    """Bonus for triggering Black Flash."""
    if black_flash:
        return 1.5
    return 0.0


def _wheel_turn_penalty(boss_adapted):
    """Penalize letting Mahoraga's wheel turn (boss adapted)."""
    if boss_adapted:
        return -1.0
    return 0.0


def _heal_waste_penalty(action, player_hp):
    """Penalize healing at high HP."""
    if action == ACTION_HEAL and player_hp > 0.7 * PLAYER_HP:
        return -1.0
    return 0.0


def _terminal_reward(done, player_hp, boss_hp):
    """Strong signal at episode end."""
    if not done:
        return 0.0
    if boss_hp <= 0:
        # Player killed Mahoraga!
        return 12.0
    if player_hp <= 0:
        # Player died
        return -10.0
    # Turn limit — compare HP ratios
    player_ratio = player_hp / PLAYER_HP
    boss_ratio = boss_hp / 2000
    if player_ratio > boss_ratio:
        return 3.0  # Player is winning
    return -5.0  # Boss is winning


def compute_rewards(info, state, action, done):
    """Compute all reward components.

    Args:
        info: dict with damage_dealt, damage_taken, black_flash, adapted, etc.
        state: current state dict
        action: player's action (0-4)
        done: whether episode is over

    Returns:
        dict of named reward components. Final scalar = sum of all values.
    """
    damage_dealt = info.get("damage_dealt", 0)
    damage_taken = info.get("damage_taken", 0)
    black_flash = info.get("black_flash", False)
    boss_adapted = info.get("adapted", False)
    domain_activated = info.get("domain_activated", False)
    domain_used = info.get("domain_used_before", False)
    category = info.get("category", None)
    last_category = info.get("last_category", None)
    consecutive_same = info.get("consecutive_same", 0)
    boss_resistances = info.get("boss_resistances", {"PHYSICAL": 0, "CE": 0, "TECHNIQUE": 0})

    player_hp = state.get("player_hp", state.get("agent_hp", 0))
    boss_hp = state.get("boss_hp", state.get("enemy_hp", 0))

    return {
        "damage_dealt": _damage_dealt_reward(damage_dealt),
        "survival": _survival_reward(damage_taken),
        "variety": _variety_reward(category, last_category),
        "anti_spam": _anti_spam_penalty(consecutive_same),
        "domain_timing": _domain_timing_reward(domain_activated, boss_resistances),
        "domain_waste": _domain_waste_penalty(action, domain_used),
        "black_flash": _black_flash_reward(black_flash),
        "wheel_turn": _wheel_turn_penalty(boss_adapted),
        "heal_waste": _heal_waste_penalty(action, player_hp),
        "terminal": _terminal_reward(done, player_hp, boss_hp),
    }
