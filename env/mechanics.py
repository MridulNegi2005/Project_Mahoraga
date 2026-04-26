"""
Combat Mechanics (v2: Boss Redesign)

Damage flows:
    Player → Mahoraga: reduced by Mahoraga's resistances
    Mahoraga → Player: raw damage (player has no resistances)
"""
import random
from utils.constants import (
    PLAYER_DAMAGE, PLAYER_HP,
    ACTION_TO_TYPE, HEAL_AMOUNT,
    DOMAIN_DAMAGE_MULTIPLIER, DOMAIN_DURATION,
    DOMAIN_POST_RESISTANCE_BOOST,
    BLACK_FLASH_CHANCE, BLACK_FLASH_MULTIPLIER, BLACK_FLASH_RESISTANCE_REDUCTION,
    CRIT_STACK_THRESHOLD, CRIT_STACK_MULTIPLIER,
    ARMOR_BYPASS_RATIO,
)


def compute_player_damage(category, boss_resistances, subtype=None,
                          crit_stack=0, domain_active=False):
    """Compute damage the player deals to Mahoraga.

    Args:
        category: "PHYSICAL", "CE", or "TECHNIQUE"
        boss_resistances: Mahoraga's current resistance dict
        subtype: Attack subtype (PIERCE bypasses 20% resistance)
        crit_stack: Current consecutive-hit stack
        domain_active: Whether Domain Expansion is active

    Returns:
        dict: {damage, black_flash, crit, raw_damage}
    """
    base = PLAYER_DAMAGE[category]
    resistance = boss_resistances.get(category, 0)

    # PIERCE bypasses 20% resistance
    if subtype == "PIERCE":
        resistance = resistance * (1 - ARMOR_BYPASS_RATIO)

    # Apply resistance reduction
    damage = base * (1 - resistance / 100.0)

    # Crit stack bonus
    is_crit = crit_stack >= CRIT_STACK_THRESHOLD
    if is_crit:
        damage *= CRIT_STACK_MULTIPLIER

    # Domain Expansion bonus
    if domain_active:
        damage *= DOMAIN_DAMAGE_MULTIPLIER

    # Black Flash (CE only, 15% chance)
    is_black_flash = False
    if category == "CE" and random.random() < BLACK_FLASH_CHANCE:
        is_black_flash = True
        damage *= BLACK_FLASH_MULTIPLIER

    damage = int(damage)

    return {
        "damage": damage,
        "black_flash": is_black_flash,
        "crit": is_crit,
        "raw_base": base,
    }


def apply_player_action(action, player_hp, boss, crit_stack, domain_active,
                         domain_turns_left, heal_cooldown, domain_used):
    """Apply the player's chosen action.

    Args:
        action: 0-4 (Physical/CE/Technique/Domain/Heal)
        player_hp: Current player HP
        boss: MahoragaBoss instance
        crit_stack: Current consecutive same-type hit count
        domain_active: Whether domain is currently active
        domain_turns_left: Remaining domain turns
        heal_cooldown: Remaining heal cooldown
        domain_used: Whether domain has been used this fight

    Returns:
        dict with all results
    """
    result = {
        "damage_dealt": 0,
        "category": None,
        "subtype": None,
        "black_flash": False,
        "crit": False,
        "adapted": False,
        "adapt_category": None,
        "domain_activated": False,
        "healed": 0,
        "heal_blocked": False,
        "action_name": "Unknown",
        "new_crit_stack": crit_stack,
        "new_domain_active": domain_active,
        "new_domain_turns": domain_turns_left,
        "new_heal_cooldown": heal_cooldown,
        "new_domain_used": domain_used,
        "new_player_hp": player_hp,
    }

    if action in ACTION_TO_TYPE:
        # ── ATTACK (actions 0-2) ──
        category = ACTION_TO_TYPE[action]
        subtype = random.choice(from_subtypes(category))

        dmg_result = compute_player_damage(
            category, boss.resistances, subtype=subtype,
            crit_stack=crit_stack, domain_active=domain_active
        )

        boss.hp = max(0, boss.hp - dmg_result["damage"])

        # Track adaptation
        adapt_info = boss.receive_hit(category)

        # Update crit stack
        # Consecutive same-type hits build stack; different type resets
        if crit_stack > 0 and result.get("_last_category") == category:
            new_crit_stack = crit_stack + 1
        elif action == getattr(apply_player_action, '_last_attack_action', -1):
            new_crit_stack = crit_stack + 1
        else:
            new_crit_stack = 1

        result.update({
            "damage_dealt": dmg_result["damage"],
            "category": category,
            "subtype": subtype,
            "black_flash": dmg_result["black_flash"],
            "crit": dmg_result["crit"],
            "adapted": adapt_info["adapted"],
            "adapt_category": adapt_info["category"] if adapt_info["adapted"] else None,
            "action_name": f"{category} Strike",
            "new_crit_stack": new_crit_stack if action == getattr(apply_player_action, '_last_attack_action', action) else 1,
        })

        # Black Flash resistance reduction
        if dmg_result["black_flash"]:
            boss.reduce_resistance(category, BLACK_FLASH_RESISTANCE_REDUCTION)

        # Track last attack for crit stack
        apply_player_action._last_attack_action = action

    elif action == 3:
        # ── DOMAIN EXPANSION ──
        if domain_used:
            # Already used — wasted turn
            result["action_name"] = "Domain (WASTED — already used)"
        else:
            boss.apply_domain_start(DOMAIN_DURATION)
            result.update({
                "domain_activated": True,
                "action_name": "DOMAIN EXPANSION",
                "new_domain_active": True,
                "new_domain_turns": DOMAIN_DURATION,
                "new_domain_used": True,
                "new_crit_stack": 0,  # Reset crit stack on domain
            })

    elif action == 4:
        # ── REVERSED CURSED TECHNIQUE (heal) ──
        if heal_cooldown > 0:
            result.update({
                "heal_blocked": True,
                "action_name": "Heal (BLOCKED — cooldown)",
            })
        else:
            heal = min(HEAL_AMOUNT, PLAYER_HP - player_hp)
            result.update({
                "healed": heal,
                "action_name": "Reversed Cursed Technique",
                "new_player_hp": min(PLAYER_HP, player_hp + heal),
                "new_heal_cooldown": from_heal_cooldown(),
            })

    result["new_player_hp"] = result.get("new_player_hp", player_hp)
    return result


def from_subtypes(category):
    """Get subtypes for a category."""
    from utils.constants import SUBTYPES
    return SUBTYPES.get(category, ["SLASH"])


def from_heal_cooldown():
    """Get heal cooldown value."""
    from utils.constants import HEAL_COOLDOWN
    return HEAL_COOLDOWN


# Legacy functions (for backward compat)
def new_resistances():
    return {"PHYSICAL": 0, "CE": 0, "TECHNIQUE": 0}


def apply_resistance_change(resistances, target_type):
    """Legacy: Increase target resistance by +40, decrease others by -20."""
    from utils.constants import ADAPT_INCREASE, ADAPT_DECREASE, RESISTANCE_MAX
    updated = {}
    for r_type in resistances:
        if r_type == target_type:
            val = resistances[r_type] + ADAPT_INCREASE
        else:
            val = resistances[r_type] - ADAPT_DECREASE
        updated[r_type] = max(0, min(RESISTANCE_MAX, val))
    return updated


def compute_enemy_damage(category, resistances, ignore_armor=False):
    """Legacy compat."""
    base = PLAYER_DAMAGE.get(category, 120)
    resistance = resistances.get(category, 0)
    if ignore_armor:
        resistance = resistance * (1 - ARMOR_BYPASS_RATIO)
    damage = base * (1 - resistance / 100.0)
    return int(damage)


def check_correct_adaptation(action, enemy_category):
    """Legacy compat."""
    if action not in ACTION_TO_TYPE:
        return False
    return ACTION_TO_TYPE[action] == enemy_category
