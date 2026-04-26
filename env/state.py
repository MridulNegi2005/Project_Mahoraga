def build_state_dict(agent_hp, enemy_hp, resistances, last_enemy_attack_type,
                     last_enemy_subtype, last_action, turn_number,
                     attack_history=None):
    return {
        "agent_hp": agent_hp,
        "enemy_hp": enemy_hp,
        "resistances": {
            "physical": resistances["PHYSICAL"],
            "ce": resistances["CE"],
            "technique": resistances["TECHNIQUE"]
        },
        "last_enemy_attack_type": last_enemy_attack_type,
        "last_enemy_subtype": last_enemy_subtype,
        "last_action": last_action,
        "turn_number": turn_number,
        "attack_history": attack_history if attack_history else []
    }
