def build_state_dict(agent_hp, enemy_hp, resistances, last_enemy_attack_type,
                     last_enemy_subtype, last_action, turn_number, adaptation_stack):
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
        "adaptation_stack": adaptation_stack
    }
