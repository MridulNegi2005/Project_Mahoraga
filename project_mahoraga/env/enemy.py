"""
Enemy — 3-Phase Teaching Curriculum
====================================
Implements a progressive enemy AI that escalates across three phases:

  Phase 1 (Turns 1-5):   PHYSICAL only, random subtype.
  Phase 2 (Turns 6-15):  Strict PHYS→CE→TECH loop, 15% RNG break chance.
  Phase 3 (Turns 16-25): Adaptive — targets Mahoraga's lowest resistance.

Each attack is returned as a rich dict with category, subtype, damage,
and an ignore_armor flag (True only for Pierce).
"""

import random
from typing import Dict, List, Optional


# ──────────────────────────────────────────────
# ATTACK DATABASE
# ──────────────────────────────────────────────
ATTACK_DATA: Dict[str, List[Dict]] = {
    "PHYSICAL": [
        {"subtype": "Slash",  "damage": 120, "ignore_armor": False},
        {"subtype": "Impact", "damage": 140, "ignore_armor": False},
        {"subtype": "Pierce", "damage": 100, "ignore_armor": True},
    ],
    "CE": [
        {"subtype": "Beam",  "damage": 150, "ignore_armor": False},
        {"subtype": "Wave",  "damage": 130, "ignore_armor": False},
        {"subtype": "Blast", "damage": 170, "ignore_armor": False},
    ],
    "TECHNIQUE": [
        {"subtype": "Delayed", "damage": 220, "ignore_armor": False},
        {"subtype": "Pattern", "damage": 190, "ignore_armor": False},
        {"subtype": "Spike",   "damage": 250, "ignore_armor": False},
    ],
}

CATEGORIES: List[str] = ["PHYSICAL", "CE", "TECHNIQUE"]

# Phase 2 strict loop order
PHASE2_LOOP: List[str] = ["PHYSICAL", "CE", "TECHNIQUE"]

# Phase boundaries (inclusive)
PHASE1_END = 5
PHASE2_END = 15
PHASE3_END = 25

# Phase 2 RNG break chance
PHASE2_BREAK_CHANCE = 0.15

# Pierce armor-ignore percentage (bypasses this fraction of resistance)
PIERCE_ARMOR_IGNORE = 0.20


class Enemy:
    """
    3-phase teaching-curriculum enemy for the Mahoraga Adaptation Engine.

    Tracks its own internal turn counter. Call `get_attack()` once per turn
    to advance the counter and receive the next attack.

    Returns
    -------
    dict with keys: category, subtype, damage, ignore_armor
    Also supports legacy tuple unpacking via `get_attack_tuple()`.
    """

    def __init__(self, seed: Optional[int] = None) -> None:
        self._rng = random.Random(seed)
        self.turn: int = 0

    def reset(self) -> None:
        """Reset the turn counter for a new episode."""
        self.turn = 0

    # ──────────────────────────────────────────
    # PUBLIC API
    # ──────────────────────────────────────────

    def get_attack(
        self,
        mahoraga_resistances: Optional[Dict[str, int]] = None,
    ) -> tuple:
        """
        Advance the turn counter and return the next attack.

        Parameters
        ----------
        mahoraga_resistances : dict, optional
            e.g. {"PHYSICAL": 40, "CE": 80, "TECHNIQUE": 0}.
            Required for Phase 3 (turns 16+). Ignored in earlier phases.

        Returns
        -------
        tuple (attack_type: str, subtype: str)
            Backwards-compatible with the existing MahoragaEnv integration.
            Use `get_attack_dict()` for the full rich payload.
        """
        self.turn += 1
        attack = self._select_attack(mahoraga_resistances)
        self._last_attack = attack
        return attack["category"], attack["subtype"]

    def get_attack_dict(
        self,
        mahoraga_resistances: Optional[Dict[str, int]] = None,
    ) -> Dict:
        """
        Advance the turn counter and return the full attack dictionary.

        Returns
        -------
        dict  {"category": str, "subtype": str, "damage": int, "ignore_armor": bool}
        """
        self.turn += 1
        attack = self._select_attack(mahoraga_resistances)
        self._last_attack = attack
        return attack

    @property
    def last_attack(self) -> Optional[Dict]:
        """The most recent attack dict, or None if no attacks yet."""
        return getattr(self, "_last_attack", None)

    @property
    def current_phase(self) -> int:
        """Return 1, 2, or 3 based on the current turn."""
        if self.turn <= PHASE1_END:
            return 1
        elif self.turn <= PHASE2_END:
            return 2
        else:
            return 3

    # ──────────────────────────────────────────
    # INTERNAL PHASE LOGIC
    # ──────────────────────────────────────────

    def _select_attack(
        self,
        mahoraga_resistances: Optional[Dict[str, int]],
    ) -> Dict:
        """Route to the correct phase handler based on turn count."""
        if self.turn <= PHASE1_END:
            return self._phase1_attack()
        elif self.turn <= PHASE2_END:
            return self._phase2_attack()
        else:
            return self._phase3_attack(mahoraga_resistances)

    def _phase1_attack(self) -> Dict:
        """
        Phase 1 (Turns 1-5): Always PHYSICAL, random subtype.
        """
        return self._random_subtype("PHYSICAL")

    def _phase2_attack(self) -> Dict:
        """
        Phase 2 (Turns 6-15): Strict PHYS→CE→TECH loop.
        15% chance per turn to break the loop and pick any random category.
        """
        if self._rng.random() < PHASE2_BREAK_CHANCE:
            # RNG break — pick any random category
            category = self._rng.choice(CATEGORIES)
        else:
            # Strict loop: turn 6→PHYS, 7→CE, 8→TECH, 9→PHYS, ...
            loop_index = (self.turn - PHASE1_END - 1) % len(PHASE2_LOOP)
            category = PHASE2_LOOP[loop_index]

        return self._random_subtype(category)

    def _phase3_attack(
        self,
        mahoraga_resistances: Optional[Dict[str, int]],
    ) -> Dict:
        """
        Phase 3 (Turns 16-25): Adaptive AI.
        Targets the category where Mahoraga has the lowest resistance.
        Ties are broken randomly.
        """
        if mahoraga_resistances is None:
            # Fallback: if no resistances provided, pick randomly
            category = self._rng.choice(CATEGORIES)
        else:
            min_val = min(mahoraga_resistances[c] for c in CATEGORIES)
            weakest = [c for c in CATEGORIES if mahoraga_resistances[c] == min_val]
            category = self._rng.choice(weakest)

        return self._random_subtype(category)

    # ──────────────────────────────────────────
    # HELPERS
    # ──────────────────────────────────────────

    def _random_subtype(self, category: str) -> Dict:
        """Pick a random subtype from the given category and return the attack dict."""
        entry = self._rng.choice(ATTACK_DATA[category])
        return {
            "category": category,
            "subtype": entry["subtype"],
            "damage": entry["damage"],
            "ignore_armor": entry["ignore_armor"],
        }
