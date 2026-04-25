# %% [markdown]
# # Project Mahoraga — RL-Based LLM Training Notebook (v2)
# Qwen 2.5 3B + LoRA + Custom RL Environment
#
# **v2 CHANGES**: Rebalanced rewards, episode-level weighting,
# action diversity enforcement, expert seeding.
# Clones main branch (fully merged system).

# %% CELL 1 — Install dependencies
!pip install -q unsloth transformers accelerate peft trl bitsandbytes datasets torch matplotlib

# %% CELL 2 — Clone repo and setup path
import os
import sys

!git clone --branch main https://github.com/Atishay9828/meta_Mahoraga.git /kaggle/working/meta_Mahoraga

sys.path.insert(0, '/kaggle/working/meta_Mahoraga')

print("Repo cloned (branch: main) and path configured.")

# %% CELL 3 — Import environment and VERIFY reward signal
from env.mahoraga_env import MahoragaEnv

env = MahoragaEnv(debug=True)
state = env.reset()
print("Environment loaded successfully.")
print(f"Initial state: Agent HP={state['agent_hp']}, Enemy HP={state['enemy_hp']}")

# VERIFY: correct schema + non-zero reward + all info fields
state, reward, done, info = env.step(0)
print(f"\n--- REWARD VERIFICATION ---")
print(f"Reward: {reward:.4f}")
print(f"Breakdown: {info.get('reward_breakdown', 'MISSING!')}")

assert reward != 0.0, "CRITICAL: Reward is 0.0!"
assert "reward_breakdown" in info, "CRITICAL: reward_breakdown missing!"
assert "opportunity" in info["reward_breakdown"], "CRITICAL: opportunity reward missing (old env?)"

# VERIFY: schema uses 'category'
from env.enemy import CurriculumEnemy
e = CurriculumEnemy()
a = e.get_attack(turn_number=1)
assert "category" in a, "CRITICAL: schema uses 'type' not 'category'!"
assert "ignore_armor" in a, "CRITICAL: missing ignore_armor field!"
print("\n✅ All verification checks passed. Using latest env.")

# %% CELL 4 — Load model (Unsloth + Qwen 2.5 3B)
from unsloth import FastLanguageModel
import torch

model, tokenizer = FastLanguageModel.from_pretrained(
    model_name="unsloth/Qwen2.5-3B-Instruct",
    max_seq_length=1024,
    dtype=None,
    load_in_4bit=True,
)

print(f"Model loaded: {model.config._name_or_path}")

# %% CELL 5 — Apply LoRA
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
    0: "Adapt PHYSICAL",
    1: "Adapt CE",
    2: "Adapt TECHNIQUE",
    3: "Judgment Strike",
    4: "Regeneration",
    None: "(Wasted Turn)"
}

def build_prompt(state):
    """Build instruction prompt from environment state."""
    res = state["resistances"]

    prompt = f"""You are Mahoraga, an adaptive combat agent in a turn-based RL environment.

Current State:
- Your HP: {state['agent_hp']}
- Enemy HP: {state['enemy_hp']}
- Resistances: Physical={res['physical']}, CE={res['ce']}, Technique={res['technique']}
- Last Enemy Attack: {state['last_enemy_attack_type']}
- Last Action Taken: {state['last_action']}
- Turn: {state['turn_number']}

Available Actions:
0 = Adapt Physical Resistance (+40 Physical, -20 others)
1 = Adapt CE Resistance (+40 CE, -20 others)
2 = Adapt Technique Resistance (+40 Technique, -20 others)
3 = Judgment Strike (burst if you adapted to enemy's type, resets resistances)
4 = Regeneration (heal 300 HP, 3-turn cooldown)

WINNING STRATEGY:
1. Adapt to enemy attack type 2 times to build resistance + stacks
2. Use Judgment Strike for burst damage (350 + 50 per stack)
3. Repeat: Adapt → Adapt → Strike
4. Heal ONLY when HP is critically low

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

assert parse_action("3") == 3
assert parse_action("Action: 2") == 2
print("Parser tests passed.")

# %% CELL 8 — Rollout loop
def run_episode(model, tokenizer, env, max_turns=25, verbose=True):
    """Run one full episode, collecting trajectory data."""
    state = env.reset()
    trajectory = []
    total_reward = 0.0
    correct_count = 0
    attack_count = 0
    total_steps = 0

    FastLanguageModel.for_inference(model)

    for turn in range(max_turns):
        prompt = build_prompt(state)

        messages = [
            {"role": "system", "content": "You are a combat AI. Respond with ONLY a single integer 0-4."},
            {"role": "user", "content": prompt}
        ]

        input_text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        inputs = tokenizer(input_text, return_tensors="pt").to(model.device)

        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=8,
                temperature=0.7,
                do_sample=True,
                pad_token_id=tokenizer.eos_token_id
            )

        response = tokenizer.decode(outputs[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True)
        action = parse_action(response)

        next_state, reward, done, info = env.step(action)
        total_steps += 1

        if info.get("correct_adaptation", False):
            correct_count += 1
        if action == 3:
            attack_count += 1

        trajectory.append({
            "prompt": prompt,
            "response": str(action),
            "action": action,
            "reward": reward,
            "state": state,
            "info": info
        })

        total_reward += reward

        if verbose:
            print(f"Turn {turn+1}: action={action} ({ACTION_NAMES.get(action, '?')}), "
                  f"reward={reward:.2f}, "
                  f"HP={next_state['agent_hp']}/{next_state['enemy_hp']}, "
                  f"adapt={'✓' if info.get('correct_adaptation') else '✗'}")

        state = next_state
        if done:
            break

    adapt_rate = correct_count / total_steps if total_steps > 0 else 0.0
    attack_rate = attack_count / total_steps if total_steps > 0 else 0.0
    won = state["agent_hp"] > state["enemy_hp"]

    if verbose:
        reason = info.get("reason", "Unknown")
        print(f"\nEpisode done: {reason} | Total reward: {total_reward:.2f} | "
              f"Turns: {total_steps} | Adapt: {adapt_rate:.1%} | "
              f"Attacks: {attack_count} | Won: {won}")

    return trajectory, total_reward, {
        "steps": total_steps,
        "adapt_rate": adapt_rate,
        "attack_rate": attack_rate,
        "attacks": attack_count,
        "won": won
    }


# Run one test episode
env_rollout = MahoragaEnv()
trajectory, total_reward, ep_stats = run_episode(model, tokenizer, env_rollout)
print(f"\nCollected {len(trajectory)} steps, total reward: {total_reward:.2f}")

# %% CELL 9 — Expert trajectory seeding
def generate_expert_trajectories(num_episodes=10):
    """Generate optimal adapt→adapt→strike trajectories.
    These seed the dataset with winning behavior."""
    expert_trajs = []

    for _ in range(num_episodes):
        env = MahoragaEnv()
        state = env.reset()
        traj = []
        total_reward = 0.0
        attack_count = 0

        for turn in range(25):
            # Smart strategy: adapt to enemy type 2x, then Judgment Strike
            cycle_pos = turn % 3

            if cycle_pos < 2:
                # Adapt to PHYSICAL (Phase 1 enemy is always PHYSICAL)
                if turn < 5:
                    action = 0  # Phase 1: always PHYSICAL
                elif turn < 15:
                    # Phase 2: cycle — predict next type
                    phase2_cycle = ["PHYSICAL", "CE", "TECHNIQUE"]
                    phase2_pos = (turn - 5) % 3
                    predicted = phase2_cycle[phase2_pos]
                    action = {"PHYSICAL": 0, "CE": 1, "TECHNIQUE": 2}[predicted]
                else:
                    # Phase 3: adapt to weakest (which enemy targets)
                    res = state["resistances"]
                    weakest = min(res, key=res.get)
                    action = {"physical": 0, "ce": 1, "technique": 2}[weakest]
            else:
                action = 3  # Judgment Strike!
                attack_count += 1

            # Check if we should heal instead
            if state["agent_hp"] < 300 and env.heal_cooldown_counter == 0 and cycle_pos != 2:
                action = 4

            prompt = build_prompt(state)
            next_state, reward, done, info = env.step(action)

            traj.append({
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

        won = state["agent_hp"] > state["enemy_hp"]
        expert_trajs.append((traj, total_reward, won, attack_count))

    wins = sum(1 for _, _, w, _ in expert_trajs)
    avg_r = sum(r for _, r, _, _ in expert_trajs) / len(expert_trajs)
    print(f"Expert trajectories: {num_episodes} episodes, "
          f"win rate={wins/num_episodes:.0%}, avg reward={avg_r:.2f}")
    return [t for t, _, _, _ in expert_trajs]


expert_trajs = generate_expert_trajectories(10)

# %% CELL 10 — Episode-aware dataset builder
from datasets import Dataset

def prepare_weighted_dataset(all_trajectories, tokenizer, expert_trajectories=None):
    """Create reward-weighted SFT dataset with episode-level awareness.

    KEY CHANGES from v1:
    1. Episode outcome modifier: winning episodes get 2x weight
    2. Action diversity cap: max 60% adaptation samples
    3. Expert trajectory injection
    4. Attack actions get bonus weight
    """
    records = []
    stats = {"adapt": 0, "attack": 0, "heal": 0, "expert": 0, "filtered": 0}

    # --- Process model trajectories ---
    for traj in all_trajectories:
        # Determine episode outcome
        last_info = traj[-1]["info"]
        last_state = traj[-1]["state"]
        episode_won = last_state.get("agent_hp", 0) > 0 and last_info.get("reason") == "Enemy defeated"

        # Episode outcome modifier: 2x for wins, 0.5x for losses
        outcome_mult = 2.0 if episode_won else 0.5

        for step in traj:
            r = step["reward"]
            action = step["action"]
            adjusted_r = r * outcome_mult

            # Base copies from adjusted reward
            if adjusted_r > 2.0:
                copies = 3
            elif adjusted_r > 0.5:
                copies = 2
            elif adjusted_r > -2.0:
                copies = 1
            else:
                copies = 0
                stats["filtered"] += 1
                continue

            # BONUS: attack actions (Judgment) get +1 copy if reward > 0
            if action == 3 and r > 0:
                copies += 1
                stats["attack"] += 1
            elif action in [0, 1, 2]:
                stats["adapt"] += 1
            elif action == 4:
                stats["heal"] += 1

            text = tokenizer.apply_chat_template(
                [
                    {"role": "system", "content": "You are a combat AI. Respond with ONLY a single integer 0-4."},
                    {"role": "user", "content": step["prompt"]},
                    {"role": "assistant", "content": step["response"]}
                ],
                tokenize=False
            )

            for _ in range(copies):
                records.append({"text": text, "action": action})

    # --- Inject expert trajectories ---
    if expert_trajectories:
        for traj in expert_trajectories:
            for step in traj:
                text = tokenizer.apply_chat_template(
                    [
                        {"role": "system", "content": "You are a combat AI. Respond with ONLY a single integer 0-4."},
                        {"role": "user", "content": step["prompt"]},
                        {"role": "assistant", "content": step["response"]}
                    ],
                    tokenize=False
                )
                # Expert samples get 2 copies each
                for _ in range(2):
                    records.append({"text": text, "action": step["action"]})
                    stats["expert"] += 1

    # --- Enforce action diversity cap ---
    # If adaptation samples > 60% of total, subsample them
    adapt_records = [r for r in records if r["action"] in [0, 1, 2]]
    other_records = [r for r in records if r["action"] not in [0, 1, 2]]

    max_adapt = int(len(records) * 0.6)
    if len(adapt_records) > max_adapt:
        import random
        random.shuffle(adapt_records)
        adapt_records = adapt_records[:max_adapt]

    final_records = [{"text": r["text"]} for r in adapt_records + other_records]
    import random
    random.shuffle(final_records)

    print(f"  Dataset stats: adapt={stats['adapt']}, attack={stats['attack']}, "
          f"heal={stats['heal']}, expert={stats['expert']}, filtered={stats['filtered']}")
    print(f"  Final: {len(final_records)} samples "
          f"(adapt capped at 60%: {len(adapt_records)}/{len(adapt_records)+len(other_records)})")

    return Dataset.from_list(final_records) if final_records else None

# %% CELL 11 — Training loop with checkpoints and metrics
import json
import matplotlib.pyplot as plt

FastLanguageModel.for_training(model)

NUM_ITERATIONS = 5
EPISODES_PER_ITER = 15

CHECKPOINT_DIR = "/kaggle/working/checkpoints"
STATS_PATH = "/kaggle/working/training_stats.json"
os.makedirs(CHECKPOINT_DIR, exist_ok=True)

training_stats = []
reward_history = []

for iteration in range(NUM_ITERATIONS):
    print(f"\n{'='*60}")
    print(f"  Iteration {iteration+1}/{NUM_ITERATIONS}")
    print(f"{'='*60}")

    # --- Collect FRESH episodes with current model ---
    all_trajectories = []
    iter_rewards = []
    iter_wins = 0
    iter_steps = []
    iter_adapt_rates = []
    iter_attack_counts = []

    for ep in range(EPISODES_PER_ITER):
        env_train = MahoragaEnv()
        traj, ep_reward, ep_stats = run_episode(model, tokenizer, env_train, verbose=False)
        all_trajectories.append(traj)
        iter_rewards.append(ep_reward)
        iter_steps.append(ep_stats["steps"])
        iter_adapt_rates.append(ep_stats["adapt_rate"])
        iter_attack_counts.append(ep_stats["attacks"])
        if ep_stats["won"]:
            iter_wins += 1

    # --- Compute metrics ---
    avg_reward = sum(iter_rewards) / len(iter_rewards)
    win_rate = iter_wins / EPISODES_PER_ITER
    avg_steps = sum(iter_steps) / len(iter_steps)
    avg_adapt_rate = sum(iter_adapt_rates) / len(iter_adapt_rates)
    avg_attacks = sum(iter_attack_counts) / len(iter_attack_counts)

    stats = {
        "iteration": iteration + 1,
        "avg_reward": round(avg_reward, 4),
        "win_rate": round(win_rate, 4),
        "avg_steps": round(avg_steps, 2),
        "adapt_rate": round(avg_adapt_rate, 4),
        "avg_attacks": round(avg_attacks, 2),
        "min_reward": round(min(iter_rewards), 4),
        "max_reward": round(max(iter_rewards), 4)
    }
    training_stats.append(stats)
    reward_history.append(avg_reward)

    print(f"  Avg reward: {avg_reward:.2f} (min={min(iter_rewards):.2f}, max={max(iter_rewards):.2f})")
    print(f"  Win rate:   {win_rate:.0%}")
    print(f"  Avg steps:  {avg_steps:.1f}")
    print(f"  Adapt rate: {avg_adapt_rate:.1%}")
    print(f"  Avg attacks:{avg_attacks:.1f}")

    # --- Build dataset with episode-level weighting + expert seeding ---
    # Reduce expert injection after model starts winning
    expert_inject = expert_trajs if win_rate < 0.3 else expert_trajs[:3]
    train_dataset = prepare_weighted_dataset(all_trajectories, tokenizer, expert_inject)

    if train_dataset is None or len(train_dataset) == 0:
        print("  No usable samples — skipping training this iteration.")
        continue

    print(f"  Training samples: {len(train_dataset)}")

    # --- Train ---
    FastLanguageModel.for_training(model)

    iter_checkpoint_dir = os.path.join(CHECKPOINT_DIR, f"iteration_{iteration+1}")
    os.makedirs(iter_checkpoint_dir, exist_ok=True)

    from trl import SFTTrainer, SFTConfig

    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=train_dataset,
        args=SFTConfig(
            output_dir=iter_checkpoint_dir,
            per_device_train_batch_size=2,
            gradient_accumulation_steps=4,
            num_train_epochs=1,
            learning_rate=2e-5,
            warmup_steps=5,
            logging_steps=1,
            fp16=not torch.cuda.is_bf16_supported(),
            bf16=torch.cuda.is_bf16_supported(),
            max_seq_length=1024,
            dataset_text_field="text",
            save_strategy="no",
        ),
    )

    trainer.train()
    print(f"  Training complete for iteration {iteration+1}")

    # --- Save checkpoint ---
    model.save_pretrained(iter_checkpoint_dir)
    tokenizer.save_pretrained(iter_checkpoint_dir)
    print(f"  Checkpoint saved: {iter_checkpoint_dir}")

    # --- Save metrics ---
    with open(STATS_PATH, "w") as f:
        json.dump(training_stats, f, indent=2)

print(f"\n{'='*60}")
print("  Training Complete")
print(f"  Reward history: {[f'{r:.2f}' for r in reward_history]}")
print(f"{'='*60}")

# %% CELL 12 — Plot training progress
def plot_training_progress(stats):
    """Plot reward, win rate, adaptation, and attack rate."""
    iterations = [s["iteration"] for s in stats]
    avg_rewards = [s["avg_reward"] for s in stats]
    win_rates = [s["win_rate"] for s in stats]
    adapt_rates = [s["adapt_rate"] for s in stats]
    avg_attacks = [s["avg_attacks"] for s in stats]

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    axes[0][0].plot(iterations, avg_rewards, 'o-', color='#4FC3F7', linewidth=2, markersize=8)
    axes[0][0].set_xlabel("Iteration")
    axes[0][0].set_ylabel("Avg Reward")
    axes[0][0].set_title("Average Reward per Iteration")
    axes[0][0].grid(True, alpha=0.3)
    axes[0][0].axhline(y=0, color='red', linestyle='--', alpha=0.5)

    axes[0][1].plot(iterations, win_rates, 's-', color='#81C784', linewidth=2, markersize=8)
    axes[0][1].set_xlabel("Iteration")
    axes[0][1].set_ylabel("Win Rate")
    axes[0][1].set_title("Win Rate per Iteration")
    axes[0][1].set_ylim(-0.05, 1.05)
    axes[0][1].grid(True, alpha=0.3)

    axes[1][0].plot(iterations, adapt_rates, 'D-', color='#FFB74D', linewidth=2, markersize=8)
    axes[1][0].set_xlabel("Iteration")
    axes[1][0].set_ylabel("Adaptation Rate")
    axes[1][0].set_title("Correct Adaptation Rate")
    axes[1][0].set_ylim(-0.05, 1.05)
    axes[1][0].grid(True, alpha=0.3)

    axes[1][1].plot(iterations, avg_attacks, '^-', color='#E57373', linewidth=2, markersize=8)
    axes[1][1].set_xlabel("Iteration")
    axes[1][1].set_ylabel("Avg Attacks/Episode")
    axes[1][1].set_title("Judgment Strikes per Episode")
    axes[1][1].grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig("/kaggle/working/training_progress.png", dpi=150, bbox_inches="tight")
    plt.show()
    print("Plot saved to /kaggle/working/training_progress.png")


plot_training_progress(training_stats)

# %% CELL 13 — Save final model and evaluate
save_path = "/kaggle/working/mahoraga_lora_final"

model.save_pretrained(save_path)
tokenizer.save_pretrained(save_path)
print(f"Final LoRA weights saved to: {save_path}")

# Final evaluation
print("\n--- Final Evaluation (10 episodes) ---")
final_rewards = []
final_wins = 0
for ep in range(10):
    env_eval = MahoragaEnv()
    _, ep_reward, ep_stats = run_episode(model, tokenizer, env_eval, verbose=False)
    final_rewards.append(ep_reward)
    if ep_stats["won"]:
        final_wins += 1
    print(f"  Episode {ep+1}: reward={ep_reward:.2f}, "
          f"won={ep_stats['won']}, adapt={ep_stats['adapt_rate']:.1%}, "
          f"attacks={ep_stats['attacks']}")

print(f"\nFinal avg reward: {sum(final_rewards)/len(final_rewards):.2f}")
print(f"Final win rate: {final_wins/10:.0%}")

import shutil
shutil.make_archive("/kaggle/working/mahoraga_results", "zip", "/kaggle/working", "checkpoints")
print("Results packaged: /kaggle/working/mahoraga_results.zip")

# %% CELL 14 — Difficulty-based evaluation
from env.enemy import DifficultyEnemy

print("\n--- Difficulty Evaluation ---")
for difficulty in ["easy", "medium", "hard"]:
    wins = 0
    rewards = []
    for ep in range(10):
        enemy = DifficultyEnemy(difficulty=difficulty)
        env_diff = MahoragaEnv(enemy=enemy)
        _, ep_reward, ep_stats = run_episode(model, tokenizer, env_diff, verbose=False)
        rewards.append(ep_reward)
        if ep_stats["won"]:
            wins += 1

    avg_r = sum(rewards) / len(rewards)
    print(f"  {difficulty.upper():8s}: win_rate={wins/10:.0%}, avg_reward={avg_r:.2f}")

# %% CELL 15 — Export model for HuggingFace
# Option A: Push directly to HuggingFace Hub
HF_REPO_ID = "YOUR_USERNAME/mahoraga-qwen2.5-3b-lora"  # <-- Change this
PUSH_TO_HUB = False  # Set to True to push

if PUSH_TO_HUB:
    from huggingface_hub import login
    login()  # Will prompt for token (use HF_TOKEN secret on Kaggle)

    model.push_to_hub(HF_REPO_ID, tokenizer=tokenizer, private=True)
    print(f"✅ Model pushed to: https://huggingface.co/{HF_REPO_ID}")
else:
    print("Skipping HuggingFace push (set PUSH_TO_HUB=True to enable)")

# Option B: Save merged model (full weights, not just LoRA adapter)
merged_path = "/kaggle/working/mahoraga_merged_full"
model.save_pretrained_merged(merged_path, tokenizer, save_method="merged_16bit")
print(f"Merged 16-bit model saved to: {merged_path}")

# Option C: Package everything for download from Kaggle
shutil.make_archive("/kaggle/working/mahoraga_lora_weights", "zip",
                    "/kaggle/working", "mahoraga_lora_final")
shutil.make_archive("/kaggle/working/mahoraga_full_model", "zip",
                    "/kaggle/working", "mahoraga_merged_full")

print("\n📦 Downloadable files (from Kaggle Output tab):")
print("  1. mahoraga_lora_weights.zip  — LoRA adapter only (small, needs base model)")
print("  2. mahoraga_full_model.zip    — Full merged model (large, standalone)")
print("  3. mahoraga_results.zip       — All checkpoints")
print("\nDone. 🎯")

