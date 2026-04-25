# %% [markdown]
# # Project Mahoraga — RL-Based LLM Training Notebook
# Qwen 2.5 3B + LoRA + Custom RL Environment

# %% CELL 1 — Install dependencies
!pip install -q unsloth transformers accelerate peft trl bitsandbytes datasets torch

# %% CELL 2 — Clone repo and setup path
import os

!git clone https://github.com/Atishay9828/meta_Mahoraga.git /kaggle/working/meta_Mahoraga

import sys
sys.path.insert(0, '/kaggle/working/meta_Mahoraga/project_mahoraga')

print("Repo cloned and path configured.")

# %% CELL 3 — Import environment and sanity check
from env.mahoraga_env import MahoragaEnv

env = MahoragaEnv()
state = env.reset()
print("Environment loaded successfully.")
print(f"Initial state: {state}")

# Take one test step
state, reward, done, info = env.step(0)
print(f"After action 0: reward={reward:.2f}, done={done}")
print(f"State: {state}")

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
    4: "Regeneration"
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

# %% CELL 9 — Rollout loop (no training)
def run_episode(model, tokenizer, env, max_turns=25, verbose=True):
    """Run one full episode, collecting trajectory data."""
    state = env.reset()
    trajectory = []
    total_reward = 0.0

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
            print(f"Turn {turn+1}: action={action} ({ACTION_NAMES[action]}), "
                  f"reward={reward:.2f}, HP={next_state['agent_hp']}/{next_state['enemy_hp']}")

        state = next_state
        if done:
            break

    if verbose:
        reason = info.get("reason", "Unknown")
        print(f"\nEpisode done: {reason} | Total reward: {total_reward:.2f} | Turns: {len(trajectory)}")

    return trajectory, total_reward


# Run one test episode
env_rollout = MahoragaEnv()
trajectory, total_reward = run_episode(model, tokenizer, env_rollout)
print(f"\nCollected {len(trajectory)} steps, total reward: {total_reward:.2f}")

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
    traj, ep_reward = run_episode(model, tokenizer, env_collect, verbose=False)
    all_trajectories.append(traj)
    print(f"  Episode {ep+1}: reward={ep_reward:.2f}, steps={len(traj)}")

dataset = trajectories_to_dataset(all_trajectories)
print(f"\nDataset size: {len(dataset)} samples")
print(f"Sample: {dataset[0]['completion']} (reward={dataset[0]['reward']:.2f})")

# %% CELL 11 — GRPO-style reward-weighted SFT trainer setup
from trl import SFTTrainer, SFTConfig

def prepare_weighted_dataset(all_trajectories):
    """Create reward-weighted SFT dataset.
    High-reward actions get more weight via duplication."""
    records = []
    for traj in all_trajectories:
        for step in traj:
            # Determine repetition count based on reward
            # Positive reward -> more copies, negative -> fewer/none
            if step["reward"] > 1.0:
                copies = 3  # Strong positive signal
            elif step["reward"] > 0:
                copies = 2  # Mild positive
            elif step["reward"] > -1.0:
                copies = 1  # Neutral-ish
            else:
                copies = 0  # Skip bad actions

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

    return Dataset.from_list(records)


train_dataset = prepare_weighted_dataset(all_trajectories)
print(f"Reward-weighted dataset: {len(train_dataset)} samples")

# %% CELL 12 — Training loop
FastLanguageModel.for_training(model)

NUM_ITERATIONS = 3
EPISODES_PER_ITER = 10

reward_history = []

for iteration in range(NUM_ITERATIONS):
    print(f"\n{'='*50}")
    print(f"  Iteration {iteration+1}/{NUM_ITERATIONS}")
    print(f"{'='*50}")

    # Collect episodes
    all_trajectories = []
    iter_rewards = []

    for ep in range(EPISODES_PER_ITER):
        env_train = MahoragaEnv()
        traj, ep_reward = run_episode(model, tokenizer, env_train, verbose=False)
        all_trajectories.append(traj)
        iter_rewards.append(ep_reward)

    avg_reward = sum(iter_rewards) / len(iter_rewards)
    reward_history.append(avg_reward)
    print(f"  Avg reward: {avg_reward:.2f} (min={min(iter_rewards):.2f}, max={max(iter_rewards):.2f})")

    # Build reward-weighted dataset
    train_dataset = prepare_weighted_dataset(all_trajectories)
    print(f"  Training samples: {len(train_dataset)}")

    if len(train_dataset) == 0:
        print("  No positive samples — skipping training this iteration.")
        continue

    # Train
    FastLanguageModel.for_training(model)

    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=train_dataset,
        args=SFTConfig(
            output_dir=f"/kaggle/working/mahoraga_checkpoints/iter_{iteration+1}",
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

print(f"\n{'='*50}")
print("  Training Complete")
print(f"  Reward history: {[f'{r:.2f}' for r in reward_history]}")
print(f"{'='*50}")

# %% CELL 13 — Save model
save_path = "/kaggle/working/mahoraga_lora_final"

model.save_pretrained(save_path)
tokenizer.save_pretrained(save_path)

print(f"LoRA weights saved to: {save_path}")

# Final evaluation
print("\n--- Final Evaluation (5 episodes) ---")
final_rewards = []
for ep in range(5):
    env_eval = MahoragaEnv()
    _, ep_reward = run_episode(model, tokenizer, env_eval, verbose=False)
    final_rewards.append(ep_reward)
    print(f"  Episode {ep+1}: reward={ep_reward:.2f}")

print(f"\nFinal avg reward: {sum(final_rewards)/len(final_rewards):.2f}")
print("Done.")
