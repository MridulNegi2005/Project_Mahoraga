from utils.constants import (
    RESISTANCE_MIN, RESISTANCE_MAX, ADAPT_INCREASE, ADAPT_DECREASE,
    BASE_DAMAGE, JUDGMENT_BASE_DAMAGE, JUDGMENT_BURST_DAMAGE,
    BURST_THRESHOLD, HEAL_AMOUNT, MAX_HP, ACTION_TO_TYPE,
    PIERCE_RESISTANCE_BYPASS
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


def compute_enemy_damage(attack_type, resistances, subtype=None):
    """Compute damage dealt by enemy to agent based on resistance.
    PIERCE subtype ignores 20% of resistance."""
    base = BASE_DAMAGE[attack_type]
    resistance = resistances[attack_type]

    # PIERCE bypasses 20% of resistance
    if subtype == "PIERCE":
        resistance = resistance * (1 - PIERCE_RESISTANCE_BYPASS)

    damage = base * (1 - resistance / 100.0)
    return int(damage)


def compute_judgment_damage(resistances, enemy_attack_type=None):
    """Compute Judgment Strike damage. Burst only if resistance of current enemy attack type > 60."""
    if enemy_attack_type and resistances.get(enemy_attack_type, 0) > BURST_THRESHOLD:
        return JUDGMENT_BURST_DAMAGE
    return JUDGMENT_BASE_DAMAGE


def apply_action_effects(action, agent_hp, enemy_hp, resistances, adaptation_stack, enemy_attack_type=None):
    """
    Apply the agent's chosen action.
    Returns: (agent_hp, enemy_hp, resistances, adaptation_stack)
    """
    if action in ACTION_TO_TYPE:
        # Adapt action (0, 1, 2)
        target_type = ACTION_TO_TYPE[action]
        resistances = apply_resistance_change(resistances, target_type)

    elif action == 3:
        # Judgment Strike
        damage = compute_judgment_damage(resistances, enemy_attack_type)
        # Stack bonus: each stack adds extra damage
        total_damage = damage + (adaptation_stack * 50)
        enemy_hp = max(0, enemy_hp - total_damage)
        resistances = new_resistances()
        adaptation_stack = 0

    elif action == 4:
        # Regeneration (does NOT reset resistances)
        agent_hp = min(MAX_HP, agent_hp + HEAL_AMOUNT)

    return agent_hp, enemy_hp, resistances, adaptation_stack


def check_correct_adaptation(action, last_enemy_attack_type):
    """Check if the agent adapted to the correct attack type."""
    if action not in ACTION_TO_TYPE:
        return False
    return ACTION_TO_TYPE[action] == last_enemy_attack_type
