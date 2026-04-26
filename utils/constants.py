# ═══════════════════════════════════════════════
# Project Mahoraga — Game Constants (v2: Boss Redesign)
# ═══════════════════════════════════════════════
# Mahoraga is the BOSS. The player (sorcerer) fights AGAINST it.

# === HP ===
PLAYER_HP = 1500     # Player (sorcerer) HP
MAHORAGA_HP = 2000   # Boss HP (default, used on hard)
MAX_TURNS = 30

# Legacy aliases (for backward compat with gym_wrapper, etc.)
MAX_HP = PLAYER_HP
ENEMY_HP = MAHORAGA_HP

# === Attack Categories ===
ATTACK_TYPES = ["PHYSICAL", "CE", "TECHNIQUE"]

# === Player Attack Damage (what player deals to Mahoraga) ===
PLAYER_DAMAGE = {
    "PHYSICAL": 130,   # Reliable, consistent
    "CE": 150,         # Medium, chance for Black Flash
    "TECHNIQUE": 190,  # Highest damage, highest risk
}

# Legacy alias
BASE_DAMAGE = PLAYER_DAMAGE

# === Mahoraga's Resistance System (passive adaptation) ===
RESISTANCE_MIN = 0
RESISTANCE_MAX = 80       # Cap prevents full immunity
ADAPT_THRESHOLD = 3       # Hits of same type before wheel turns (default)
ADAPT_RESISTANCE_GAIN = 25  # Resistance gained per wheel turn

# Legacy aliases (mechanics.py compat)
ADAPT_INCREASE = 40
ADAPT_DECREASE = 20

# === Mahoraga's Attacks (boss → player, each turn) ===
MAHORAGA_ATTACK_BASE = 80       # Default fist strike (before adaptation)
MAHORAGA_ATTACK_ADAPTED = 100   # After 1+ wheel turns
MAHORAGA_CLEAVE_DAMAGE = 200    # Devastating burst attack
MAHORAGA_CLEAVE_THRESHOLD = 4   # Total adaptations needed for Cleave
MAHORAGA_HEAL_AMOUNT = 250      # One-time self-heal
MAHORAGA_HEAL_HP_THRESHOLD = 0.25  # Heals when below 25% HP

# === Player: Domain Expansion ===
DOMAIN_DAMAGE_MULTIPLIER = 1.75  # +75% damage during domain
DOMAIN_DURATION = 3              # Lasts 3 turns of attacks
DOMAIN_POST_RESISTANCE_BOOST = 15  # Mahoraga gains +15 all res after domain ends

# === Player: Black Flash (passive on CE attacks) ===
BLACK_FLASH_CHANCE = 0.15       # 15% chance on CE attacks
BLACK_FLASH_MULTIPLIER = 2.5    # 2.5x damage
BLACK_FLASH_RESISTANCE_REDUCTION = 15  # Reduces boss CE resistance by 15

# === Player: Reversed Cursed Technique (heal) ===
HEAL_AMOUNT = 250
HEAL_COOLDOWN = 4               # 4-turn cooldown

# === Player: Crit Stack ===
CRIT_STACK_THRESHOLD = 3        # 3 consecutive same-category hits
CRIT_STACK_MULTIPLIER = 1.5     # 1.5x damage on crit

# === Action Mapping (Player's 5 actions) ===
ACTION_PHYSICAL = 0
ACTION_CE = 1
ACTION_TECHNIQUE = 2
ACTION_DOMAIN = 3
ACTION_HEAL = 4
VALID_ACTIONS = [0, 1, 2, 3, 4]

# Action → attack category (for actions 0-2)
ACTION_TO_TYPE = {
    0: "PHYSICAL",
    1: "CE",
    2: "TECHNIQUE",
}

# Legacy aliases
ACTION_ADAPT_PHYSICAL = 0
ACTION_ADAPT_CE = 1
ACTION_ADAPT_TECHNIQUE = 2
ACTION_JUDGMENT = 3
ACTION_REGENERATION = 4

# === Subtypes (flavor text for attacks) ===
SUBTYPES = {
    "PHYSICAL": ["SLASH", "IMPACT", "PIERCE"],
    "CE": ["BLAST", "WAVE", "BEAM"],
    "TECHNIQUE": ["SPIKE", "DELAYED", "PATTERN"],
}

# === Subtype Effects ===
ARMOR_BYPASS_RATIO = 0.2  # PIERCE ignores 20% resistance

# === Curriculum Enemy Phases (legacy, kept for old CurriculumEnemy) ===
PHASE_1_END = 5
PHASE_2_END = 15
PHASE_2_DEVIATION = 0.15

# === Difficulty levels ===
# Higher difficulty = boss adapts faster, has more HP, stronger attacks
DIFFICULTY_CONFIG = {
    "easy": {
        "description": "Boss adapts slowly, lower HP. Good for learning.",
        "adapt_threshold": 4,
        "resistance_max": 60,
        "cleave_threshold": 6,
        "boss_hp": 1400,
        "opponent_pattern": "repeat",
        "opponent_randomness": 0.05,
    },
    "medium": {
        "description": "Balanced difficulty. Boss adapts after 3 same-type hits.",
        "adapt_threshold": 3,
        "resistance_max": 70,
        "cleave_threshold": 5,
        "boss_hp": 1800,
        "opponent_pattern": "cycle",
        "opponent_randomness": 0.15,
    },
    "hard": {
        "description": "Boss adapts after 2 hits, full HP, Cleave unlocks at 4 turns.",
        "adapt_threshold": 2,
        "resistance_max": 80,
        "cleave_threshold": 4,
        "boss_hp": MAHORAGA_HP,
        "opponent_pattern": "random",
        "opponent_randomness": 0.85,
    },
}
