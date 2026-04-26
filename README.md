---
title: "Mahoraga — Adaptive Combat RL Environment"
emoji: ⚔️
colorFrom: red
colorTo: gray
sdk: docker
app_port: 7860
tags:
  - reinforcement-learning
  - openenv
  - llm-agent
  - adaptive-ai
  - grpo
  - unsloth
  - trl
---

<div align="center">

<img src="docs/mahoraga_wheel.svg" alt="Mahoraga Wheel" width="200"/>

# ⚔️ DIVINE GENERAL MAHORAGA

### A boss that learns how you fight. Then makes sure it never works again.

<br>

**Meta OpenEnv Hackathon 2026** · OpenEnv + TRL + Unsloth

[![Adapts](https://img.shields.io/badge/Adapts_to-Everything-crimson?style=for-the-badge)]()
[![Reward](https://img.shields.io/badge/Avg_Reward-18.55-blue?style=for-the-badge)]()
[![Survived](https://img.shields.io/badge/Players_Who_Survived-Good_Luck-black?style=for-the-badge)]()

📓 [**Training Notebook**](https://www.kaggle.com/code/atishay9828/meta-mahoraga/edit) · 🤗 [**Live Demo**](https://huggingface.co/spaces/MridulNegi2005/Project-Mahoraga) · 🏠 [**GitHub**](https://github.com/MridulNegi2005/Project_Mahoraga)

</div>

---

## 🎮 Let's Be Honest — Boss Fights Are Broken

Every game. Every RPG. Every "epic final boss."

You die once. You learn the pattern. You spam the same combo. Boss dead. GG.

**Dodge → Hit → Dodge → Hit → Dodge → Hit.**

That's not strategy. That's muscle memory with extra steps. The boss doesn't learn. The boss doesn't care that you've been spamming the same fire spell for the last 12 turns. It just stands there and takes it.

We've been fighting NPCs that are *literally designed to lose.*

---

**Now imagine a boss that watches you.**

Every move you make? Noted. Every attack you spam? Countered. You found a winning strategy? Congrats — it worked once. Try it again and you'll hit a wall of resistance so thick your damage might as well be a gentle breeze.

**That's Mahoraga.**

Straight from the Jujutsu Kaisen universe — the shikigami that *nobody has ever tamed.* Not because it's the strongest. Because it **adapts to anything you throw at it.**

You slash it? It builds resistance to slashing.
You blast it with cursed energy? It learns to tank that too.
You try the same thing twice? That's cute. It already adapted.

We took that concept and turned it into a real, trainable RL environment — powered by an LLM that actually *learns* to be this terrifying.

---

## ⚔️ How Mahoraga Hunts You

Mahoraga isn't a scripted boss. It's an LLM (Qwen 2.5 3B) fine-tuned through reinforcement learning to make tactical combat decisions in real time.

### The Resistance Engine

This is the core. This is what makes Mahoraga... *Mahoraga.*

Every time the agent observes your attack pattern, it builds resistance:

```
You attack PHYSICAL  →  Mahoraga adapts  →  +40% Physical Resistance
You attack PHYSICAL  →  Mahoraga adapts  →  +80% Physical Resistance (CAPPED)
Your PHYSICAL damage? Basically zero now.

You switch to CE?     →  Mahoraga's watching. It'll catch on.
```

Resistance isn't free, though. Building one defense weakens the others (−20% to non-adapted types). Mahoraga has to *choose* what to defend against — and if it reads you wrong, that's your opening.

**But here's the thing: it almost never reads you wrong anymore.**

### The Judgment Strike 💀

When Mahoraga has stacked enough correct adaptations, it unleashes **Judgment Strike** — a devastating burst that can deal **350 + 50 per stack** damage in a single turn.

The catch? Judgment Strike resets everything. All resistances. All stacks. Back to zero.

So Mahoraga has to decide: *Do I keep building defenses, or do I cash in right now for a massive hit?*

The trained model learned the answer. It waits. It stacks. It times. Then it deletes you in one move.

### The 3-Phase Escalation

Mahoraga doesn't start at full power. It *wakes up.*

| Phase | Turns | What You're Facing |
|-------|-------|-------------------|
| 🟢 **Awakening** | 1–5 | Predictable patterns. You think you've got this. |
| 🟡 **Reading** | 6–15 | Cycling attack types. 15% random deviation. It's testing you. |
| 🔴 **Hunting** | 16+ | It reads your weakest resistance and **targets it directly.** |

By Phase 3, Mahoraga isn't reacting anymore. It's *predicting.* It looks at your defenses, finds the gap, and exploits it. Every. Single. Turn.

---

## 🧠 What Mahoraga Learned (On Its Own)

We didn't program a strategy. We didn't hardcode "adapt then strike." We gave it a reward signal and an environment that punishes repetition.

Here's what emerged:

### Early Training: A Confused Shikigami

Iteration 1 Mahoraga is... sad. It picks random actions. It heals when it's at full HP. It attacks without building stacks. It dies to its own inefficiency.

**Avg reward: −10.47. Didn't win a single fight.**

### Late Training: The Divine General Awakens

By iteration 5, Mahoraga independently discovered an optimal combat loop:

```
👁️  OBSERVE  → Read the incoming attack type
🛡️  ADAPT    → Build resistance to exactly that category
⚡  STACK    → Accumulate adaptation bonuses
⚔️  STRIKE   → Judgment Strike at peak damage
🔄  RESET    → Switch stance, never repeat, keep hunting
```

It stopped spamming. It stopped healing unnecessarily. It started *reading the fight* and making decisions based on what would maximize damage output per turn.

**This wasn't coded. This was learned.**

The agent went from a mindless attacker to a calculated predator — adapting, timing, and striking with surgical precision. In just 5 training iterations.

---

## 📈 The Glow-Up: From Punching Bag to Final Boss

Training: 5 iterations of reward-weighted SFT on Qwen 2.5 3B (LoRA, Kaggle T4 GPU).

### Training Metrics — The Full Picture

<div align="center">
<img src="docs/training_metrics.png" alt="Training Metrics — Reward, Win Rate, Adaptation, Attacks" width="750"/>
</div>

<br>

**28-point reward swing.** Win rate 0% → undefeated. Attacks per episode cut in half. Every chart tells the same story: Mahoraga went from clueless to lethal.

### Final Boss Performance (10-Episode Eval)

| Episode | Reward | Result | Attacks Used | Adaptation Rate |
|---------|--------|--------|-------------|-----------------|
| 1 | 13.48 | ✅ Won | 7 | 22.2% |
| 2 | 19.86 | ✅ Won | 4 | 33.3% |
| 3 | 19.07 | ✅ Won | 4 | 42.9% |
| 4 | 19.07 | ✅ Won | 4 | 42.9% |
| 5 | 19.86 | ✅ Won | 4 | 33.3% |
| 6 | 19.77 | ✅ Won | 4 | 33.3% |
| 7 | 14.88 | ✅ Won | 7 | 12.5% |
| 8 | 19.86 | ✅ Won | 4 | 33.3% |
| 9 | 19.86 | ✅ Won | 4 | 33.3% |
| 10 | 19.77 | ✅ Won | 4 | 33.3% |

**10/10 wins. 80% of fights ended in just 4 moves.**

Look at episodes 2–6 and 8–10. Same pattern. Same efficiency. Same ruthless execution. Mahoraga found the optimal loop and locked in.

### The Before & After

| | 💀 Untrained | ⚔️ Trained |
|---|---|---|
| **Reward** | −10.47 | **+18.55** |
| **Win Rate** | 0% | **Undefeated** |
| **Attacks to Win** | ~9 (still lost) | **4** |
| **Adaptation Accuracy** | 0% | **33–43%** |
| **Healing Spam** | Constant | **Zero** |

That "Attacks to Win" drop is the real story. The untrained model threw 9 attacks and still lost. The trained model needs 4 and it's done. That's not incremental improvement — that's a fundamentally different strategy.

---

## 💡 Why Should You Care?

Mahoraga isn't just an anime-inspired boss fight (though it absolutely is that too).

It's a proof of concept for **adaptive RL agents** — LLMs that change their behavior when the environment changes around them.

### The Real Problem

Most LLM agents are one-trick ponies. They find what works and repeat it. That's fine when the world is static.

But the world isn't static:
- **Negotiation opponents** change their strategy mid-conversation
- **Code environments** evolve — yesterday's fix is today's bug
- **Patients** respond differently to treatment over time
- **Markets** punish anyone who keeps running the same playbook

Mahoraga proves that an LLM can learn to **stop repeating itself** when repetition gets punished. That's a small mechanic with massive implications.

### What We Actually Proved

| Claim | Evidence |
|-------|----------|
| LLMs can learn adaptive sequential behavior through RL | 0% → Undefeated win rate in 5 iterations |
| Emergent strategy arises without explicit programming | Agent independently discovered adapt→stack→strike loop |
| Environment-based rewards outperform static reward models | 7 composable reward functions, each preventing a specific exploit |
| Resistance mechanics force genuine adaptation | Repeating strategies reduces damage to near-zero |

---

## 🏗️ Under the Hood (Quick)

```
┌──────────┐     ┌───────────────┐     ┌──────────────┐
│  OpenEnv  │────▶│   Mahoraga    │────▶│  Qwen 2.5 3B │
│           │     │   Environment │     │  LoRA / 4-bit │
└──────────┘     └───────────────┘     └──────────────┘
                        │
            ┌───────────┼───────────┐
            ▼           ▼           ▼
      7 Reward     3-Phase      Resistance
      Functions    Curriculum   Engine
```

| Stack | Why |
|-------|-----|
| **OpenEnv** | Universal RL environment framework (reset / step / state) |
| **TRL** | Training loop — reward-weighted SFT, GRPO-style |
| **Unsloth** | 4-bit quantization, fast inference on a single T4 |
| **Qwen 2.5 3B** | Base LLM — LoRA fine-tuned (r=16, targets q/k/v/o) |

**7 reward functions** work together: survival, combat, adaptation, anti-cowardice, efficiency, terminal, and opportunity. Each one exists because the agent found an exploit without it.

---

## 🎮 Face Mahoraga Yourself

### Interactive Dashboard

```bash
# Terminal 1 — Wake the boss
python api.py                         # FastAPI → localhost:8000

# Terminal 2 — Enter the arena
cd frontend && npm install && npm run dev   # React → localhost:5173
```

### Gradio (Lightweight)

```bash
python app.py                         # Gradio → localhost:7860
```

### Train Your Own Mahoraga (Kaggle)

```bash
# Upload notebooks/meta-mahoraga.ipynb → Kaggle → Enable T4 GPU → Run all
# Watch it go from punching bag to Divine General in ~30 minutes
```

### Quick Test

```bash
git clone https://github.com/Atishay9828/meta_Mahoraga
cd meta_Mahoraga && pip install -r requirements.txt
python main.py                        # Watch a random agent get destroyed
```

---

## 📂 What's Inside

```
meta_Mahoraga/
├── env/
│   ├── mahoraga_env.py      # The arena — turn-based RL environment
│   ├── enemy.py             # 3-phase curriculum boss AI
│   ├── mechanics.py         # Resistance engine + damage math
│   ├── rewards.py           # 7 composable reward functions
│   └── gym_wrapper.py       # Gymnasium-compatible interface
├── notebooks/
│   └── meta-mahoraga.ipynb  # Full training pipeline (Kaggle-ready)
├── frontend/                # React tactical dashboard
├── api.py                   # FastAPI + LLM inference server
├── app.py                   # Gradio interactive UI
└── main.py                  # CLI arena
```

---

<div align="center">

<br>

**Meta OpenEnv Hackathon 2026**

*"The more it is hit, the more it adapts. That is the nature of Mahoraga."*

**Team BANGERS** · [Atishay](https://github.com/Atishay9828) & [Mridul](https://github.com/MridulNegi2005)

📓 [Training Notebook](https://www.kaggle.com/code/atishay9828/meta-mahoraga/edit) · 🤗 [Live Demo](https://huggingface.co/spaces/MridulNegi2005/Project-Mahoraga)

<br>

⚔️

</div>