# %% [markdown]
# # Project Mahoraga — RL Training (v4: Curriculum Boss Fight)
# Qwen 2.5 7B + LoRA + Adaptive Boss Environment
#
# **v4 CHANGES**:
# - Upgraded to Qwen 2.5 7B for stronger reasoning
# - Curriculum training: Easy → Medium → Hard with confidence gates
# - Auto-resume from latest Drive checkpoint
# - Clean logging (results every N iterations)
# - Frequent checkpoints to Google Drive

# %% CELL 1 — Install dependencies + suppress warnings
import os
os.environ["TRANSFORMERS_VERBOSITY"] = "error"
os.environ["TOKENIZERS_PARALLELISM"] = "false"
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", message=".*max_new_tokens.*")
warnings.filterwarnings("ignore", message=".*max_length.*")
warnings.filterwarnings("ignore", message=".*attention mask.*")
warnings.filterwarnings("ignore", message=".*use_return_dict.*")

import subprocess
subprocess.run(["pip", "install", "-q", "unsloth", "transformers", "accelerate",
                "peft", "trl", "bitsandbytes", "datasets", "torch", "matplotlib"], check=True)

import unsloth

import logging
logging.getLogger("transformers").setLevel(logging.ERROR)
logging.getLogger("transformers.generation").setLevel(logging.ERROR)

# %% CELL 2 — Mount Google Drive and setup
import os
import sys
import json
import glob
import time
import random
import shutil
from google.colab import drive

drive.mount('/content/drive')

DRIVE_DIR = "/content/drive/MyDrive/Mahoraga"
CHECKPOINT_DIR = os.path.join(DRIVE_DIR, "checkpoints")
STATS_PATH = os.path.join(DRIVE_DIR, "training_stats.json")
CURRICULUM_PATH = os.path.join(DRIVE_DIR, "curriculum_state.json")
os.makedirs(CHECKPOINT_DIR, exist_ok=True)

# Clone repo
if not os.path.exists('/content/meta_Mahoraga'):
    import subprocess
    subprocess.run(["git", "clone", "--branch", "main",
                    "https://github.com/Atishay9828/meta_Mahoraga.git",
                    "/content/meta_Mahoraga"], check=True)
sys.path.insert(0, '/content/meta_Mahoraga')

print(f"Drive dir: {DRIVE_DIR}")

# %% CELL 3 — Import environment and verify
from env.mahoraga_env import MahoragaEnv

env = MahoragaEnv(debug=False)
state = env.reset()
state, reward, done, info = env.step(0)

assert reward != 0.0, "Reward is 0!"
assert "reward_breakdown" in info, "reward_breakdown missing!"
assert "damage_dealt" in info["reward_breakdown"], "damage_dealt missing!"
assert "boss_resistances" in info, "boss_resistances missing!"

state2, _, _, info2 = env.step(0)
assert info2["adapted"], "Boss should adapt after 2 same-type hits!"

print("✅ Environment v2 verified. Boss adapts passively.")

# %% CELL 4 — Auto-resume: find latest checkpoint
def find_latest_checkpoint():
    """Scan Drive for the most recent saved model checkpoint."""
    # Priority 1: curriculum milestone models (easy_best, medium_best, etc.)
    for name in ["hard_best", "medium_best", "easy_best"]:
        path = os.path.join(CHECKPOINT_DIR, name)
        if os.path.exists(path) and os.path.isdir(path):
            print(f"📂 Found milestone checkpoint: {name}")
            return path, name

    # Priority 2: iteration checkpoints (latest by number)
    pattern = os.path.join(CHECKPOINT_DIR, "iter_*")
    checkpoints = [p for p in glob.glob(pattern) if os.path.exists(os.path.join(p, "adapter_config.json"))]
    if checkpoints:
        latest = sorted(checkpoints, key=lambda x: int(os.path.basename(x).split('_')[1]))[-1]
        name = os.path.basename(latest)
        print(f"📂 Found iteration checkpoint: {name}")
        return latest, name

    # Priority 3: final model from previous run
    final_path = os.path.join(DRIVE_DIR, "mahoraga_lora_final")
    if os.path.exists(final_path):
        print(f"📂 Found final model from previous run")
        return final_path, "lora_final"

    print("🆕 No checkpoint found. Starting fresh.")
    return None, None

RESUME_PATH, RESUME_NAME = find_latest_checkpoint()

# %% CELL 5 — Load model (Qwen 2.5 3B + LoRA)
from unsloth import FastLanguageModel
import torch

if RESUME_PATH:
    print(f"🔄 Resuming from: {RESUME_NAME}")
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=RESUME_PATH,
        max_seq_length=512,
        dtype=None,
        load_in_4bit=True,
    )
else:
    print("🆕 Loading base model: Qwen 2.5 3B")
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name="unsloth/Qwen2.5-3B-Instruct",
        max_seq_length=512,
        dtype=None,
        load_in_4bit=True,
    )

    model = FastLanguageModel.get_peft_model(
        model,
        r=16,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
        lora_alpha=16,
        lora_dropout=0,
        bias="none",
        use_gradient_checkpointing="unsloth",
    )

model.print_trainable_parameters()

# %% CELL 6 — Prompt builder
ACTION_NAMES = {
    0: "Physical Strike",
    1: "CE Blast",
    2: "Technique Strike",
    3: "Domain Expansion",
    4: "Reversed Cursed Technique",
    None: "(Wasted Turn)"
}

SYSTEM_MSG = "You are a combat AI fighting an adaptive boss. Respond with ONLY a single integer 0-4."

def build_prompt(state):
    """Build instruction prompt for the player (sorcerer) fighting Mahoraga."""
    boss_res = state.get("boss_resistances", {"PHYSICAL": 0, "CE": 0, "TECHNIQUE": 0})
    history = state.get("attack_history", [])
    crit_stack = state.get("crit_stack", 0)
    domain_used = state.get("domain_used", False)
    domain_active = state.get("domain_active", False)
    heal_cd = state.get("heal_cooldown", 0)
    wheel_turns = state.get("boss_wheel_turns", 0)

    history_str = " → ".join(history) if len(history) >= 2 else "Not enough data yet"

    highest_key = max(boss_res, key=boss_res.get)
    highest_val = boss_res[highest_key]

    domain_str = "ACTIVE (+50% DMG)" if domain_active else ("USED" if domain_used else "AVAILABLE")
    heal_str = f"COOLDOWN ({heal_cd} turns)" if heal_cd > 0 else "READY"

    prompt = f"""You are a sorcerer fighting Mahoraga, an adaptive boss that passively gains resistance to attack types you repeat.

Current State:
- Your HP: {state.get('player_hp', state.get('agent_hp', 0))}
- Mahoraga HP: {state.get('boss_hp', state.get('enemy_hp', 0))}
- Mahoraga Resistances: Physical={boss_res['PHYSICAL']}%, CE={boss_res['CE']}%, Technique={boss_res['TECHNIQUE']}%
- Mahoraga Wheel Turns: {wheel_turns} (more = stronger boss attacks)
- Last Boss Attack: {state.get('last_boss_attack', 'None')}
- Turn: {state['turn_number']}/30

Your Status:
- Crit Stack: {crit_stack}/3 (3 = next same-type hit does 1.5x)
- Domain Expansion: {domain_str}
- Heal: {heal_str}

Your Attack History: {history_str}

⚠️ Mahoraga's Highest Resistance: {highest_key} ({highest_val}%) — AVOID this type!

Available Actions:
0 = Physical Strike (120 base dmg, reduced by boss Physical resistance)
1 = CE Blast (150 base dmg, 15% chance for BLACK FLASH = 2.5x dmg!)
2 = Technique Strike (220 base dmg, highest risk/reward)
3 = Domain Expansion (ONCE per fight: resets boss resistances, +50% dmg for 3 turns)
4 = Reversed Cursed Technique (heal 250 HP, 4-turn cooldown)

STRATEGY GUIDE:
1. VARY your attacks — if you spam one type, Mahoraga adapts and becomes resistant
2. Use CE attacks for chance of Black Flash (2.5x damage!)
3. Save Domain Expansion for when Mahoraga has high resistances
4. Kill Mahoraga FAST — the longer the fight, the stronger it gets
5. Heal ONLY when HP is critically low

Choose the best action. Return ONLY a single integer (0-4)."""

    return prompt

# %% CELL 7 — Output parser
import re

def parse_action(text):
    """Extract integer action 0-4 from model output. Fallback to 0."""
    text = text.strip()
    if text in ['0', '1', '2', '3', '4']:
        return int(text)
    match = re.search(r'[0-4]', text)
    if match:
        return int(match.group())
    return 0

# %% CELL 8 — Rollout (silent by default)
def run_episode(model, tokenizer, env, max_turns=30):
    """Run one episode. Returns trajectory, total_reward, stats dict."""
    state = env.reset()
    trajectory = []
    total_reward = 0.0
    bf_count = 0
    domain_used = False
    total_steps = 0

    FastLanguageModel.for_inference(model)

    for turn in range(max_turns):
        prompt = build_prompt(state)

        messages = [
            {"role": "system", "content": SYSTEM_MSG},
            {"role": "user", "content": prompt}
        ]

        input_text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        inputs = tokenizer(input_text, return_tensors="pt").to(model.device)

        with torch.no_grad():
            import transformers
            transformers.logging.set_verbosity_error()
            outputs = model.generate(
                **inputs,
                max_new_tokens=8,
                max_length=None,
                temperature=0.7,
                do_sample=True,
                pad_token_id=tokenizer.eos_token_id
            )

        response = tokenizer.decode(outputs[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True)
        action = parse_action(response)

        next_state, reward, done, info = env.step(action)
        total_steps += 1

        if info.get("black_flash", False):
            bf_count += 1
        if info.get("domain_activated", False):
            domain_used = True

        trajectory.append({
            "prompt": prompt,
            "response": str(action),
            "action": action,
            "reward": reward,
            "state": state,
            "info": info
        })

        total_reward += reward
        state = next_state
        if done:
            break

    won = state.get("boss_hp", state.get("enemy_hp", 1)) <= 0

    return trajectory, total_reward, {
        "steps": total_steps,
        "black_flash_count": bf_count,
        "domain_used": domain_used,
        "won": won
    }

# %% CELL 9 — Expert trajectory seeding (difficulty = opponent behavior)

def _pick_expert_action(difficulty, turn, state, cycle_idx, domain_used, env):
    """Pick opponent action based on difficulty.
    easy=repeat, medium=cycle, hard=random."""
    player_hp = state.get("player_hp", state.get("agent_hp", 0))

    if player_hp < 350 and env.heal_cooldown_counter == 0:
        return 4, cycle_idx, domain_used

    if not domain_used and turn >= 8 and difficulty != "easy":
        boss_res = state.get("boss_resistances", {})
        if sum(1 for v in boss_res.values() if v >= 30) >= 1:
            return 3, cycle_idx, True

    if difficulty == "easy":
        action = 0 if random.random() > 0.05 else random.choice([0, 1, 2])
        return action, cycle_idx, domain_used
    elif difficulty == "medium":
        if random.random() < 0.15:
            action = random.choice([0, 1, 2])
        else:
            action = [0, 1, 2][cycle_idx % 3]
            cycle_idx += 1
        return action, cycle_idx, domain_used
    else:
        if random.random() < 0.85:
            action = random.choice([0, 1, 2])
        else:
            boss_res = state.get("boss_resistances", {"PHYSICAL": 0, "CE": 0, "TECHNIQUE": 0})
            weakest = min(boss_res, key=boss_res.get)
            action = {"PHYSICAL": 0, "CE": 1, "TECHNIQUE": 2}[weakest]
        return action, cycle_idx, domain_used


def generate_expert_trajectories(difficulty, num=4):
    """Generate expert trajectories for a specific difficulty."""
    trajs = []
    for _ in range(num):
        env = MahoragaEnv(difficulty=difficulty)
        state = env.reset()
        traj = []
        total_reward = 0.0
        cycle_idx = 0
        domain_used = False

        for turn in range(30):
            action, cycle_idx, domain_used = _pick_expert_action(
                difficulty, turn, state, cycle_idx, domain_used, env
            )
            prompt = build_prompt(state)
            next_state, reward, done, info = env.step(action)
            traj.append({
                "prompt": prompt, "response": str(action),
                "action": action, "reward": reward,
                "state": state, "info": info
            })
            total_reward += reward
            state = next_state
            if done:
                break

        trajs.append(traj)
    return trajs

# %% CELL 10 — Dataset builder
from datasets import Dataset

def prepare_weighted_dataset(trajectories, tokenizer, expert_trajs=None):
    """Create reward-weighted SFT dataset."""
    records = []

    for traj in trajectories:
        last_state = traj[-1]["state"]
        episode_won = last_state.get("boss_hp", last_state.get("enemy_hp", 1)) <= 0
        mult = 2.0 if episode_won else 0.5

        for step in traj:
            adjusted_r = step["reward"] * mult
            if adjusted_r > 2.0:
                copies = 3
            elif adjusted_r > 0.5:
                copies = 2
            elif adjusted_r > -2.0:
                copies = 1
            else:
                continue

            if step["action"] == 3 and step["reward"] > 0:
                copies += 1

            text = tokenizer.apply_chat_template(
                [{"role": "system", "content": SYSTEM_MSG},
                 {"role": "user", "content": step["prompt"]},
                 {"role": "assistant", "content": step["response"]}],
                tokenize=False
            )
            for _ in range(copies):
                records.append({"text": text, "action": step["action"]})

    if expert_trajs:
        for traj in expert_trajs:
            for step in traj:
                text = tokenizer.apply_chat_template(
                    [{"role": "system", "content": SYSTEM_MSG},
                     {"role": "user", "content": step["prompt"]},
                     {"role": "assistant", "content": step["response"]}],
                    tokenize=False
                )
                for _ in range(2):
                    records.append({"text": text, "action": step["action"]})

    # Balance: cap any single action type at 60%
    from collections import Counter
    action_counts = Counter(r["action"] for r in records)
    max_per_action = int(len(records) * 0.6)
    for action_id, count in action_counts.items():
        if count > max_per_action:
            action_records = [r for r in records if r["action"] == action_id]
            other_records = [r for r in records if r["action"] != action_id]
            random.shuffle(action_records)
            records = other_records + action_records[:max_per_action]

    final = [{"text": r["text"]} for r in records]
    random.shuffle(final)
    return Dataset.from_list(final) if final else None


# %% CELL 11 — Checkpoint & curriculum helpers

def save_checkpoint(model, tokenizer, name, stats=None):
    """Save model + stats to Drive."""
    path = os.path.join(CHECKPOINT_DIR, name)
    os.makedirs(path, exist_ok=True)
    model.save_pretrained(path)
    tokenizer.save_pretrained(path)
    if stats:
        with open(os.path.join(path, "stats.json"), "w") as f:
            json.dump(stats, f, indent=2)


def save_curriculum_state(state):
    """Persist curriculum progress to Drive."""
    with open(CURRICULUM_PATH, "w") as f:
        json.dump(state, f, indent=2)


def load_curriculum_state():
    """Load curriculum progress from Drive."""
    if os.path.exists(CURRICULUM_PATH):
        with open(CURRICULUM_PATH) as f:
            return json.load(f)
    return {"current_difficulty": "easy", "easy_done": False,
            "medium_done": False, "hard_done": False,
            "total_iterations": 0, "all_stats": []}


def evaluate_model(model, tokenizer, difficulty, num_episodes=10):
    """Run evaluation episodes. Returns win_rate, avg_reward, stats list."""
    results = []
    for _ in range(num_episodes):
        env = MahoragaEnv(difficulty=difficulty)
        _, ep_reward, ep_stats = run_episode(model, tokenizer, env)
        results.append({"reward": ep_reward, "won": ep_stats["won"],
                         "steps": ep_stats["steps"],
                         "bf": ep_stats["black_flash_count"],
                         "domain": ep_stats["domain_used"]})
    wins = sum(1 for r in results if r["won"])
    avg_r = sum(r["reward"] for r in results) / len(results)
    return wins / len(results), avg_r, results


# %% CELL 12 — Curriculum Training Loop
# ═══════════════════════════════════════════════════════════
#   Easy → (>= 60% win rate) → Medium → (>= 40% win rate) → Hard
#   Checkpoints every 5 iterations. Milestone saves on promotion.
#   Auto-resumes from curriculum_state.json.
# ═══════════════════════════════════════════════════════════

from trl import SFTTrainer, SFTConfig

FastLanguageModel.for_training(model)

# --- Configuration ---
EPISODES_PER_ITER = 15           # Episodes per training iteration
LOG_EVERY = 5                    # Print progress every N iterations
CHECKPOINT_EVERY = 5             # Save checkpoint every N iterations
MAX_ITERS_PER_DIFFICULTY = 50    # Safety cap per difficulty
EVAL_EPISODES = 10               # Episodes for confidence evaluation

# Confidence thresholds (win rate to graduate)
CONFIDENCE = {"easy": 0.60, "medium": 0.40, "hard": 0.30}

# --- Load curriculum progress ---
curriculum = load_curriculum_state()
current_difficulty = curriculum["current_difficulty"]
total_iters = curriculum["total_iterations"]
all_stats = curriculum["all_stats"]

print(f"\n{'='*60}")
print(f"  CURRICULUM TRAINING — Starting at: {current_difficulty.upper()}")
print(f"  Resuming from iteration {total_iters}")
print(f"{'='*60}\n")

for difficulty in ["easy", "medium", "hard"]:
    if curriculum.get(f"{difficulty}_done", False):
        print(f"  ✅ {difficulty.upper()} already completed. Skipping.")
        continue
    if difficulty != current_difficulty and not curriculum.get(f"{current_difficulty}_done", False):
        continue

    current_difficulty = difficulty
    print(f"\n{'━'*60}")
    print(f"  🎮 PHASE: {difficulty.upper()}")
    pattern_name = {"easy": "repeat", "medium": "cycle", "hard": "random"}[difficulty]
    print(f"  Opponent pattern: {pattern_name}")
    print(f"  Win rate needed: {CONFIDENCE[difficulty]:.0%}")
    print(f"{'━'*60}")

    # Generate expert trajectories for this difficulty
    expert_trajs = generate_expert_trajectories(difficulty, num=6)
    consecutive_confident = 0
    
    # Calculate how many iterations we already did for this difficulty
    difficulty_iter = sum(1 for s in all_stats if s["difficulty"] == difficulty)
    remaining_iters = max(1, MAX_ITERS_PER_DIFFICULTY - difficulty_iter)

    for local_iter in range(remaining_iters):
        total_iters += 1
        difficulty_iter += 1

        # --- Collect episodes ---
        trajectories = []
        iter_rewards = []
        iter_wins = 0
        iter_bf = 0

        for ep in range(EPISODES_PER_ITER):
            env_train = MahoragaEnv(difficulty=difficulty)
            traj, ep_reward, ep_stats = run_episode(model, tokenizer, env_train)
            trajectories.append(traj)
            iter_rewards.append(ep_reward)
            if ep_stats["won"]:
                iter_wins += 1
            iter_bf += ep_stats["black_flash_count"]

        avg_reward = sum(iter_rewards) / len(iter_rewards)
        win_rate = iter_wins / EPISODES_PER_ITER
        avg_steps = sum(len(t) for t in trajectories) / len(trajectories)

        stats = {
            "iter": total_iters, "difficulty": difficulty,
            "avg_reward": round(avg_reward, 3),
            "win_rate": round(win_rate, 3),
            "avg_steps": round(avg_steps, 1),
            "black_flashes": iter_bf,
            "min_r": round(min(iter_rewards), 2),
            "max_r": round(max(iter_rewards), 2),
        }
        all_stats.append(stats)

        # --- Log progress ---
        if difficulty_iter % LOG_EVERY == 0 or difficulty_iter == 1:
            print(f"  [{difficulty.upper():6s} iter {difficulty_iter:3d}]  "
                  f"win={win_rate:5.0%}  reward={avg_reward:+6.2f}  "
                  f"steps={avg_steps:4.1f}  BF={iter_bf}  "
                  f"range=[{min(iter_rewards):+.1f}, {max(iter_rewards):+.1f}]")

        # --- Build dataset & train ---
        inject = expert_trajs if win_rate < 0.3 else expert_trajs[:2]
        train_dataset = prepare_weighted_dataset(trajectories, tokenizer, inject)

        if train_dataset and len(train_dataset) > 0:
            FastLanguageModel.for_training(model)

            trainer = SFTTrainer(
                model=model,
                tokenizer=tokenizer,
                train_dataset=train_dataset,
                args=SFTConfig(
                    output_dir="/tmp/mahoraga_trainer_output",
                    per_device_train_batch_size=4,
                    gradient_accumulation_steps=2,
                    num_train_epochs=1,
                    learning_rate=2e-5,
                    warmup_steps=5,
                    logging_steps=9999,  # Suppress HF trainer logs
                    fp16=not torch.cuda.is_bf16_supported(),
                    bf16=torch.cuda.is_bf16_supported(),
                    max_seq_length=512,
                    dataset_text_field="text",
                    save_strategy="no",
                    report_to="none",
                ),
            )
            trainer.train()

        # --- Periodic checkpoint ---
        if difficulty_iter % CHECKPOINT_EVERY == 0:
            save_checkpoint(model, tokenizer, f"iter_{total_iters}", stats)

        # --- Save curriculum progress (crash recovery) ---
        curriculum["current_difficulty"] = difficulty
        curriculum["total_iterations"] = total_iters
        curriculum["all_stats"] = all_stats
        save_curriculum_state(curriculum)

        # --- Confidence check ---
        if win_rate >= CONFIDENCE[difficulty]:
            consecutive_confident += 1
        else:
            consecutive_confident = 0

        # Need 3 consecutive confident iterations to graduate
        if consecutive_confident >= 3:
            # Run formal evaluation to confirm
            print(f"\n  🔍 Evaluating {difficulty.upper()} confidence ({EVAL_EPISODES} eps)...")
            eval_wr, eval_ar, _ = evaluate_model(model, tokenizer, difficulty, EVAL_EPISODES)
            print(f"     Eval: win_rate={eval_wr:.0%}, avg_reward={eval_ar:+.2f}")

            if eval_wr >= CONFIDENCE[difficulty]:
                print(f"  🏆 {difficulty.upper()} MASTERED! Saving milestone...")
                save_checkpoint(model, tokenizer, f"{difficulty}_best", {
                    "difficulty": difficulty, "win_rate": eval_wr,
                    "avg_reward": eval_ar, "iterations": difficulty_iter
                })
                curriculum[f"{difficulty}_done"] = True
                save_curriculum_state(curriculum)
                break
            else:
                print(f"     Not confident enough. Continuing training...")
                consecutive_confident = 0

    else:
        # Hit MAX_ITERS — save what we have and move on
        print(f"  ⚠️ {difficulty.upper()}: Max iterations reached. Saving and moving on...")
        save_checkpoint(model, tokenizer, f"{difficulty}_best", stats)
        curriculum[f"{difficulty}_done"] = True
        save_curriculum_state(curriculum)

print(f"\n{'='*60}")
print(f"  ✅ CURRICULUM COMPLETE — {total_iters} total iterations")
print(f"{'='*60}")

# %% CELL 13 — Save final model
save_path = os.path.join(DRIVE_DIR, "mahoraga_lora_final")
model.save_pretrained(save_path)
tokenizer.save_pretrained(save_path)

with open(STATS_PATH, "w") as f:
    json.dump(all_stats, f, indent=2)

print(f"Final model saved: {save_path}")

# %% CELL 14 — Plot training progress
import matplotlib.pyplot as plt

def plot_training_progress(stats):
    """Plot reward and win rate across curriculum phases."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    colors = {"easy": "#81C784", "medium": "#FFB74D", "hard": "#E57373"}

    for diff in ["easy", "medium", "hard"]:
        phase = [s for s in stats if s["difficulty"] == diff]
        if not phase:
            continue
        iters = [s["iter"] for s in phase]
        rewards = [s["avg_reward"] for s in phase]
        wrs = [s["win_rate"] for s in phase]

        axes[0].plot(iters, rewards, 'o-', color=colors[diff], label=diff.upper(), markersize=4)
        axes[1].plot(iters, wrs, 's-', color=colors[diff], label=diff.upper(), markersize=4)

    axes[0].set_xlabel("Iteration")
    axes[0].set_ylabel("Avg Reward")
    axes[0].set_title("Reward Curve (by Difficulty Phase)")
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)
    axes[0].axhline(y=0, color='gray', linestyle='--', alpha=0.5)

    axes[1].set_xlabel("Iteration")
    axes[1].set_ylabel("Win Rate")
    axes[1].set_title("Win Rate (by Difficulty Phase)")
    axes[1].legend()
    axes[1].set_ylim(-0.05, 1.05)
    axes[1].grid(True, alpha=0.3)

    # Draw confidence thresholds
    for diff, thresh in CONFIDENCE.items():
        axes[1].axhline(y=thresh, color=colors[diff], linestyle=':', alpha=0.5)

    plt.tight_layout()
    plot_path = os.path.join(DRIVE_DIR, "training_progress.png")
    plt.savefig(plot_path, dpi=150, bbox_inches="tight")
    plt.show()
    print(f"Plot saved: {plot_path}")

plot_training_progress(all_stats)

# %% CELL 15 — Final evaluation across all difficulties
print("\n--- FINAL EVALUATION ---")
for difficulty in ["easy", "medium", "hard"]:
    wr, ar, results = evaluate_model(model, tokenizer, difficulty, 10)
    bf_total = sum(r["bf"] for r in results)
    domain_total = sum(1 for r in results if r["domain"])
    print(f"  {difficulty.upper():8s}: win={wr:5.0%}  reward={ar:+6.2f}  "
          f"BF={bf_total}  domains={domain_total}/10")

# %% CELL 16 — Export
merged_path = os.path.join(DRIVE_DIR, "mahoraga_merged_full")
model.save_pretrained_merged(merged_path, tokenizer, save_method="merged_16bit")

shutil.make_archive(os.path.join(DRIVE_DIR, "mahoraga_lora_weights"), "zip",
                    DRIVE_DIR, "mahoraga_lora_final")

print(f"\n📦 All saved to {DRIVE_DIR}:")
print("  1. mahoraga_lora_final/  — LoRA adapter")
print("  2. mahoraga_merged_full/ — Full model")
print("  3. checkpoints/         — All checkpoints + milestones")
print("  4. training_progress.png")
print("  5. training_stats.json")
print("  6. curriculum_state.json")
print("\n✅ Done. Safe on Drive.")
