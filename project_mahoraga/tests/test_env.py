import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from env.mahoraga_env import MahoragaEnv

def run_tests():
    print("Running MahoragaEnv Tests...\n")
    
    # Test 1: Resistance update correctness
    env = MahoragaEnv()
    env.reset()
    env.step(0)  # Slash Adapt
    state = env._get_state()
    assert state["resistances"]["SLASH"] == 40
    assert state["resistances"]["FIRE"] == 0  # Should clamp to 0
    assert state["resistances"]["ENERGY"] == 0
    print("Test 1 Passed: Resistance update correctness")

    # Test 2: Damage calculation
    env.reset()
    env.step(0)  # Slash Adapt (+40)
    env.step(0)  # Slash Adapt (+80 total)
    state, _, _, _ = env.step(3)  # Sword Attack (burst)
    assert state["enemy_hp"] == 1000 - 350
    assert state["resistances"]["SLASH"] == 0
    print("Test 2 Passed: Damage calculation (Burst)")

    # Test 3: Episode termination
    env.reset()
    for _ in range(25):
        state, _, done, info = env.step(4)  # Heal to survive 25 turns
    assert done == True
    assert info["reason"] == "Turn limit reached"
    print("Test 3 Passed: Episode termination (Turn limit)\n")
    
    print("All tests passed!")

if __name__ == "__main__":
    run_tests()
