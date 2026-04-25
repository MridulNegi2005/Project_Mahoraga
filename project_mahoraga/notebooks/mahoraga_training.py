# %% [markdown]
# # Project Mahoraga — RL-Based LLM Training Notebook
# Qwen 2.5 3B + LoRA + Custom RL Environment
#
# **CRITICAL**: Must clone branch `phase1-env-setup` (not main).
# Main branch has no reward system, subtypes, or heal cooldown.

# %% CELL 1 — Install dependencies
!pip install -q unsloth transformers accelerate peft trl bitsandbytes datasets torch matplotlib

# %% CELL 2 — Clone repo (CORRECT BRANCH) and setup path
import os
import sys

# CRITICAL FIX: Clone the correct branch with reward system
!git clone --branch phase1-env-setup https://github.com/Atishay9828/meta_Mahoraga.git /kaggle/working/meta_Mahoraga

sys.path.insert(0, '/kaggle/working/meta_Mahoraga/project_mahoraga')

print("Repo cloned (branch: phase1-env-setup) and path configured.")

# %% CELL 3 — Import environment and VERIFY reward signal
from env.mahoraga_env import MahoragaEnv

# Sanity check with debug mode ON
env = MahoragaEnv(debug=True)
state = env.reset()
print("Environment loaded successfully.")
print(f"Initial state keys: {list(state.keys())}")
print(f"Agent HP: {state['agent_hp']}")

# Take one test step and VERIFY non-zero reward
state, reward, done, info = env.step(0)
print(f"\n--- REWARD VERIFICATION ---")
print(f"Reward: {reward:.4f}  (MUST be non-zero)")
print(f"Breakdown: {info.get('reward_breakdown', 'MISSING!')}")
print(f"Damage taken: {info.get('damage_taken', 'MISSING!')}")
print(f"Correct adaptation: {info.get('correct_adaptation', 'MISSING!')}")

assert reward != 0.0, "CRITICAL: Reward is still 0.0! Pipeline broken."
assert "reward_breakdown" in info, "CRITICAL: reward_breakdown missing from info!"
print("\n✅ Reward pipeline verified — non-zero rewards flowing.")

# %% CELL 4 — Load model (Unsloth + Qwen 2.5 3B)
from unsloth import FastLanguageModel
import torch

model, tokenizer = FastLanguageModel.from_pretrained(
    model_name="unsloth/Qwen2.5-3B-Instruct",
    max_seq_length=1024,
    dtype=None,  # auto-detect
    load_in_4bit=True,
)

print(f"Model loaded: {model.config._name_or_path}")
print(f"Device: {model.device}")

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
3 = Judgment Strike (attack enemy, burst damage if matching resistance > 60, resets resistances)
4 = Regeneration (heal 300 HP, 3-turn cooldown)

Strategy hints:
- Adapting to the enemy's attack type reduces damage taken
- Building resistance > 60 then using Judgment Strike deals 350+ damage
- Healing at high HP is wasteful

Choose the best action. Return ONLY a single integer (0, 1, 2, 3, or 4). Nothing else."""

    return prompt


# Test prompt
env_test = MahoragaEnv()
test_state = env_test.reset()
print(build_prompt(test_state))

# %% CELL 7 — Output parser
import re

def parse_action(text):
    """Extract integer action 0-4 from model output. Fallback to 0."""
    text = text.strip()

    # Try direct single digit
    if text in ['0', '1', '2', '3', '4']:
        return int(text)

    # Search for first occurrence of 0-4
    match = re.search(r'[0-4]', text)
    if match:
        return int(match.group())

    # Fallback
    return 0


# Test parser
assert parse_action("3") == 3
assert parse_action("Action: 2") == 2
assert parse_action("I choose action 4 because...") == 4
assert parse_action("invalid") == 0
print("Parser tests passed.")

# %% CELL 8 — Single-step inference test
FastLanguageModel.for_inference(model)

env_test = MahoragaEnv()
state = env_test.reset()

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

print(f"Model raw output: '{response}'")
print(f"Parsed action: {action} ({ACTION_NAMES[action]})")

# Verify reward from this step
state, reward, done, info = env_test.step(action)
print(f"Reward from step: {reward:.4f}")
print(f"Breakdown: {info['reward_breakdown']}")

# %% CELL 9 — Rollout loop with reward verification
def run_episode(model, tokenizer, env, max_turns=25, verbose=True):
    """Run one full episode, collecting trajectory data."""
    state = env.reset()
    trajectory = []
    total_reward = 0.0
    correct_count = 0
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
            breakdown = info.get("reward_breakdown", {})
            print(f"Turn {turn+1}: action={action} ({ACTION_NAMES.get(action, '?')}), "
                  f"reward={reward:.2f}, "
                  f"HP={next_state['agent_hp']}/{next_state['enemy_hp']}, "
                  f"adapt={'✓' if info.get('correct_adaptation') else '✗'}")

        state = next_state
        if done:
            break

    adapt_rate = correct_count / total_steps if total_steps > 0 else 0.0
    won = state["agent_hp"] > state["enemy_hp"]

    if verbose:
        reason = info.get("reason", "Unknown")
        print(f"\nEpisode done: {reason} | Total reward: {total_reward:.2f} | "
              f"Turns: {total_steps} | Adapt rate: {adapt_rate:.1%} | Won: {won}")

    return trajectory, total_reward, {"steps": total_steps, "adapt_rate": adapt_rate, "won": won}


# Run one test episode
env_rollout = MahoragaEnv()
trajectory, total_reward, ep_stats = run_episode(model, tokenizer, env_rollout)
print(f"\nCollected {len(trajectory)} steps, total reward: {total_reward:.2f}")
print(f"Reward samples: {[f'{t[\"reward\"]:.2f}' for t in trajectory[:5]]}")

# %% CELL 10 — Prepare RL dataset from trajectories
from datasets import Dataset

def trajectories_to_dataset(all_trajectories):
    """Convert list of trajectories into a HuggingFace Dataset for training."""
    records = []
    for traj in all_trajectories:
        for step in traj:
            messages = [
                {"role": "system", "content": "You are a combat AI. Respond with ONLY a single integer 0-4."},
                {"role": "user", "content": step["prompt"]},
                {"role": "assistant", "content": step["response"]}
            ]
            records.append({
                "messages": messages,
                "prompt": step["prompt"],
                "completion": step["response"],
                "reward": step["reward"],
                "action": step["action"]
            })
    return Dataset.from_list(records)


# Collect multiple episodes for initial dataset
print("Collecting initial trajectories...")
all_trajectories = []
for ep in range(5):
    env_collect = MahoragaEnv()
    traj, ep_reward, _ = run_episode(model, tokenizer, env_collect, verbose=False)
    all_trajectories.append(traj)
    print(f"  Episode {ep+1}: reward={ep_reward:.2f}, steps={len(traj)}")

dataset = trajectories_to_dataset(all_trajectories)
print(f"\nDataset size: {len(dataset)} samples")
print(f"Sample: action={dataset[0]['completion']} reward={dataset[0]['reward']:.2f}")

# Verify rewards are non-zero
rewards = [d["reward"] for d in dataset]
print(f"Reward range: [{min(rewards):.2f}, {max(rewards):.2f}]")
print(f"Non-zero rewards: {sum(1 for r in rewards if r != 0.0)}/{len(rewards)}")

# %% CELL 11 — GRPO-style reward-weighted SFT trainer setup
from trl import SFTTrainer, SFTConfig
import json

def prepare_weighted_dataset(all_trajectories, tokenizer):
    """Create reward-weighted SFT dataset.
    High-reward actions get more weight via duplication.
    Negative-reward actions included at low weight for balanced learning."""
    records = []
    reward_stats = {"strong_pos": 0, "mild_pos": 0, "neutral": 0, "negative": 0}

    for traj in all_trajectories:
        for step in traj:
            r = step["reward"]

            # Determine repetition count based on reward
            if r > 1.0:
                copies = 3  # Strong positive signal
                reward_stats["strong_pos"] += 1
            elif r > 0:
                copies = 2  # Mild positive
                reward_stats["mild_pos"] += 1
            elif r > -1.5:
                copies = 1  # Include neutral/mildly negative for balance
                reward_stats["neutral"] += 1
            else:
                copies = 0  # Skip very bad actions
                reward_stats["negative"] += 1

            text = tokenizer.apply_chat_template(
                [
                    {"role": "system", "content": "You are a combat AI. Respond with ONLY a single integer 0-4."},
                    {"role": "user", "content": step["prompt"]},
                    {"role": "assistant", "content": step["response"]}
                ],
                tokenize=False
            )

            for _ in range(copies):
                records.append({"text": text})

    print(f"  Weighting stats: {reward_stats}")
    return Dataset.from_list(records) if records else None


train_dataset = prepare_weighted_dataset(all_trajectories, tokenizer)
print(f"Reward-weighted dataset: {len(train_dataset)} samples")

# %% CELL 12 — Training loop with checkpoints and metrics
import json
import matplotlib.pyplot as plt

FastLanguageModel.for_training(model)

NUM_ITERATIONS = 5
EPISODES_PER_ITER = 10

# Checkpoint and metrics paths
CHECKPOINT_DIR = "/kaggle/working/checkpoints"
STATS_PATH = "/kaggle/working/training_stats.json"
os.makedirs(CHECKPOINT_DIR, exist_ok=True)

training_stats = []
reward_history = []

for iteration in range(NUM_ITERATIONS):
    print(f"\n{'='*60}")
    print(f"  Iteration {iteration+1}/{NUM_ITERATIONS}")
    print(f"{'='*60}")

    # --- Collect episodes ---
    all_trajectories = []
    iter_rewards = []
    iter_wins = 0
    iter_steps = []
    iter_adapt_rates = []

    for ep in range(EPISODES_PER_ITER):
        env_train = MahoragaEnv()
        traj, ep_reward, ep_stats = run_episode(model, tokenizer, env_train, verbose=False)
        all_trajectories.append(traj)
        iter_rewards.append(ep_reward)
        iter_steps.append(ep_stats["steps"])
        iter_adapt_rates.append(ep_stats["adapt_rate"])
        if ep_stats["won"]:
            iter_wins += 1

    # --- Compute metrics ---
    avg_reward = sum(iter_rewards) / len(iter_rewards)
    win_rate = iter_wins / EPISODES_PER_ITER
    avg_steps = sum(iter_steps) / len(iter_steps)
    avg_adapt_rate = sum(iter_adapt_rates) / len(iter_adapt_rates)

    stats = {
        "iteration": iteration + 1,
        "avg_reward": round(avg_reward, 4),
        "win_rate": round(win_rate, 4),
        "avg_steps": round(avg_steps, 2),
        "adapt_rate": round(avg_adapt_rate, 4),
        "min_reward": round(min(iter_rewards), 4),
        "max_reward": round(max(iter_rewards), 4)
    }
    training_stats.append(stats)
    reward_history.append(avg_reward)

    print(f"  Avg reward: {avg_reward:.2f} (min={min(iter_rewards):.2f}, max={max(iter_rewards):.2f})")
    print(f"  Win rate:   {win_rate:.1%}")
    print(f"  Avg steps:  {avg_steps:.1f}")
    print(f"  Adapt rate: {avg_adapt_rate:.1%}")

    # --- Build reward-weighted dataset ---
    train_dataset = prepare_weighted_dataset(all_trajectories, tokenizer)

    if train_dataset is None or len(train_dataset) == 0:
        print("  No usable samples — skipping training this iteration.")
        continue

    print(f"  Training samples: {len(train_dataset)}")

    # --- Train ---
    FastLanguageModel.for_training(model)

    iter_checkpoint_dir = os.path.join(CHECKPOINT_DIR, f"iteration_{iteration+1}")
    os.makedirs(iter_checkpoint_dir, exist_ok=True)

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
    print(f"  Metrics saved: {STATS_PATH}")

print(f"\n{'='*60}")
print("  Training Complete")
print(f"  Reward history: {[f'{r:.2f}' for r in reward_history]}")
print(f"{'='*60}")

# %% CELL 13 — Plot training progress
def plot_training_progress(stats):
    """Plot reward and win rate across training iterations."""
    iterations = [s["iteration"] for s in stats]
    avg_rewards = [s["avg_reward"] for s in stats]
    win_rates = [s["win_rate"] for s in stats]
    adapt_rates = [s["adapt_rate"] for s in stats]

    fig, axes = plt.subplots(1, 3, figsize=(18, 5))

    # Avg Reward
    axes[0].plot(iterations, avg_rewards, 'o-', color='#4FC3F7', linewidth=2, markersize=8)
    axes[0].set_xlabel("Iteration")
    axes[0].set_ylabel("Avg Reward")
    axes[0].set_title("Average Reward per Iteration")
    axes[0].grid(True, alpha=0.3)
    axes[0].axhline(y=0, color='red', linestyle='--', alpha=0.5)

    # Win Rate
    axes[1].plot(iterations, win_rates, 's-', color='#81C784', linewidth=2, markersize=8)
    axes[1].set_xlabel("Iteration")
    axes[1].set_ylabel("Win Rate")
    axes[1].set_title("Win Rate per Iteration")
    axes[1].set_ylim(-0.05, 1.05)
    axes[1].grid(True, alpha=0.3)

    # Adaptation Rate
    axes[2].plot(iterations, adapt_rates, 'D-', color='#FFB74D', linewidth=2, markersize=8)
    axes[2].set_xlabel("Iteration")
    axes[2].set_ylabel("Adaptation Rate")
    axes[2].set_title("Correct Adaptation Rate per Iteration")
    axes[2].set_ylim(-0.05, 1.05)
    axes[2].grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig("/kaggle/working/training_progress.png", dpi=150, bbox_inches="tight")
    plt.show()
    print("Plot saved to /kaggle/working/training_progress.png")


plot_training_progress(training_stats)

# %% CELL 14 — Save final model and package results
save_path = "/kaggle/working/mahoraga_lora_final"

model.save_pretrained(save_path)
tokenizer.save_pretrained(save_path)
print(f"Final LoRA weights saved to: {save_path}")

# Final evaluation
print("\n--- Final Evaluation (5 episodes) ---")
final_rewards = []
for ep in range(5):
    env_eval = MahoragaEnv()
    _, ep_reward, ep_stats = run_episode(model, tokenizer, env_eval, verbose=False)
    final_rewards.append(ep_reward)
    print(f"  Episode {ep+1}: reward={ep_reward:.2f}, "
          f"won={ep_stats['won']}, adapt={ep_stats['adapt_rate']:.1%}")

print(f"\nFinal avg reward: {sum(final_rewards)/len(final_rewards):.2f}")

# Package results
import shutil
shutil.make_archive("/kaggle/working/mahoraga_results", "zip", "/kaggle/working", "checkpoints")
print("Results packaged: /kaggle/working/mahoraga_results.zip")
print("Done.")
