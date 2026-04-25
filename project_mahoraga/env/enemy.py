import random
from utils.constants import SUBTYPES, ATTACK_TYPES


class Enemy:
    """Phase 1 enemy: always attacks with PHYSICAL, random subtype."""

    def __init__(self):
        self.phase = 1

    def get_attack(self):
        """Returns dict: {type, subtype, base_damage}."""
        from utils.constants import BASE_DAMAGE
        attack_type = "PHYSICAL"
        subtype = random.choice(SUBTYPES[attack_type])
        return {
            "type": attack_type,
            "subtype": subtype,
            "base_damage": BASE_DAMAGE[attack_type]
        }


class PatternEnemy:
    """Phase 2 enemy: cycles PHYSICAL -> CE -> TECHNIQUE with random subtypes.
    10-15% chance of picking a random type instead of the pattern."""

    def __init__(self):
        self.phase = 2
        self.pattern = ["PHYSICAL", "CE", "TECHNIQUE"]
        self.pattern_index = 0
        self.deviation_chance = 0.12  # ~12% randomness

    def get_attack(self):
        """Returns dict: {type, subtype, base_damage}."""
        from utils.constants import BASE_DAMAGE

        # Occasional random deviation
        if random.random() < self.deviation_chance:
            attack_type = random.choice(ATTACK_TYPES)
        else:
            attack_type = self.pattern[self.pattern_index]
            self.pattern_index = (self.pattern_index + 1) % len(self.pattern)

        subtype = random.choice(SUBTYPES[attack_type])
        return {
            "type": attack_type,
            "subtype": subtype,
            "base_damage": BASE_DAMAGE[attack_type]
        }
