# Project Mahoraga — Adaptive Boss Fight Engine

An RL-based combat game inspired by Mahoraga from JJK. The player (sorcerer) fights an adaptive boss that passively gains resistance to repeated attack types. The RL agent must learn to vary attacks, time Domain Expansion, and manage resources to defeat the boss before it fully adapts.

**Trained on Qwen 2.5 3B (LoRA)** using reward-weighted SFT with curriculum difficulty (Easy -> Medium -> Hard).

---

## Quick Start

### Frontend Dashboard (Recommended)

```bash
# Terminal 1: Start the API server
python api.py
# -> FastAPI on http://localhost:8000

# Terminal 2: Start the React dashboard
cd frontend
npm install    # first time only
npm run dev
# -> Dashboard on http://localhost:5173
```

### CLI Mode

```bash
python main.py           # Single random episode
python scripts/diagnose.py     # Strategy comparison
python scripts/trace_medium.py # Step-by-step medium game
```

---

## How The Game Works

### The Boss: Mahoraga

Mahoraga is an **adaptive boss** that passively gains resistance to attack types the player repeats:

- Every time the player hits with the same attack category N times (N = adapt threshold), **the wheel turns**
- Each wheel turn increases resistance to that category by 25%
- After enough wheel turns, Mahoraga unlocks **Cleave** (devastating burst attack)
- Mahoraga can **self-heal once** when below 25% HP

### The Player: Sorcerer (5 Actions)

| Action | Name | Effect |
|--------|------|--------|
| 0 | Physical Strike | 130 base damage, reduced by Physical resistance |
| 1 | CE Blast | 150 base damage, 15% chance for Black Flash (2.5x!) |
| 2 | Technique Strike | 190 base damage, highest risk/reward |
| 3 | Domain Expansion | ONCE per fight: resets all resistances, +75% damage for 3 turns |
| 4 | Reversed Cursed Technique | Heal 250 HP, 4-turn cooldown |

### Key Mechanics

- **Attack Variety**: Repeating the same attack type lets Mahoraga adapt. Cycle between Physical, CE, and Technique
- **Black Flash**: CE attacks have a 15% chance to deal 2.5x damage and reduce boss CE resistance
- **Crit Stack**: 3 consecutive same-type hits deal 1.5x damage (risky — boss adapts faster)
- **Domain Expansion**: Resets boss resistances and gives +75% damage for 3 turns. Timing is crucial
- **Boss Scaling**: Each wheel turn makes Mahoraga's attacks stronger. After 4 turns, it unlocks Cleave (200 dmg)

### Difficulty Levels

| Level | Boss HP | Adapt Threshold | Cleave At | Description |
|-------|---------|----------------|-----------|-------------|
| **Easy** | 1400 | 4 hits | 6 turns | Boss adapts slowly. Good for learning |
| **Medium** | 1800 | 3 hits | 5 turns | Balanced. Strategy matters |
| **Hard** | 2000 | 2 hits | 4 turns | Boss adapts fast. Requires real strategy |

---

## Architecture

```
meta_Mahoraga/
├── api.py                  # FastAPI server (REST + LLM auto-play)
├── main.py                 # CLI: run a single episode
│
├── env/                    # Core RL environment
│   ├── mahoraga_env.py     # MahoragaEnv (player vs boss)
│   ├── mahoraga_boss.py    # MahoragaBoss (adaptive boss logic)
│   ├── mechanics.py        # Damage computation, crit, Black Flash
│   ├── rewards.py          # 10-component reward system
│   ├── state.py            # State dict builder
│   ├── enemy.py            # Legacy CurriculumEnemy (for reference)
│   └── gym_wrapper.py      # Gymnasium-compatible wrapper
│
├── utils/                  # Constants and validation
│   ├── constants.py        # HP, damage, adaptation thresholds
│   └── validators.py       # Action validation
│
├── frontend/               # React + Framer Motion dashboard
│   ├── src/App.jsx         # Main UI component
│   ├── src/index.css       # Design system
│   └── vite.config.js      # Vite + API proxy
│
├── notebooks/              # Training pipeline
│   ├── mahoraga_training.py    # Source (Colab, saves to Drive)
│   └── mahoraga_training.ipynb # Notebook version
│
├── tests/                  # Test suite
│   ├── test_env.py         # Core environment tests (73)
│   └── test_gym_wrapper.py # Gym wrapper tests (33)
│
├── scripts/                # Diagnostic tools
│   ├── diagnose.py         # Strategy comparison
│   ├── trace_medium.py     # Step-by-step medium game trace
│   └── random_agent_gym.py # Random agent baseline
│
└── requirements.txt        # Python dependencies
```

---

## Reward System (10 Components)

| Component | Signal | Purpose |
|-----------|--------|---------|
| Damage Dealt | `+damage / 80` | Encourage aggression |
| Survival | `-damage_taken / 100` | Penalize taking hits |
| Variety | `+0.5` for switching types | Slow boss adaptation |
| Anti-Spam | `-0.8` for 3+ same type | Prevent spamming |
| Domain Timing | `+2.0` if used at high res | Reward smart domain use |
| Domain Waste | `-1.0` if reused | Prevent wasting domain |
| Black Flash | `+1.5` on trigger | Reward CE attacks |
| Wheel Turn | `-1.0` on boss adapt | Punish letting boss adapt |
| Heal Waste | `-1.0` at high HP | Prevent unnecessary healing |
| Terminal | `+12` win / `-10` loss | Strong end-of-episode signal |

---

## Training

- **Model:** Qwen 2.5 3B Instruct (4-bit quantized via Unsloth)
- **Method:** LoRA (r=16, alpha=16) targeting q/k/v/o projections
- **Algorithm:** Reward-weighted SFT with curriculum difficulty
- **Platform:** Google Colab (T4 GPU, saves to Drive)
- **Curriculum:** Easy (60% win gate) -> Medium (40% win gate) -> Hard (30% win gate)

---

## API Reference

| Method | Endpoint | Body | Description |
|--------|----------|------|-------------|
| `POST` | `/api/reset` | `{ "difficulty": "easy"\|"medium"\|"hard" }` | Reset environment |
| `POST` | `/api/step` | `{ "action": 0-4 }` | Execute one manual turn |
| `POST` | `/api/auto-step` | -- | LLM picks the action |
| `GET` | `/api/model-status` | -- | Check if LLM is loaded |

---

## Dependencies

### Backend
```
numpy gymnasium fastapi uvicorn pydantic  # Core
torch transformers peft                   # LLM inference
bitsandbytes accelerate unsloth          # 4-bit quantization
```

### Frontend
```
react framer-motion              # UI + animations
tailwindcss @tailwindcss/vite    # Styling
vite                             # Build tool
```

---

## Team

- **Atishay** (RL Backend, Training Pipeline) -- [GitHub](https://github.com/Atishay9828)
- **Mridul** (Frontend Dashboard, FastAPI Bridge, UI/UX)

---

*"The more it is hit, the more it adapts. That is the nature of Mahoraga."*
