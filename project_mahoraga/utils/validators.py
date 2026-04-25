def validate_action(action):
    if action not in [0, 1, 2, 3, 4]:
        raise ValueError("Invalid action. Must be an integer between 0 and 4.")
