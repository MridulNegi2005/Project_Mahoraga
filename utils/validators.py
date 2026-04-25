from utils.constants import VALID_ACTIONS


def validate_action(action):
    if action not in VALID_ACTIONS:
        raise ValueError(
            f"Invalid action: {action}. Must be one of {VALID_ACTIONS}."
        )
