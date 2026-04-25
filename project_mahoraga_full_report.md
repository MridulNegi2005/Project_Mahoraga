# Project Mahoraga — Complete System Report

> **Version**: 1.0 (Post-Merge)
> **Branch**: `main` (fully merged from `phase1-env-setup`)
> **Tests**: 143/143 passing
> **Date**: 2026-04-25

---

## 1. Project Overview

**Project Mahoraga** is a reinforcement learning environment where an AI agent ("Mahoraga") learns adaptive combat through a resistance trade-off system. Named after Jujutsu Kaisen's Mahoraga — a shikigami that adapts to any attack — the system trains an LLM (Qwen 2.5 3B) to make tactical decisions in a turn-based combat loop.

**Core Loop**: `Observe → Adapt → Accumulate → Punish`

The agent must:
1. Observe enemy attack patterns
2. Build resistance to the correct attack category
3. Accumulate adaptation stacks
4. Execute Judgment Strike for burst damage at the right moment

**This is NOT a game.** It is a clean, testable RL environment designed for LLM fine-tuning via reward-weighted SFT.

---

## 2. Architecture Breakdown

```
project_mahoraga/
├── env/
│   ├── mahoraga_env.py      # Main environment orchestrator
│   ├── mechanics.py         # Resistance, damage, action math
│   ├── enemy.py             # CurriculumEnemy (3-phase AI)
│   ├── rewards.py           # 6-component composable reward system
│   ├── state.py             # State dict builder
│   └── gym_wrapper.py       # Gymnasium-compatible wrapper
├── utils/
│   ├── constants.py         # All game constants and mappings
│   └── validators.py        # Action validation
├── tests/
│   ├── test_env.py          # 110 core tests
│   └── test_gym_wrapper.py  # 33 wrapper tests
├── notebooks/
│   ├── mahoraga_training.py     # Training notebook (source)
│   └── mahoraga_training.ipynb  # Training notebook (Kaggle)
├── scripts/
│   └── random_agent_gym.py  # Random agent demo
├── app.py                   # Gradio interactive UI
├── main.py                  # CLI episode runner
└── README.md
```

### Module Details

#### `env/mahoraga_env.py` — Environment Orchestrator
- `MahoragaEnv(debug=False)` — main class
- `reset()` → returns state dict
- `step(action)` → returns `(state, reward, done, info)`
- Coordinates enemy attacks, agent actions, reward computation
- Tracks: HP, resistances, adaptation stack, heal cooldown, last adapted category

#### `env/mechanics.py` — Core Math
- `new_resistances()` — creates `{PHYSICAL: 0, CE: 0, TECHNIQUE: 0}`
- `apply_resistance_change(res, type)` — +40 target, -20 others, clamp [0,80]
- `compute_enemy_damage(category, res, ignore_armor)` — damage formula
- `compute_judgment_damage(last_adapted, enemy_cat)` — adaptation-match burst
- `apply_action_effects(...)` — dispatches action 0-4
- `check_correct_adaptation(action, category)` — validates adaptation

#### `env/enemy.py` — CurriculumEnemy
- Single `CurriculumEnemy` class with 3-phase behavior
- `get_attack(turn_number, resistances)` → `{category, subtype, damage, ignore_armor}`
- Phase selection based on turn number

#### `env/rewards.py` — Composable Rewards
- 6 independent functions + 1 aggregator
- Returns dict, NOT a single scalar
- `compute_rewards(info, state, action, done)` → dict

#### `env/state.py` — State Builder
- Converts internal uppercase keys to lowercase for RL observation
- `build_state_dict(...)` → dict with 7 keys

#### `env/gym_wrapper.py` — Gymnasium Interface
- `MahoragaGymEnv(gym.Env)` wraps `MahoragaEnv`
- `Discrete(5)` action space, `Dict` observation space
- Encodes categoricals to integers for neural networks

#### `app.py` — Gradio UI
- Interactive combat arena with 5 action buttons
- Displays HP, resistances, stack, cooldown, combat log
- Launch: `python app.py`

---

## 3. Core Mechanics

### Resistance System
Three categories: **PHYSICAL**, **CE**, **TECHNIQUE**. Range: [0, 80].

When agent adapts to a category:
- Target category: **+40**
- Other categories: **-20**
- All clamped to [0, 80]

Higher resistance = less damage from that category.

### Action Space (0–4)

| Action | Name | Effect |
|--------|------|--------|
| 0 | Adapt PHYSICAL | +40 PHYSICAL res, -20 others |
| 1 | Adapt CE | +40 CE res, -20 others |
| 2 | Adapt TECHNIQUE | +40 TECHNIQUE res, -20 others |
| 3 | Judgment Strike | Deal damage, consume stacks, reset res |
| 4 | Regeneration | +300 HP, 3-turn cooldown |

### Adaptation Stack
- +1 when agent correctly adapts to current enemy attack category
- Consumed by Judgment Strike: each stack adds +50 damage
- Reset to 0 after Judgment Strike

### Judgment Strike Logic
**Condition**: Burst (350 dmg) if `last_adapted_category == current_enemy_category`
**Otherwise**: Base (100 dmg)
**Total**: `burst_or_base + (stacks × 50)`
**After**: Resistances reset to 0, stacks reset to 0

### Heal Cooldown
- Heals +300 HP (capped at MAX_HP=1200)
- 3-turn cooldown after use
- Does NOT reset resistances
- If used while on cooldown → wasted turn (action nullified)

### Damage Formula
```
resistance = category_resistance
if ignore_armor:
    resistance = resistance × 0.8    # 20% bypass (PIERCE only)
damage = base_damage × (1 - resistance / 100)
```

### HP Configuration
| Entity | HP |
|--------|----|
| Agent (Mahoraga) | 1200 |
| Enemy | 1000 |

---

## 4. Enemy System — CurriculumEnemy

Three-phase curriculum designed for progressive learning:

### Phase 1: Tutorial (Turns 1–5)
- Always attacks with **PHYSICAL**
- Agent learns basic adaptation against a single category
- Predictable — builds confidence

### Phase 2: Pattern (Turns 6–15)
- Cycles: **PHYSICAL → CE → TECHNIQUE**
- 15% random injection (picks random category instead of pattern)
- Agent learns to predict cycling patterns and handle surprises

### Phase 3: Adaptive (Turns 16–25)
- **Targets the agent's lowest resistance category**
- Reads `resistances` dict, picks `min(resistances, key=resistances.get)`
- Agent must learn balanced defense or get exploited
- If no resistances provided, falls back to random

### Subtypes
Each category has 3 subtypes (visual/variation only):

| Category | Subtypes |
|----------|----------|
| PHYSICAL | SLASH, IMPACT, **PIERCE** |
| CE | BLAST, WAVE, BEAM |
| TECHNIQUE | SPIKE, DELAYED, PATTERN |

**PIERCE** is special: `ignore_armor=True` → bypasses 20% of resistance.

### Attack Dict Schema (LOCKED)
```python
{
    "category": "PHYSICAL" | "CE" | "TECHNIQUE",
    "subtype": "SLASH" | "IMPACT" | ... ,
    "damage": int,
    "ignore_armor": bool
}
```

---

## 5. Reward System

Six independent components computed per step. Final reward = sum of all components.

| Component | Formula | Purpose | Typical Range |
|-----------|---------|---------|---------------|
| **Survival** | `-(damage_taken / 100)` | Penalize taking damage | [-2.2, 0] |
| **Combat** | `+(damage_dealt / 100)` | Reward dealing damage | [0, 4.5] |
| **Adaptation** | `+1.5` if correct, else `0` | **Strongest signal** — correct resistance match | {0, 1.5} |
| **Anti-Cowardice** | `-1.0` if heal at >70% HP | Prevent heal spam exploit | {-1.0, 0} |
| **Efficiency** | `+0.5` if damage >= 200 | Encourage big hits | {0, 0.5} |
| **Terminal** | `+5.0` win / `-5.0` loss | Strong episode-end signal | {-5.0, 0, 5.0} |

### Why Each Exists
- **Survival**: Without it, agent ignores defense
- **Combat**: Without it, agent never attacks
- **Adaptation**: Core learning signal — the entire point of Mahoraga
- **Anti-Cowardice**: Agent discovers healing is "safe" and spams it; this prevents that
- **Efficiency**: Encourages building stacks before striking instead of weak Judgments
- **Terminal**: Large signal at episode boundary for credit assignment

### Reward Breakdown
Every `step()` returns `info["reward_breakdown"]` with all 6 components as a dict. This is critical for debugging and analysis.

---

## 6. Training Pipeline

### Model: Qwen 2.5 3B Instruct (via Unsloth)
- 4-bit quantized loading
- LoRA: r=16, targets q/k/v/o_proj, no bias
- max_seq_length: 1024

### Prompt Design
```
You are Mahoraga, an adaptive combat agent...
Current State: HP, resistances, last attack, turn
Available Actions: 0-4 with descriptions + strategy hints
→ Return ONLY a single integer (0-4)
```

### Rollout Loop
1. Reset env
2. For each turn: build prompt → generate → parse action → env.step()
3. Collect trajectory: `{prompt, response, action, reward, state, info}`
4. Track: total reward, correct adaptation rate, win/loss

### Reward-Weighted SFT (GRPO-style)
Instead of PPO (complex, unstable on T4s), uses reward-weighted supervised fine-tuning:
- Collect episodes with current model
- Weight actions by reward: **>1.0 → 3 copies**, **>0 → 2**, **>-1.5 → 1**, **else → skip**
- Fine-tune via SFTTrainer on weighted dataset
- Repeat for N iterations

### Training Loop
```
for iteration in range(5):
    episodes = collect_episodes(10)
    dataset = reward_weight(episodes)
    sft_train(model, dataset)
    save_checkpoint()
    log_metrics()
```

### Checkpoints & Metrics
- LoRA weights saved per iteration: `/kaggle/working/checkpoints/iteration_N/`
- Metrics JSON: avg_reward, win_rate, avg_steps, adapt_rate
- Plot: 3-panel chart (reward, win rate, adaptation rate vs iteration)

---

## 7. UI System (Gradio)

### Structure
- 5 action buttons (Adapt×3, Judgment, Heal) + Reset
- Two columns: Agent stats (HP, resistances, stack, cooldown) | Enemy stats (HP, turn, reward)
- Monospace combat log

### State Mapping
UI reads directly from `MahoragaEnv` instance — no intermediary layer.

### Log Format
```
Turn X:
  Enemy:
    → [Subtype] ([Category])
  Mahoraga:
    → [Action]
  Result:
    → Damage: Y | Correct Adaptation: YES/NO | Stack: Z
    → Reward: R.RR
```

---

## 8. Data Flow

```
┌─────────┐    ┌──────────┐    ┌───────┐    ┌────────┐    ┌─────┐
│  State   │───▶│  Prompt  │───▶│ Model │───▶│ Action │───▶│ Env │
│  Dict    │    │ Builder  │    │ (LLM) │    │ Parser │    │     │
└─────────┘    └──────────┘    └───────┘    └────────┘    └──┬──┘
                                                             │
     ┌───────────────────────────────────────────────────────┘
     │
     ▼
┌──────────┐    ┌──────────┐    ┌──────────────┐
│ Rewards  │───▶│ Dataset  │───▶│ SFT Trainer  │
│ (6 comp) │    │ (weight) │    │ (LoRA update)│
└──────────┘    └──────────┘    └──────────────┘
```

1. **State** → 7-key dict (HP, resistances, last attack, turn, etc.)
2. **Prompt** → Natural language with state + action descriptions
3. **Model** → Generates single integer 0-4
4. **Parser** → Extracts int, fallback to 0
5. **Env** → Applies action, computes damage, checks termination
6. **Rewards** → 6 independent components, summed to scalar
7. **Dataset** → High-reward actions duplicated, low-reward filtered
8. **Training** → SFT on weighted dataset updates LoRA weights

---

## 9. Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| **Unified schema** (`category/damage/ignore_armor`) | Two teams used different field names; unified to prevent silent bugs |
| **CurriculumEnemy** | Progressive difficulty prevents early collapse; Phase 3 forces balanced play |
| **Adaptation-match Judgment** | Old threshold-based burst was exploitable; matching requires tactical awareness |
| **Composable rewards (NOT monolithic)** | Debugging, tuning, and analysis require visibility into individual signals |
| **Reward-weighted SFT over PPO** | PPO on T4 GPUs with LLMs is unstable; GRPO-style SFT is simpler and proven |
| **Asymmetric HP (1200 vs 1000)** | Slight agent advantage encourages exploration; symmetric HP led to agent always losing |
| **Heal does NOT reset resistances** | Prevents heal+reset exploit that nullifies adaptation investment |

---

## 10. Known Risks / Edge Cases

| Risk | Description | Mitigation |
|------|-------------|------------|
| **Reward imbalance** | Adaptation (+1.5) may dominate over combat signals | Monitor adapt_rate; if >80%, reduce adaptation reward |
| **Over-adaptation** | Agent may only adapt, never attack | Terminal reward (-5.0 loss) penalizes passive play |
| **Phase 3 exploit** | Agent could learn to keep all resistances equal to confuse Phase 3 | Phase 3 picks min, so equal res still gets attacked |
| **Training instability** | SFT on small datasets can overfit | Use gradient accumulation, low LR (2e-5), 1 epoch per iter |
| **Heal spam** | Agent learns heal is safe | Anti-cowardice penalty (-1.0) + cooldown (3 turns) |
| **Wasted turns** | Heal on cooldown wastes a turn | Action nullified, no positive rewards possible |
| **PIERCE bypass** | 20% resistance bypass can surprise agent | Only 1/3 chance of PIERCE subtype, negligible long-term |
| **Zero reward on notebook** | Cloning wrong branch (main vs phase1-env-setup) | Notebook has `--branch phase1-env-setup` + assertion check |

---

## 11. How to Run

### Local Environment
```bash
cd project_mahoraga
python main.py                  # Run random episode
python tests/test_env.py        # Run 110 core tests
python tests/test_gym_wrapper.py  # Run 33 gym tests
```

### Gradio UI
```bash
cd project_mahoraga
python app.py                   # Opens browser at localhost:7860
```

### Kaggle Training
1. Upload `notebooks/mahoraga_training.ipynb` to Kaggle
2. Enable **GPU** (2× T4)
3. Run all 14 cells in order
4. Model saves to `/kaggle/working/mahoraga_lora_final`

### Debug Mode
```python
env = MahoragaEnv(debug=True)
# Prints reward breakdown every step
```

---

## 12. Future Improvements

| Area | Improvement | Effort |
|------|-------------|--------|
| **Training** | Replace reward-weighted SFT with true GRPO/PPO | High |
| **Enemy** | Add Phase 4: combo attacks (multi-type per turn) | Medium |
| **Enemy** | Better randomness model (Markov chain instead of uniform) | Medium |
| **Rewards** | Dynamic reward scaling based on training progress | Medium |
| **Multi-agent** | Two Mahoraga agents competing | High |
| **Observation** | Add enemy history buffer (last N attacks) to state | Low |
| **UI** | Add resistance bar charts, HP progress graphs | Low |
| **Eval** | Automated benchmark suite (win rate vs each phase) | Medium |
| **Deploy** | HuggingFace Spaces deployment for Gradio UI | Low |

---

## 13. Git History

```
ec92cdd MERGE: Unified schema, CurriculumEnemy, Gradio UI
c8f2f7c CRITICAL FIX: Clone correct branch + debug mode
cfb710a Phase 5: Kaggle training notebook
e9f91da Phase 4: Gymnasium wrapper
fd4d842 Phase 3: Composable reward system
b27a5b7 Phase 2: Enemy subtypes
5ed57fe Patch: Judgment/heal/HP fixes
832e7c6 Phase 1: Core environment
22712d1 Initial commit
```

---

## 14. Constants Reference

```python
MAX_HP = 1200           # Agent HP
ENEMY_HP = 1000         # Enemy HP
MAX_TURNS = 25
ADAPT_INCREASE = 40     # Resistance gain on adapt
ADAPT_DECREASE = 20     # Resistance loss on others
RESISTANCE_MAX = 80
JUDGMENT_BASE_DAMAGE = 100
JUDGMENT_BURST_DAMAGE = 350
HEAL_AMOUNT = 300
HEAL_COOLDOWN = 3
ARMOR_BYPASS_RATIO = 0.2  # PIERCE effect
PHASE_1_END = 5
PHASE_2_END = 15
PHASE_2_DEVIATION = 0.15
```

---

*This report is a complete knowledge transfer document. A new engineer or AI model should be able to understand, modify, and extend the system using only this document and the source code.*
