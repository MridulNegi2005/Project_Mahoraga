from utils.constants import MAX_HP, ACTION_REGENERATION, ACTION_JUDGMENT


def _survival_reward(damage_taken):
    """Penalize taking damage."""
    return -(damage_taken / 100.0)


def _combat_reward(damage_dealt):
    """Reward dealing damage — scaled up to encourage attacking."""
    return damage_dealt / 80.0


def _adaptation_reward(correct_adaptation):
    """Reward correct adaptation — reduced to avoid dominating the signal."""
    if correct_adaptation:
        return 0.8
    return 0.0


def _anti_cowardice_reward(action, agent_hp):
    """Penalize healing at high HP."""
    if action == ACTION_REGENERATION and agent_hp > 0.7 * MAX_HP:
        return -1.0
    return 0.0


def _efficiency_bonus(damage_dealt):
    """Bonus for significant damage (burst strikes)."""
    if damage_dealt >= 200:
        return 1.0
    return 0.0


def _terminal_reward(done, agent_hp, enemy_hp):
    """Strong signal at episode end — increased to make winning matter."""
    if not done:
        return 0.0
    if agent_hp > enemy_hp:
        return 10.0
    return -8.0


def _opportunity_penalty(action, adaptation_stack):
    """Penalize NOT attacking when stacks are high enough for burst.
    If stack >= 2 and agent doesn't use Judgment, it's wasting potential."""
    if adaptation_stack >= 2 and action != ACTION_JUDGMENT:
        return -0.5
    return 0.0


def compute_rewards(info, state, action, done):
    """Compute all reward components independently.

    Returns dict of named reward components.
    Final scalar = sum of all values.
    """
    damage_taken = info.get("damage_taken", 0)
    damage_dealt = info.get("damage_dealt", 0)
    correct_adaptation = info.get("correct_adaptation", False)
    adaptation_stack = info.get("adaptation_stack", 0)
    agent_hp = state["agent_hp"]
    enemy_hp = state["enemy_hp"]

    return {
        "survival": _survival_reward(damage_taken),
        "combat": _combat_reward(damage_dealt),
        "adaptation": _adaptation_reward(correct_adaptation),
        "anti_cowardice": _anti_cowardice_reward(action, agent_hp),
        "efficiency": _efficiency_bonus(damage_dealt),
        "terminal": _terminal_reward(done, agent_hp, enemy_hp),
        "opportunity": _opportunity_penalty(action, adaptation_stack)
    }
