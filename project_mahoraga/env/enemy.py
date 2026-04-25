class Enemy:
    """Phase 1 enemy: always attacks with PHYSICAL."""

    def __init__(self):
        self.phase = 1

    def get_attack(self):
        """Returns (attack_type, subtype) tuple."""
        return "PHYSICAL", "SLASH"
