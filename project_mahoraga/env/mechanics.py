from utils.constants import (
    RESISTANCE_LIMITS, RESISTANCE_CHANGES, DAMAGE_VALUES, HEAL_AMOUNT, MAX_HP, BURST_THRESHOLD
)

def apply_resistance_change(resistances, target_type):
    for r_type in resistances:
        if r_type == target_type:
            resistances[r_type] += RESISTANCE_CHANGES["INCREASE"]
        else:
            resistances[r_type] -= RESISTANCE_CHANGES["DECREASE"]
        
        resistances[r_type] = max(RESISTANCE_LIMITS["MIN"], min(RESISTANCE_LIMITS["MAX"], resistances[r_type]))
    return resistances

def compute_damage(action, resistances):
    if action == 3:  # Sword Attack
        if resistances.get("SLASH", 0) > BURST_THRESHOLD:
            return DAMAGE_VALUES["BURST_DAMAGE"]
        return DAMAGE_VALUES["BASE_DAMAGE"]
    return 0

def reset_resistances():
    return {"SLASH": 0, "FIRE": 0, "ENERGY": 0}

def apply_action_effects(action, agent_hp, enemy_hp, resistances):
    if action == 0:
        resistances = apply_resistance_change(resistances, "SLASH")
    elif action == 1:
        resistances = apply_resistance_change(resistances, "FIRE")
    elif action == 2:
        resistances = apply_resistance_change(resistances, "ENERGY")
    elif action == 3:
        damage = compute_damage(action, resistances)
        enemy_hp = max(0, enemy_hp - damage)
        resistances = reset_resistances()
    elif action == 4:
        agent_hp = min(MAX_HP, agent_hp + HEAL_AMOUNT)
        resistances = reset_resistances()
        
    return agent_hp, enemy_hp, resistances
