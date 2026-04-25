from env.state import build_state_dict
from env.enemy import Enemy
from env.mechanics import (
    new_resistances, apply_action_effects, compute_enemy_damage,
    check_correct_adaptation
)
from env.rewards import compute_rewards
from utils.constants import MAX_HP, MAX_TURNS, HEAL_COOLDOWN
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
        self.heal_cooldown_counter = 0
        return self._get_state()

    def _get_state(self):
        return build_state_dict(
            self.agent_hp,
            self.enemy_hp,
            self.resistances,
            self.last_enemy_attack_type,
            self.last_enemy_subtype,
            self.last_action,
            self.turn_number
        )

    def step(self, action):
        validate_action(action)
        self.turn_number += 1

        # Decrement heal cooldown at start of turn
        if self.heal_cooldown_counter > 0:
            self.heal_cooldown_counter -= 1

        # Check heal cooldown — if on cooldown, safely ignore and flag
        heal_on_cooldown = False
        if action == 4 and self.heal_cooldown_counter > 0:
            heal_on_cooldown = True
            action = None  # Nullify action — agent wastes turn

        # 1. Enemy attacks first
        attack = self.enemy.get_attack()
        attack_type = attack["type"]
        subtype = attack["subtype"]
        enemy_damage = compute_enemy_damage(attack_type, self.resistances, subtype=subtype)
        self.agent_hp = max(0, self.agent_hp - enemy_damage)
        self.last_enemy_attack_type = attack_type
        self.last_enemy_subtype = subtype

        # Check early death from enemy attack
        if self.agent_hp <= 0:
            self.last_action = action
            info = {
                "reason": "Agent defeated",
                "damage_taken": enemy_damage,
                "damage_dealt": 0,
                "correct_adaptation": False,
                "adaptation_stack": self.adaptation_stack,
                "heal_on_cooldown": heal_on_cooldown
            }
            state = self._get_state()
            reward_dict = compute_rewards(info, state, action, True)
            info["reward_breakdown"] = reward_dict
            total_reward = sum(reward_dict.values())
            return state, total_reward, True, info

        # 2. Mahoraga observes and takes action
        correct_adaptation = False
        if action is not None:
            correct_adaptation = check_correct_adaptation(action, attack_type)
            if correct_adaptation:
                self.adaptation_stack += 1

        # 3. Apply agent action effects
        damage_dealt = 0
        if action is not None:
            enemy_hp_before = self.enemy_hp
            self.agent_hp, self.enemy_hp, self.resistances, self.adaptation_stack = (
                apply_action_effects(
                    action, self.agent_hp, self.enemy_hp,
                    self.resistances, self.adaptation_stack,
                    enemy_attack_type=attack_type
                )
            )
            damage_dealt = max(0, enemy_hp_before - self.enemy_hp)

            # Set heal cooldown if heal was used
            if action == 4:
                self.heal_cooldown_counter = HEAL_COOLDOWN

        self.last_action = action

        # 4. Check termination
        done = False
        info = {
            "damage_taken": enemy_damage,
            "damage_dealt": damage_dealt,
            "correct_adaptation": correct_adaptation,
            "adaptation_stack": self.adaptation_stack,
            "heal_on_cooldown": heal_on_cooldown
        }

        if self.enemy_hp <= 0:
            done = True
            info["reason"] = "Enemy defeated"
        elif self.agent_hp <= 0:
            done = True
            info["reason"] = "Agent defeated"
        elif self.turn_number >= self.max_turns:
            done = True
            info["reason"] = "Turn limit reached"

        # 5. Compute rewards
        state = self._get_state()
        reward_dict = compute_rewards(info, state, action, done)
        info["reward_breakdown"] = reward_dict
        total_reward = sum(reward_dict.values())

        return state, total_reward, done, info
