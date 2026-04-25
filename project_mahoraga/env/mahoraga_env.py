from env.state import build_state_dict
from env.enemy import Enemy
from env.mechanics import apply_action_effects, reset_resistances
from utils.constants import MAX_HP, MAX_TURNS, DAMAGE_VALUES
from utils.validators import validate_action

class MahoragaEnv:
    def __init__(self):
        self.max_hp = MAX_HP
        self.max_turns = MAX_TURNS
        self.enemy = Enemy()
        self.reset()

    def reset(self):
        self.agent_hp = self.max_hp
        self.enemy_hp = self.max_hp
        self.resistances = reset_resistances()
        self.last_action = None
        self.last_enemy_action = None
        self.turn_number = 0
        return self._get_state()

    def _get_state(self):
        return build_state_dict(
            self.agent_hp,
            self.enemy_hp,
            self.resistances,
            self.last_action,
            self.last_enemy_action,
            self.turn_number
        )

    def step(self, action):
        validate_action(action)

        self.turn_number += 1
        self.last_action = action

        # Apply agent action
        self.agent_hp, self.enemy_hp, self.resistances = apply_action_effects(
            action, self.agent_hp, self.enemy_hp, self.resistances
        )

        done = False
        info = {}

        if self.enemy_hp <= 0:
            done = True
            info["reason"] = "Enemy defeated"
            return self._get_state(), 0.0, done, info

        # Apply enemy action
        enemy_action = self.enemy.get_action()
        self.last_enemy_action = enemy_action

        # Enemy damage logic
        if enemy_action == "SLASH":
            enemy_damage = DAMAGE_VALUES["ENEMY_BASE_DAMAGE"] * (1 - self.resistances["SLASH"] / 100.0)
            self.agent_hp = max(0, int(self.agent_hp - enemy_damage))

        if self.agent_hp <= 0:
            done = True
            info["reason"] = "Agent defeated"
        elif self.turn_number >= self.max_turns:
            done = True
            info["reason"] = "Turn limit reached"

        return self._get_state(), 0.0, done, info
