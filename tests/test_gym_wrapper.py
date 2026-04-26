import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from env.gym_wrapper import MahoragaGymEnv

PASS = 0
FAIL = 0


def check(name, condition):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  [PASS] {name}")
    else:
        FAIL += 1
        print(f"  [FAIL] {name}")


def test_reset_returns_valid_observation():
    print("\n--- Test: Reset Returns Valid Observation ---")
    env = MahoragaGymEnv()
    obs, info = env.reset()

    check("Reset returns tuple of 2", isinstance(obs, dict) and isinstance(info, dict))
    check("Observation has agent_hp", "agent_hp" in obs)
    check("Observation has enemy_hp", "enemy_hp" in obs)
    check("Observation has resistances", "resistances" in obs)
    check("Observation has last_enemy_attack_type", "last_enemy_attack_type" in obs)
    check("Observation has last_enemy_subtype", "last_enemy_subtype" in obs)
    check("Observation has last_action", "last_action" in obs)
    check("Observation has turn_number", "turn_number" in obs)


def test_observation_matches_space():
    print("\n--- Test: Observation Matches Observation Space ---")
    env = MahoragaGymEnv()
    obs, _ = env.reset()

    check("Initial obs is in observation_space", env.observation_space.contains(obs))

    # Take a step and check again
    obs2, _, _, _, _ = env.step(0)
    check("Post-step obs is in observation_space", env.observation_space.contains(obs2))

    # Judgment Strike
    obs3, _, _, _, _ = env.step(3)
    check("Post-judgment obs is in observation_space", env.observation_space.contains(obs3))


def test_step_returns_correct_format():
    print("\n--- Test: Step Returns Correct Tuple Format ---")
    env = MahoragaGymEnv()
    env.reset()
    result = env.step(0)

    check("Step returns tuple of 5", len(result) == 5)
    obs, reward, terminated, truncated, info = result
    check("obs is dict", isinstance(obs, dict))
    check("reward is float", isinstance(reward, (int, float)))
    check("terminated is bool", isinstance(terminated, bool))
    check("truncated is bool", isinstance(truncated, bool))
    check("truncated is False", truncated is False)
    check("info is dict", isinstance(info, dict))
    check("info has reward_breakdown", "reward_breakdown" in info)


def test_action_space():
    print("\n--- Test: Action Space ---")
    env = MahoragaGymEnv()
    check("Action space is Discrete(5)", env.action_space.n == 5)

    # All valid actions should work
    for a in range(5):
        check(f"Action {a} is in action_space", env.action_space.contains(a))

    check("Action 5 is NOT in action_space", not env.action_space.contains(5))
    check("Action -1 is NOT in action_space", not env.action_space.contains(-1))


def test_multiple_steps():
    print("\n--- Test: Multiple Steps Run Without Crash ---")
    env = MahoragaGymEnv()
    obs, _ = env.reset()

    steps = 0
    done = False
    while not done:
        action = env.action_space.sample()
        obs, reward, terminated, truncated, info = env.step(action)
        done = terminated or truncated
        steps += 1
        # Verify observation stays valid every step
        if not env.observation_space.contains(obs):
            check(f"Obs valid at step {steps}", False)
            return

    check(f"Ran {steps} steps without crash", True)
    check("Episode terminated", terminated is True)
    check("All observations valid throughout episode", True)


def test_reset_after_episode():
    print("\n--- Test: Reset After Episode ---")
    env = MahoragaGymEnv()

    # Run full episode
    env.reset()
    done = False
    while not done:
        _, _, done, _, _ = env.step(env.action_space.sample())

    # Reset and run again
    obs, info = env.reset()
    check("Reset after episode returns valid obs", env.observation_space.contains(obs))
    from utils.constants import PLAYER_HP
    check(f"Agent HP reset to max ({PLAYER_HP})", obs["agent_hp"][0] == PLAYER_HP)
    check("Turn number reset to 0", obs["turn_number"][0] == 0)


if __name__ == "__main__":
    print("=" * 50)
    print("  MahoragaGymEnv Wrapper Tests")
    print("=" * 50)

    test_reset_returns_valid_observation()
    test_observation_matches_space()
    test_step_returns_correct_format()
    test_action_space()
    test_multiple_steps()
    test_reset_after_episode()

    print("\n" + "=" * 50)
    print(f"  Results: {PASS} passed, {FAIL} failed")
    print("=" * 50)

    if FAIL > 0:
        sys.exit(1)
