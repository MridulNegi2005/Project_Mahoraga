# ═══════════════════════════════════════════════
# Project Mahoraga — Game Constants (v2: Boss Redesign)
# ═══════════════════════════════════════════════
# Mahoraga is the BOSS. The player (sorcerer) fights AGAINST it.

# === HP ===
PLAYER_HP = 1200     # Player (sorcerer) HP
MAHORAGA_HP = 2000   # Boss HP (tanky adaptive boss)
MAX_TURNS = 30       # Increased from 25 for bigger boss fight

# Legacy aliases (for backward compat with gym_wrapper, etc.)
MAX_HP = PLAYER_HP
ENEMY_HP = MAHORAGA_HP

# === Attack Categories ===
ATTACK_TYPES = ["PHYSICAL", "CE", "TECHNIQUE"]

# === Player Attack Damage (what player deals to Mahoraga) ===
PLAYER_DAMAGE = {
    "PHYSICAL": 120,   # Reliable, consistent
    "CE": 150,         # Medium, chance for Black Flash
    "TECHNIQUE": 220,  # Highest damage, highest risk
}

# Legacy alias
BASE_DAMAGE = PLAYER_DAMAGE

# === Mahoraga's Resistance System (passive adaptation) ===
RESISTANCE_MIN = 0
RESISTANCE_MAX = 90       # Boss can get near-immune
ADAPT_THRESHOLD = 2       # Hits of same type before wheel turns
ADAPT_RESISTANCE_GAIN = 30  # Resistance gained per wheel turn

# Legacy aliases (mechanics.py compat)
ADAPT_INCREASE = 40
ADAPT_DECREASE = 20

# === Mahoraga's Attacks (boss → player, each turn) ===
MAHORAGA_ATTACK_BASE = 100      # Default fist strike
MAHORAGA_ATTACK_ADAPTED = 130   # After 1+ wheel turns
MAHORAGA_CLEAVE_DAMAGE = 250    # Unlocked at 3+ total adaptations
MAHORAGA_CLEAVE_THRESHOLD = 3   # Total adaptations needed for Cleave
MAHORAGA_HEAL_AMOUNT = 300      # One-time self-heal
MAHORAGA_HEAL_HP_THRESHOLD = 0.30  # Heals when below 30% HP

# === Player: Domain Expansion ===
DOMAIN_DAMAGE_MULTIPLIER = 1.5  # +50% damage during domain
DOMAIN_DURATION = 3             # Lasts 3 turns
DOMAIN_POST_RESISTANCE_BOOST = 20  # Mahoraga gains +20 all res after domain ends

# === Player: Black Flash (passive on CE attacks) ===
BLACK_FLASH_CHANCE = 0.15       # 15% chance on CE attacks
BLACK_FLASH_MULTIPLIER = 2.5    # 2.5x damage
BLACK_FLASH_RESISTANCE_REDUCTION = 20  # Reduces boss CE resistance by 20

# === Player: Reversed Cursed Technique (heal) ===
HEAL_AMOUNT = 250
HEAL_COOLDOWN = 4               # 4-turn cooldown (up from 3)

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

# === Difficulty (from Mahoraga's perspective) ===
# Difficulty controls the OPPONENT's (sorcerer's) attack behavior,
# which determines how easy/hard it is for Mahoraga to predict and adapt.
# Mahoraga's own stats (HP, adaptation, etc.) are IDENTICAL across difficulties.
DIFFICULTY_CONFIG = {
    "easy": {
        # Opponent repeats the same attack type → easy for Mahoraga to adapt
        "opponent_pattern": "repeat",   # Always same category
        "opponent_randomness": 0.05,    # 5% chance of random deviation
        "description": "Opponent spams one attack type. Easy to predict.",
        # Boss stats (same across all)
        "adapt_threshold": 2,
        "resistance_max": 90,
        "cleave_threshold": 3,
        "boss_hp": MAHORAGA_HP,
    },
    "medium": {
        # Opponent cycles PHYSICAL → CE → TECHNIQUE predictably
        "opponent_pattern": "cycle",    # Predictable rotation
        "opponent_randomness": 0.15,    # 15% random deviation
        "description": "Opponent cycles attacks. Mahoraga must detect patterns.",
        "adapt_threshold": 2,
        "resistance_max": 90,
        "cleave_threshold": 3,
        "boss_hp": MAHORAGA_HP,
    },
    "hard": {
        # Opponent attacks near-randomly → very hard for Mahoraga to predict
        "opponent_pattern": "random",   # Weighted random
        "opponent_randomness": 0.85,    # 85% random, 15% strategic (hits weakest res)
        "description": "Opponent is unpredictable. Mahoraga must generalize.",
        "adapt_threshold": 2,
        "resistance_max": 90,
        "cleave_threshold": 3,
        "boss_hp": MAHORAGA_HP,
    },
}
