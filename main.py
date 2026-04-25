import random
from env.mahoraga_env import MahoragaEnv

ACTION_NAMES = {
    0: "Adapt PHYSICAL",
    1: "Adapt CE",
    2: "Adapt TECHNIQUE",
    3: "Judgment Strike",
    4: "Regeneration",
    None: "(Wasted Turn)"
}


def main():
    env = MahoragaEnv()
    state = env.reset()

    print("=" * 60)
    print("  PROJECT MAHORAGA -- Curriculum Episode")
    print("=" * 60)
    print(f"\nInitial State:")
    print(f"  Agent HP: {state['agent_hp']}  |  Enemy HP: {state['enemy_hp']}")
    print(f"  Resistances: {state['resistances']}")
    print("-" * 60)

    done = False
    while not done:
        action = random.randint(0, 4)

        agent_hp_before = state["agent_hp"]
        enemy_hp_before = state["enemy_hp"]

        state, reward, done, info = env.step(action)

        print(f"\nTurn {state['turn_number']}:")
        print(f"  Enemy:")
        print(f"    -> {state['last_enemy_subtype']} ({state['last_enemy_attack_type']})")
        print(f"    -> Damage: {info['damage_taken']}")
        print(f"  Mahoraga:")
        print(f"    -> {ACTION_NAMES.get(env.last_action, 'Unknown')}")
        print(f"  Result:")
        print(f"    -> Damage: {info['damage_taken']} | "
              f"Correct Adaptation: {'YES' if info.get('correct_adaptation') else 'NO'} | "
              f"Stack: {info['adaptation_stack']}")
        print(f"    -> Agent HP: {agent_hp_before} -> {state['agent_hp']}")
        print(f"    -> Enemy HP: {enemy_hp_before} -> {state['enemy_hp']}")
        print(f"    -> Reward: {reward:.2f}")
        if info.get("heal_on_cooldown"):
            print(f"    ** HEAL BLOCKED (on cooldown) **")

        if done:
            print("\n" + "=" * 60)
            print(f"  EPISODE ENDED -- {info.get('reason', 'Unknown')}")
            print(f"  Final Agent HP: {state['agent_hp']}")
            print(f"  Final Enemy HP: {state['enemy_hp']}")
            print(f"  Total Turns: {state['turn_number']}")
            print("=" * 60)


if __name__ == "__main__":
    main()
