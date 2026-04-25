from env.state import build_state_dict
from env.enemy import Enemy
from env.mechanics import (
    new_resistances, apply_action_effects, compute_enemy_damage,
    check_correct_adaptation
)
from utils.constants import MAX_HP, MAX_TURNS
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
        self.resistances = new_resistances()
        self.adaptation_stack = 0
        self.last_action = None
        self.last_enemy_attack_type = None
        self.last_enemy_subtype = None
        self.turn_number = 0
        return self._get_state()

    def _get_state(self):
        return build_state_dict(
            self.agent_hp,
            self.enemy_hp,
            self.resistances,
            self.last_enemy_attack_type,
            self.last_enemy_subtype,
            self.last_action,
            self.turn_number,
            self.adaptation_stack
        )

    def step(self, action):
        validate_action(action)
        self.turn_number += 1

        # 1. Enemy attacks first
        attack_type, subtype = self.enemy.get_attack()
        enemy_damage = compute_enemy_damage(attack_type, self.resistances)
        self.agent_hp = max(0, self.agent_hp - enemy_damage)
        self.last_enemy_attack_type = attack_type
        self.last_enemy_subtype = subtype

        # Check early death from enemy attack
        if self.agent_hp <= 0:
            self.last_action = action
            return self._get_state(), 0.0, True, {"reason": "Agent defeated"}

        # 2. Mahoraga observes and takes action
        # Check if adaptation is correct (before applying action)
        if check_correct_adaptation(action, attack_type):
            self.adaptation_stack += 1

        # 3. Apply agent action effects
        self.agent_hp, self.enemy_hp, self.resistances, self.adaptation_stack = (
            apply_action_effects(
                action, self.agent_hp, self.enemy_hp,
                self.resistances, self.adaptation_stack
            )
        )
        self.last_action = action

        # 4. Check termination
        done = False
        info = {}

        if self.enemy_hp <= 0:
            done = True
            info["reason"] = "Enemy defeated"
        elif self.agent_hp <= 0:
            done = True
            info["reason"] = "Agent defeated"
        elif self.turn_number >= self.max_turns:
            done = True
            info["reason"] = "Turn limit reached"

        return self._get_state(), 0.0, done, info
