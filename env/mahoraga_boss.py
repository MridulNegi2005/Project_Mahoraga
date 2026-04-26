"""
MahoragaBoss — The adaptive boss that passively gains resistance.

In JJK, Mahoraga adapts to whatever damages it. The more you hit it
with the same attack type, the more resistant it becomes. Its wheel
turns each time it adapts, and after enough adaptations it unlocks
devastating Cleave attacks.
"""
import random
from utils.constants import (
    ATTACK_TYPES, SUBTYPES,
    MAHORAGA_ATTACK_BASE, MAHORAGA_ATTACK_ADAPTED, MAHORAGA_CLEAVE_DAMAGE,
    MAHORAGA_HEAL_AMOUNT, MAHORAGA_HEAL_HP_THRESHOLD,
    RESISTANCE_MIN, DIFFICULTY_CONFIG,
)


class MahoragaBoss:
    """Mahoraga — the adaptive boss.

    Passive Mechanics:
        - Tracks how many times each attack category hits it
        - After `adapt_threshold` hits of the same type, the wheel turns:
          → resistance to that category increases
        - After `cleave_threshold` total wheel turns → unlocks Cleave attack

    Attacks (chosen automatically each turn):
        - Fist Strike (default): base damage
        - Adapted Strike (1+ wheel turns): higher damage
        - Cleave (3+ total turns): devastating burst
        - Self-heal: once per fight when HP < 30%
    """

    def __init__(self, difficulty="hard"):
        self.difficulty = difficulty.lower()
        config = DIFFICULTY_CONFIG.get(self.difficulty, DIFFICULTY_CONFIG["hard"])

        self.adapt_threshold = config["adapt_threshold"]
        self.resistance_max = config["resistance_max"]
        self.cleave_threshold = config["cleave_threshold"]
        self.max_hp = config["boss_hp"]

        self.reset()

    def reset(self):
        """Reset boss state for a new episode."""
        self.hp = self.max_hp
        self.resistances = {"PHYSICAL": 0, "CE": 0, "TECHNIQUE": 0}
        self.hit_counters = {"PHYSICAL": 0, "CE": 0, "TECHNIQUE": 0}
        self.total_wheel_turns = 0
        self.has_healed = False
        self.domain_blocked_turns = 0  # Turns where adaptation is blocked (Domain)
        self.heal_blocked_turns = 0    # Turns where self-heal is blocked (Domain)

    # ──────────────────────────────────────────────
    # Passive Adaptation (called when player hits boss)
    # ──────────────────────────────────────────────

    def receive_hit(self, category):
        """Track a hit and potentially adapt (wheel turn).

        Args:
            category: "PHYSICAL", "CE", or "TECHNIQUE"

        Returns:
            dict with adaptation info:
                adapted: bool — did the wheel turn?
                category: str — what category was adapted to
                new_resistance: int — new resistance value for that category
        """
        if self.domain_blocked_turns > 0:
            # Domain Expansion blocks adaptation
            return {"adapted": False, "category": category, "new_resistance": self.resistances[category]}

        self.hit_counters[category] += 1

        if self.hit_counters[category] >= self.adapt_threshold:
            # WHEEL TURNS — adapt!
            self.hit_counters[category] = 0  # Reset counter for this type
            old_res = self.resistances[category]
            from utils.constants import ADAPT_RESISTANCE_GAIN
            new_res = min(self.resistance_max, old_res + ADAPT_RESISTANCE_GAIN)
            self.resistances[category] = new_res
            self.total_wheel_turns += 1
            return {"adapted": True, "category": category, "new_resistance": new_res}

        return {"adapted": False, "category": category, "new_resistance": self.resistances[category]}

    # ──────────────────────────────────────────────
    # Boss Attack Selection
    # ──────────────────────────────────────────────

    def choose_attack(self):
        """Select Mahoraga's attack for this turn.

        Returns:
            dict: {name, damage, category, subtype, is_cleave}
        """
        # Self-heal check (once per fight, when below threshold)
        if not self.has_healed and self.hp < self.max_hp * MAHORAGA_HEAL_HP_THRESHOLD:
            if self.heal_blocked_turns <= 0:
                self.has_healed = True
                heal_amount = min(MAHORAGA_HEAL_AMOUNT, self.max_hp - self.hp)
                self.hp += heal_amount
                return {
                    "name": "Positive Energy Heal",
                    "damage": 0,
                    "heal": heal_amount,
                    "category": None,
                    "subtype": None,
                    "is_cleave": False,
                }

        # Attack selection
        category = random.choice(ATTACK_TYPES)
        subtype = random.choice(SUBTYPES[category])

        if self.total_wheel_turns >= self.cleave_threshold:
            # Cleave unlocked — 40% chance to use it
            if random.random() < 0.40:
                return {
                    "name": "Cleave",
                    "damage": MAHORAGA_CLEAVE_DAMAGE,
                    "heal": 0,
                    "category": category,
                    "subtype": "CLEAVE",
                    "is_cleave": True,
                }

        if self.total_wheel_turns >= 1:
            damage = MAHORAGA_ATTACK_ADAPTED + (self.total_wheel_turns * 10)
        else:
            damage = MAHORAGA_ATTACK_BASE

        return {
            "name": "Adapted Strike" if self.total_wheel_turns >= 1 else "Fist Strike",
            "damage": damage,
            "heal": 0,
            "category": category,
            "subtype": subtype,
            "is_cleave": False,
        }

    # ──────────────────────────────────────────────
    # Domain Expansion Effects
    # ──────────────────────────────────────────────

    def apply_domain_start(self, duration):
        """Domain Expansion was activated by the player.
        Resets all resistances and blocks adaptation."""
        self.resistances = {"PHYSICAL": 0, "CE": 0, "TECHNIQUE": 0}
        self.hit_counters = {"PHYSICAL": 0, "CE": 0, "TECHNIQUE": 0}
        self.domain_blocked_turns = duration
        self.heal_blocked_turns = duration

    def apply_domain_end(self, resistance_boost):
        """Domain ended — Mahoraga adapts to the domain itself."""
        for cat in ATTACK_TYPES:
            self.resistances[cat] = min(
                self.resistance_max,
                self.resistances[cat] + resistance_boost
            )

    def tick_domain(self):
        """Decrement domain block counters (adaptation + heal blocks)."""
        if self.domain_blocked_turns > 0:
            self.domain_blocked_turns -= 1
        if self.heal_blocked_turns > 0:
            self.heal_blocked_turns -= 1

    # ──────────────────────────────────────────────
    # Reduce resistance (Black Flash effect)
    # ──────────────────────────────────────────────

    def reduce_resistance(self, category, amount):
        """Reduce boss resistance for a category (e.g. Black Flash)."""
        self.resistances[category] = max(
            RESISTANCE_MIN,
            self.resistances[category] - amount
        )

    def get_state(self):
        """Return boss state dict for observation."""
        return {
            "hp": self.hp,
            "max_hp": self.max_hp,
            "resistances": dict(self.resistances),
            "hit_counters": dict(self.hit_counters),
            "total_wheel_turns": self.total_wheel_turns,
            "has_healed": self.has_healed,
            "domain_blocked": self.domain_blocked_turns > 0,
        }
