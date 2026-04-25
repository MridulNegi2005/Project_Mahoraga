import random
import utils.constants as const
from utils.constants import (
    SUBTYPES, ATTACK_TYPES, BASE_DAMAGE,
    PHASE_1_END, PHASE_2_END
)


class CurriculumEnemy:
    """3-phase curriculum enemy for RL training.

    Phase 1 (turns 1-5):   Always PHYSICAL
    Phase 2 (turns 6-15):  Cycle PHYSICAL -> CE -> TECHNIQUE, 15% random injection
    Phase 3 (turns 16-25): Target lowest resistance category
    """

    def __init__(self):
        self.turn = 0
        self.pattern = ["PHYSICAL", "CE", "TECHNIQUE"]
        self.pattern_index = 0

    def get_attack(self, turn_number=None, resistances=None):
        """Returns dict: {category, subtype, damage, ignore_armor}.

        Args:
            turn_number: Current turn (1-indexed). Uses internal counter if None.
            resistances: Dict of {PHYSICAL, CE, TECHNIQUE} values for Phase 3.
        """
        if turn_number is not None:
            self.turn = turn_number
        else:
            self.turn += 1

        category = self._select_category(resistances)
        subtype = random.choice(SUBTYPES[category])
        ignore_armor = (subtype == "PIERCE")

        return {
            "category": category,
            "subtype": subtype,
            "damage": BASE_DAMAGE[category],
            "ignore_armor": ignore_armor
        }

    def _select_category(self, resistances=None):
        """Select attack category based on current phase."""
        if self.turn <= PHASE_1_END:
            # Phase 1: Always PHYSICAL
            return "PHYSICAL"

        elif self.turn <= PHASE_2_END:
            # Phase 2: Cycle with random injection
            if random.random() < const.PHASE_2_DEVIATION:
                return random.choice(ATTACK_TYPES)
            else:
                category = self.pattern[self.pattern_index]
                self.pattern_index = (self.pattern_index + 1) % len(self.pattern)
                return category

        else:
            # Phase 3: Target lowest resistance
            if resistances is None:
                return random.choice(ATTACK_TYPES)
            lowest = min(resistances, key=resistances.get)
            return lowest
