# === HP ===
MAX_HP = 1200       # Agent HP
ENEMY_HP = 1000     # Enemy HP (asymmetric)
MAX_TURNS = 25

# === Attack Categories (RL Level) ===
ATTACK_TYPES = ["PHYSICAL", "CE", "TECHNIQUE"]

# === Base Damage per Category ===
BASE_DAMAGE = {
    "PHYSICAL": 120,
    "CE": 150,
    "TECHNIQUE": 220
}

# === Resistance ===
RESISTANCE_MIN = 0
RESISTANCE_MAX = 80
ADAPT_INCREASE = 40
ADAPT_DECREASE = 20

# === Judgment Strike ===
JUDGMENT_BASE_DAMAGE = 100
JUDGMENT_BURST_DAMAGE = 350

# === Regeneration ===
HEAL_AMOUNT = 300
HEAL_COOLDOWN = 3

# === Action Mapping ===
ACTION_ADAPT_PHYSICAL = 0
ACTION_ADAPT_CE = 1
ACTION_ADAPT_TECHNIQUE = 2
ACTION_JUDGMENT = 3
ACTION_REGENERATION = 4
VALID_ACTIONS = [0, 1, 2, 3, 4]

# === Action to Resistance Category ===
ACTION_TO_TYPE = {
    0: "PHYSICAL",
    1: "CE",
    2: "TECHNIQUE"
}

# === Subtypes ===
SUBTYPES = {
    "PHYSICAL": ["SLASH", "IMPACT", "PIERCE"],
    "CE": ["BLAST", "WAVE", "BEAM"],
    "TECHNIQUE": ["SPIKE", "DELAYED", "PATTERN"]
}

# === Subtype Effects ===
ARMOR_BYPASS_RATIO = 0.2  # PIERCE ignores 20% resistance (ignore_armor)

# === Curriculum Enemy Phases ===
PHASE_1_END = 5     # Turns 1-5: always PHYSICAL
PHASE_2_END = 15    # Turns 6-15: cycling with 15% randomness
PHASE_2_DEVIATION = 0.15
