from utils.constants import (
    RESISTANCE_MIN, RESISTANCE_MAX, ADAPT_INCREASE, ADAPT_DECREASE,
    JUDGMENT_BASE_DAMAGE, JUDGMENT_BURST_DAMAGE,
    HEAL_AMOUNT, MAX_HP, ACTION_TO_TYPE,
    ARMOR_BYPASS_RATIO
)


def new_resistances():
    return {"PHYSICAL": 0, "CE": 0, "TECHNIQUE": 0}


def apply_resistance_change(resistances, target_type):
    """Increase target resistance by +40, decrease others by -20. Clamp to [0, 80]."""
    updated = {}
    for r_type in resistances:
        if r_type == target_type:
            val = resistances[r_type] + ADAPT_INCREASE
        else:
            val = resistances[r_type] - ADAPT_DECREASE
        updated[r_type] = max(RESISTANCE_MIN, min(RESISTANCE_MAX, val))
    return updated


def compute_enemy_damage(category, resistances, ignore_armor=False):
    """Compute damage dealt by enemy to agent based on resistance.

    Args:
        category: Attack category (PHYSICAL/CE/TECHNIQUE)
        resistances: Dict of resistance values
        ignore_armor: If True, bypasses 20% of resistance (PIERCE effect)
    """
    from utils.constants import BASE_DAMAGE
    base = BASE_DAMAGE[category]
    resistance = resistances[category]

    if ignore_armor:
        resistance = resistance * (1 - ARMOR_BYPASS_RATIO)

    damage = base * (1 - resistance / 100.0)
    return int(damage)


def compute_judgment_damage(last_adapted_category, enemy_category):
    """Compute Judgment Strike damage.
    Burst if last adapted category matches current enemy attack category."""
    if last_adapted_category and last_adapted_category == enemy_category:
        return JUDGMENT_BURST_DAMAGE
    return JUDGMENT_BASE_DAMAGE


def apply_action_effects(action, agent_hp, enemy_hp, resistances, adaptation_stack,
                         enemy_category=None, last_adapted_category=None):
    """Apply the agent's chosen action.
    Returns: (agent_hp, enemy_hp, resistances, adaptation_stack)
    """
    if action in ACTION_TO_TYPE:
        # Adapt action (0, 1, 2)
        target_type = ACTION_TO_TYPE[action]
        resistances = apply_resistance_change(resistances, target_type)

    elif action == 3:
        # Judgment Strike — burst if adapted to matching category
        damage = compute_judgment_damage(last_adapted_category, enemy_category)
        total_damage = damage + (adaptation_stack * 50)
        enemy_hp = max(0, enemy_hp - total_damage)
        resistances = new_resistances()
        adaptation_stack = 0

    elif action == 4:
        # Regeneration (does NOT reset resistances)
        agent_hp = min(MAX_HP, agent_hp + HEAL_AMOUNT)

    return agent_hp, enemy_hp, resistances, adaptation_stack


def check_correct_adaptation(action, enemy_category):
    """Check if the agent adapted to the correct attack category."""
    if action not in ACTION_TO_TYPE:
        return False
    return ACTION_TO_TYPE[action] == enemy_category
