"""
State builder (v2: Boss Redesign)

Returns state dict used by the RL agent (player) and training prompt.
Now includes Mahoraga's boss state (resistances, wheel turns, etc.).
"""


def build_state_dict(player_hp, boss_hp, boss_resistances,
                     boss_wheel_turns, last_boss_attack_name,
                     last_player_action, turn_number,
                     crit_stack=0, domain_active=False,
                     domain_turns_left=0, domain_used=False,
                     heal_cooldown=0, last_category=None,
                     consecutive_same=0, attack_history=None,
                     # Legacy aliases
                     agent_hp=None, enemy_hp=None, resistances=None,
                     last_enemy_attack_type=None, last_enemy_subtype=None,
                     last_action=None):
    """Build the state observation dict.

    Supports both new boss-style and legacy field names.
    """
    # Handle legacy callers
    _player_hp = player_hp if agent_hp is None else agent_hp
    _boss_hp = boss_hp if enemy_hp is None else enemy_hp

    # Boss resistances (new format)
    if boss_resistances is not None:
        _boss_res = boss_resistances
    elif resistances is not None:
        # Legacy format — convert
        _boss_res = {
            "PHYSICAL": resistances.get("PHYSICAL", resistances.get("physical", 0)),
            "CE": resistances.get("CE", resistances.get("ce", 0)),
            "TECHNIQUE": resistances.get("TECHNIQUE", resistances.get("technique", 0)),
        }
    else:
        _boss_res = {"PHYSICAL": 0, "CE": 0, "TECHNIQUE": 0}

    return {
        # Player state
        "player_hp": _player_hp,
        "agent_hp": _player_hp,  # Legacy alias

        # Boss (Mahoraga) state
        "boss_hp": _boss_hp,
        "enemy_hp": _boss_hp,  # Legacy alias
        "boss_resistances": _boss_res,
        "resistances": {  # Legacy alias (lowercase)
            "physical": _boss_res["PHYSICAL"],
            "ce": _boss_res["CE"],
            "technique": _boss_res["TECHNIQUE"],
        },
        "boss_wheel_turns": boss_wheel_turns,

        # Last actions
        "last_boss_attack": last_boss_attack_name,
        "last_enemy_attack_type": last_enemy_attack_type or last_boss_attack_name,
        "last_enemy_subtype": last_enemy_subtype,
        "last_player_action": last_player_action,
        "last_action": last_action if last_action is not None else last_player_action,

        # Turn info
        "turn_number": turn_number,

        # Player mechanics
        "crit_stack": crit_stack,
        "domain_active": domain_active,
        "domain_turns_left": domain_turns_left,
        "domain_used": domain_used,
        "heal_cooldown": heal_cooldown,

        # Attack tracking
        "last_category": last_category,
        "consecutive_same": consecutive_same,
        "attack_history": attack_history if attack_history else [],
    }
