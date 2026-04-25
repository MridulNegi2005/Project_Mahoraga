import random
from env.mahoraga_env import MahoragaEnv

def main():
    env = MahoragaEnv()
    state = env.reset()
    
    print("=== MahoragaEnv Episode Start ===")
    print(f"Initial State: {state}\n")
    
    done = False
    while not done:
        action = random.randint(0, 4)
        
        agent_hp_before = state["agent_hp"]
        enemy_hp_before = state["enemy_hp"]
        
        state, reward, done, info = env.step(action)
        
        print(f"Turn: {state['turn_number']}")
        print(f"Action Taken: {action}")
        print(f"Agent HP: {agent_hp_before} -> {state['agent_hp']}")
        print(f"Enemy HP: {enemy_hp_before} -> {state['enemy_hp']}")
        print(f"Resistances: {state['resistances']}")
        if done:
            print(f"\nEpisode finished! Reason: {info.get('reason')}")
            
if __name__ == "__main__":
    main()
