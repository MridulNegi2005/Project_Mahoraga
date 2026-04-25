import random
from env.mahoraga_env import MahoragaEnv

ACTION_NAMES = {
    0: "Adapt PHYSICAL",
    1: "Adapt CE",
    2: "Adapt TECHNIQUE",
    3: "Judgment Strike",
    4: "Regeneration"
}


def main():
    env = MahoragaEnv()
    state = env.reset()

    print("=" * 60)
    print("  PROJECT MAHORAGA — Phase 1 Episode")
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
        print(f"  Enemy Attack: {state['last_enemy_attack_type']} ({state['last_enemy_subtype']})")
        print(f"  Agent Action: {ACTION_NAMES[action]}")
        print(f"  Agent HP:  {agent_hp_before} -> {state['agent_hp']}")
        print(f"  Enemy HP:  {enemy_hp_before} -> {state['enemy_hp']}")
        print(f"  Resistances: {state['resistances']}")
        print(f"  Adaptation Stack: {env.adaptation_stack}")

        if done:
            print("\n" + "=" * 60)
            print(f"  EPISODE ENDED — {info.get('reason', 'Unknown')}")
            print(f"  Final Agent HP: {state['agent_hp']}")
            print(f"  Final Enemy HP: {state['enemy_hp']}")
            print(f"  Total Turns: {state['turn_number']}")
            print("=" * 60)


if __name__ == "__main__":
    main()
