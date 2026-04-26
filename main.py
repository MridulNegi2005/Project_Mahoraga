import random
from env.mahoraga_env import MahoragaEnv, ACTION_NAMES


def main():
    env = MahoragaEnv(debug=False)
    state = env.reset()

    print("=" * 60)
    print("  PROJECT MAHORAGA — Sorcerer vs Adaptive Boss")
    print("=" * 60)
    print(f"\nInitial State:")
    print(f"  Player HP: {state['player_hp']}  |  Boss HP: {state['boss_hp']}")
    print(f"  Boss Resistances: {state['boss_resistances']}")
    print("-" * 60)

    done = False
    while not done:
        action = random.randint(0, 4)

        player_hp_before = state["player_hp"]
        boss_hp_before = state["boss_hp"]

        state, reward, done, info = env.step(action)

        print(f"\nTurn {state['turn_number']}:")
        print(f"  Player Action: {ACTION_NAMES.get(action, 'Unknown')}")
        print(f"    -> Damage dealt to boss: {info['damage_dealt']}")
        if info.get("black_flash"):
            print(f"    ** BLACK FLASH! **")
        if info.get("adapted"):
            print(f"    !! Boss adapted to {info['adapt_category']}! Wheel turn #{info['boss_wheel_turns']}")
        print(f"  Boss Attack: {info.get('boss_attack_name', 'None')}")
        print(f"    -> Damage taken: {info['damage_taken']}")
        print(f"  HP: Player {player_hp_before} -> {state['player_hp']}")
        print(f"      Boss   {boss_hp_before} -> {state['boss_hp']}")
        print(f"  Boss Resistances: P={state['boss_resistances']['PHYSICAL']} "
              f"CE={state['boss_resistances']['CE']} "
              f"T={state['boss_resistances']['TECHNIQUE']}")
        print(f"  Reward: {reward:.2f}")
        if info.get("heal_on_cooldown"):
            print(f"    ** HEAL BLOCKED (on cooldown) **")

        if done:
            print("\n" + "=" * 60)
            reason = info.get("reason", "Unknown")
            won = state["boss_hp"] <= 0
            print(f"  EPISODE ENDED — {reason}")
            print(f"  Result: {'VICTORY!' if won else 'DEFEAT'}")
            print(f"  Final Player HP: {state['player_hp']}")
            print(f"  Final Boss HP: {state['boss_hp']}")
            print(f"  Total Turns: {state['turn_number']}")
            print("=" * 60)


if __name__ == "__main__":
    main()
