def build_state_dict(agent_hp, enemy_hp, resistances, last_action, last_enemy_action, turn_number):
    return {
        "agent_hp": agent_hp,
        "enemy_hp": enemy_hp,
        "resistances": resistances.copy(),
        "last_action": last_action,
        "last_enemy_action": last_enemy_action,
        "turn_number": turn_number
    }
