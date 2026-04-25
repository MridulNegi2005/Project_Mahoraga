import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from env.gym_wrapper import MahoragaGymEnv


def main():
    env = MahoragaGymEnv()
    obs, info = env.reset()

    print("=" * 60)
    print("  PROJECT MAHORAGA -- Gymnasium Random Agent")
    print("=" * 60)
    print(f"\nAction Space: {env.action_space}")
    print(f"Observation Space keys: {list(env.observation_space.spaces.keys())}")
    print("-" * 60)

    total_reward = 0.0
    steps = 0
    done = False

    while not done:
        action = env.action_space.sample()
        obs, reward, terminated, truncated, info = env.step(action)
        done = terminated or truncated
        total_reward += reward
        steps += 1

        print(f"\nStep {steps}: action={action}, reward={reward:.2f}, done={done}")
        print(f"  Agent HP: {obs['agent_hp'][0]}  |  Enemy HP: {obs['enemy_hp'][0]}")
        print(f"  Resistances: {obs['resistances']}")

    print("\n" + "=" * 60)
    print(f"  Episode complete in {steps} steps")
    print(f"  Total reward: {total_reward:.2f}")
    print(f"  Reason: {info.get('reason', 'Unknown')}")
    print("=" * 60)


if __name__ == "__main__":
    main()
