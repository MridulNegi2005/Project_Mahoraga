import gymnasium as gym
from gymnasium import spaces
import numpy as np

from env.mahoraga_env import MahoragaEnv


# === Encoding Maps ===
ATTACK_TYPE_ENCODING = {
    "PHYSICAL": 0,
    "CE": 1,
    "TECHNIQUE": 2,
    None: 0  # Default for initial state
}

SUBTYPE_ENCODING = {
    "SLASH": 0,
    "IMPACT": 1,
    "PIERCE": 2,
    "BLAST": 3,
    "WAVE": 4,
    "BEAM": 5,
    "SPIKE": 6,
    "DELAYED": 7,
    "PATTERN": 8,
    None: 0  # Default for initial state
}

ACTION_ENCODING = {
    0: 0,
    1: 1,
    2: 2,
    3: 3,
    4: 4,
    None: 0  # Default for initial state / wasted turn
}


class MahoragaGymEnv(gym.Env):
    """Gymnasium-compatible wrapper for MahoragaEnv."""

    metadata = {"render_modes": []}

    def __init__(self):
        super().__init__()
        self.env = MahoragaEnv()

        self.action_space = spaces.Discrete(5)

        self.observation_space = spaces.Dict({
            "agent_hp": spaces.Box(low=0, high=1500, shape=(1,), dtype=np.int32),
            "enemy_hp": spaces.Box(low=0, high=1500, shape=(1,), dtype=np.int32),
            "resistances": spaces.Box(low=0, high=80, shape=(3,), dtype=np.int32),
            "last_enemy_attack_type": spaces.Discrete(3),
            "last_enemy_subtype": spaces.Discrete(9),
            "last_action": spaces.Discrete(5),
            "turn_number": spaces.Box(low=0, high=25, shape=(1,), dtype=np.int32)
        })

    def _encode_state(self, state):
        """Convert raw state dict to gymnasium-compatible observation."""
        res = state["resistances"]
        return {
            "agent_hp": np.array([state["agent_hp"]], dtype=np.int32),
            "enemy_hp": np.array([state["enemy_hp"]], dtype=np.int32),
            "resistances": np.array(
                [res["physical"], res["ce"], res["technique"]], dtype=np.int32
            ),
            "last_enemy_attack_type": ATTACK_TYPE_ENCODING[state["last_enemy_attack_type"]],
            "last_enemy_subtype": SUBTYPE_ENCODING[state["last_enemy_subtype"]],
            "last_action": ACTION_ENCODING[state["last_action"]],
            "turn_number": np.array([state["turn_number"]], dtype=np.int32)
        }

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        state = self.env.reset()
        observation = self._encode_state(state)
        info = {}
        return observation, info

    def step(self, action):
        state, reward, done, info = self.env.step(action)
        observation = self._encode_state(state)
        terminated = done
        truncated = False
        return observation, reward, terminated, truncated, info
