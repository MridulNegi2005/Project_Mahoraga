import gymnasium as gym
from gymnasium import spaces
import numpy as np

from env.mahoraga_env import MahoragaEnv
from utils.constants import PLAYER_HP, MAHORAGA_HP, MAX_TURNS, RESISTANCE_MAX


ATTACK_TYPE_ENCODING = {
    "PHYSICAL": 0, "CE": 1, "TECHNIQUE": 2,
    "Fist Strike": 0, "Adapted Strike": 1, "Cleave": 2,
    "Positive Energy Heal": 0, None: 0,
}

SUBTYPE_ENCODING = {
    "SLASH": 0, "IMPACT": 1, "PIERCE": 2,
    "BLAST": 3, "WAVE": 4, "BEAM": 5,
    "SPIKE": 6, "DELAYED": 7, "PATTERN": 8,
    "CLEAVE": 9, None: 0,
}

ACTION_ENCODING = {0: 0, 1: 1, 2: 2, 3: 3, 4: 4, None: 0}


class MahoragaGymEnv(gym.Env):
    """Gymnasium-compatible wrapper for MahoragaEnv."""

    metadata = {"render_modes": []}

    def __init__(self, difficulty="hard"):
        super().__init__()
        self.env = MahoragaEnv(difficulty=difficulty)

        self.action_space = spaces.Discrete(5)

        self.observation_space = spaces.Dict({
            "agent_hp": spaces.Box(low=0, high=PLAYER_HP, shape=(1,), dtype=np.int32),
            "enemy_hp": spaces.Box(low=0, high=MAHORAGA_HP, shape=(1,), dtype=np.int32),
            "resistances": spaces.Box(low=0, high=RESISTANCE_MAX, shape=(3,), dtype=np.int32),
            "last_enemy_attack_type": spaces.Discrete(4),
            "last_enemy_subtype": spaces.Discrete(10),
            "last_action": spaces.Discrete(5),
            "turn_number": spaces.Box(low=0, high=MAX_TURNS, shape=(1,), dtype=np.int32),
        })

    def _encode_state(self, state):
        """Convert raw state dict to gymnasium-compatible observation."""
        res = state["resistances"]
        attack_type = state.get("last_enemy_attack_type")
        subtype = state.get("last_enemy_subtype")
        return {
            "agent_hp": np.array([state["agent_hp"]], dtype=np.int32),
            "enemy_hp": np.array([state["enemy_hp"]], dtype=np.int32),
            "resistances": np.array(
                [res["physical"], res["ce"], res["technique"]], dtype=np.int32
            ),
            "last_enemy_attack_type": ATTACK_TYPE_ENCODING.get(attack_type, 0),
            "last_enemy_subtype": SUBTYPE_ENCODING.get(subtype, 0),
            "last_action": ACTION_ENCODING.get(state["last_action"], 0),
            "turn_number": np.array([state["turn_number"]], dtype=np.int32),
        }

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        state = self.env.reset()
        return self._encode_state(state), {}

    def step(self, action):
        state, reward, done, info = self.env.step(action)
        return self._encode_state(state), reward, done, False, info
