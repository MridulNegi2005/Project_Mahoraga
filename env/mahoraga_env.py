"""
MahoragaEnv (v2: Boss Redesign)

The RL agent is the PLAYER (sorcerer) fighting against Mahoraga (boss).

Turn flow:
    1. Player chooses action (0-4)
    2. Player's action resolves (attack / domain / heal)
    3. Mahoraga passively adapts (if hit with same type enough)
    4. Mahoraga attacks the player
    5. Check termination
"""
import random
from env.state import build_state_dict
from env.mahoraga_boss import MahoragaBoss
from env.rewards import compute_rewards
from utils.constants import (
    PLAYER_HP, MAHORAGA_HP, MAX_TURNS, HEAL_COOLDOWN,
    ACTION_TO_TYPE, DOMAIN_DURATION, DOMAIN_POST_RESISTANCE_BOOST,
    SUBTYPES, DIFFICULTY_CONFIG,
)
from utils.validators import validate_action


ACTION_NAMES = {
    0: "Physical Strike",
    1: "CE Blast",
    2: "Technique Strike",
    3: "Domain Expansion",
    4: "Reversed Cursed Technique",
    None: "Wasted Turn",
}


class MahoragaEnv:
    """RL environment: Player vs Mahoraga (adaptive boss).

    Actions (Player):
        0: Physical Strike — deal PHYSICAL damage
        1: CE Blast — deal CE damage (15% Black Flash chance)
        2: Technique Strike — deal TECHNIQUE damage (highest base)
        3: Domain Expansion — reset boss resistances, +50% dmg for 3 turns (once)
        4: Reversed Cursed Technique — heal 250 HP (4-turn cooldown)
    """

    def __init__(self, debug=False, difficulty="hard", enemy=None):
        self.difficulty = difficulty.lower()
        self.debug = debug
        self.max_turns = MAX_TURNS

        # Boss setup
        config = DIFFICULTY_CONFIG.get(self.difficulty, DIFFICULTY_CONFIG["hard"])
        self.boss_max_hp = config["boss_hp"]
        self.player_max_hp = PLAYER_HP

        # Legacy compat
        self.max_hp = PLAYER_HP
        self.enemy_max_hp = self.boss_max_hp

        self.reset()

    def reset(self):
        """Reset for new episode."""
        self.player_hp = self.player_max_hp
        self.boss = MahoragaBoss(difficulty=self.difficulty)
        self.turn_number = 0

        # Player state
        self.crit_stack = 0
        self.domain_active = False
        self.domain_turns_left = 0
        self.domain_used = False
        self.heal_cooldown_counter = 0
        self.last_player_action = None
        self.last_category = None
        self.consecutive_same = 0
        self.attack_history = []

        # Boss attack tracking
        self.last_boss_attack_name = None
        self.last_boss_attack_damage = 0

        # Legacy compat
        self.agent_hp = self.player_hp
        self.enemy_hp = self.boss.hp
        self.resistances = {"PHYSICAL": 0, "CE": 0, "TECHNIQUE": 0}
        self.adaptation_stack = 0
        self.last_action = None
        self.last_adapted_category = None
        self.last_enemy_attack_type = None
        self.last_enemy_subtype = None
        self.enemy = self.boss  # Legacy alias

        return self._get_state()

    def _get_state(self):
        return build_state_dict(
            player_hp=self.player_hp,
            boss_hp=self.boss.hp,
            boss_resistances=self.boss.resistances,
            boss_wheel_turns=self.boss.total_wheel_turns,
            last_boss_attack_name=self.last_boss_attack_name,
            last_player_action=self.last_player_action,
            turn_number=self.turn_number,
            crit_stack=self.crit_stack,
            domain_active=self.domain_active,
            domain_turns_left=self.domain_turns_left,
            domain_used=self.domain_used,
            heal_cooldown=self.heal_cooldown_counter,
            last_category=self.last_category,
            consecutive_same=self.consecutive_same,
            attack_history=list(self.attack_history),
            last_enemy_attack_type=self.last_boss_attack_name,
            last_enemy_subtype=None,
        )

    def step(self, action):
        """Execute one turn of combat.

        Flow: Player acts → Boss adapts → Boss attacks → Tick cooldowns → Check done
        """
        validate_action(action)
        self.turn_number += 1

        # ── 0. Tick heal cooldown ──
        if self.heal_cooldown_counter > 0:
            self.heal_cooldown_counter -= 1

        # ── 1. Player acts ──
        heal_on_cooldown = False
        damage_dealt = 0
        black_flash = False
        is_crit = False
        adapted = False
        adapt_category = None
        domain_activated = False
        healed = 0
        action_name = "Unknown"
        category = None
        subtype = None

        prev_category = self.last_category

        if action in ACTION_TO_TYPE:
            # ATTACK
            category = ACTION_TO_TYPE[action]
            subtype = random.choice(SUBTYPES[category])

            # Compute damage
            from env.mechanics import compute_player_damage
            dmg_result = compute_player_damage(
                category, self.boss.resistances, subtype=subtype,
                crit_stack=self.crit_stack, domain_active=self.domain_active
            )
            damage_dealt = dmg_result["damage"]
            black_flash = dmg_result["black_flash"]
            is_crit = dmg_result["crit"]

            # Apply damage to boss
            self.boss.hp = max(0, self.boss.hp - damage_dealt)

            # Boss passive adaptation
            adapt_info = self.boss.receive_hit(category)
            adapted = adapt_info["adapted"]
            adapt_category = adapt_info["category"] if adapted else None

            # Black Flash effect
            if black_flash:
                from utils.constants import BLACK_FLASH_RESISTANCE_REDUCTION
                self.boss.reduce_resistance(category, BLACK_FLASH_RESISTANCE_REDUCTION)

            # Crit stack tracking
            if category == prev_category:
                self.consecutive_same += 1
            else:
                self.consecutive_same = 1

            # Update crit stack
            if category == prev_category:
                self.crit_stack += 1
            else:
                self.crit_stack = 1

            # If crit was used, reset stack
            if is_crit:
                self.crit_stack = 0

            self.last_category = category
            action_name = f"{category} Strike"

            # Track attack history
            self.attack_history.append(category)
            if len(self.attack_history) > 4:
                self.attack_history.pop(0)

        elif action == 3:
            # DOMAIN EXPANSION
            if self.domain_used:
                action_name = "Domain (WASTED)"
            else:
                self.boss.apply_domain_start(DOMAIN_DURATION)
                self.domain_active = True
                self.domain_turns_left = DOMAIN_DURATION
                self.domain_used = True
                self.crit_stack = 0
                domain_activated = True
                action_name = "DOMAIN EXPANSION"

        elif action == 4:
            # REVERSED CURSED TECHNIQUE (heal)
            if self.heal_cooldown_counter > 0:
                heal_on_cooldown = True
                action_name = "Heal (BLOCKED)"
            else:
                from utils.constants import HEAL_AMOUNT
                heal = min(HEAL_AMOUNT, self.player_max_hp - self.player_hp)
                self.player_hp = min(self.player_max_hp, self.player_hp + heal)
                self.heal_cooldown_counter = HEAL_COOLDOWN
                healed = heal
                action_name = "Reversed Cursed Technique"

        self.last_player_action = action

        # ── 1b. Tick domain AFTER player's attack resolves ──
        if self.domain_active and self.domain_turns_left > 0:
            self.domain_turns_left -= 1
            if self.domain_turns_left <= 0:
                self.domain_active = False
                self.boss.apply_domain_end(DOMAIN_POST_RESISTANCE_BOOST)
        self.boss.tick_domain()

        # ── 2. Check if boss died from player's attack ──
        if self.boss.hp <= 0:
            info = self._build_info(
                damage_dealt=damage_dealt, damage_taken=0,
                black_flash=black_flash, crit=is_crit,
                adapted=adapted, adapt_category=adapt_category,
                domain_activated=domain_activated, healed=healed,
                heal_on_cooldown=heal_on_cooldown,
                category=category, subtype=subtype,
                boss_attack_name=None, boss_attack_damage=0,
                action_name=action_name,
                prev_category=prev_category,
                reason="Mahoraga defeated",
            )
            state = self._get_state()
            self._update_legacy(action, category)
            return self._finalize(state, info, done=True, action=action)

        # ── 3. Mahoraga attacks player ──
        boss_attack = self.boss.choose_attack()
        boss_damage = boss_attack["damage"]
        self.player_hp = max(0, self.player_hp - boss_damage)
        self.last_boss_attack_name = boss_attack["name"]
        self.last_boss_attack_damage = boss_damage

        # ── 4. Check termination ──
        done = False
        reason = None
        if self.player_hp <= 0:
            done = True
            reason = "Player defeated"
        elif self.turn_number >= self.max_turns:
            done = True
            reason = "Turn limit reached"

        info = self._build_info(
            damage_dealt=damage_dealt, damage_taken=boss_damage,
            black_flash=black_flash, crit=is_crit,
            adapted=adapted, adapt_category=adapt_category,
            domain_activated=domain_activated, healed=healed,
            heal_on_cooldown=heal_on_cooldown,
            category=category, subtype=subtype,
            boss_attack_name=boss_attack["name"],
            boss_attack_damage=boss_damage,
            action_name=action_name,
            prev_category=prev_category,
            reason=reason,
        )

        state = self._get_state()
        self._update_legacy(action, category)
        return self._finalize(state, info, done=done, action=action)

    def _build_info(self, damage_dealt, damage_taken, black_flash, crit,
                    adapted, adapt_category, domain_activated, healed,
                    heal_on_cooldown, category, subtype,
                    boss_attack_name, boss_attack_damage, action_name,
                    prev_category=None, reason=None):
        """Build the info dict for this step."""
        info = {
            # Damage
            "damage_dealt": damage_dealt,
            "damage_taken": damage_taken,

            # Player attack info
            "category": category,
            "subtype": subtype,
            "black_flash": black_flash,
            "crit": crit,
            "action_name": action_name,

            # Boss adaptation
            "adapted": adapted,
            "adapt_category": adapt_category,
            "boss_resistances": dict(self.boss.resistances),
            "boss_wheel_turns": self.boss.total_wheel_turns,

            # Boss attack
            "boss_attack_name": boss_attack_name,
            "boss_attack_damage": boss_attack_damage,

            # Domain / heal
            "domain_activated": domain_activated,
            "domain_used_before": self.domain_used and not domain_activated,
            "healed": healed,
            "heal_on_cooldown": heal_on_cooldown,

            # For rewards (prev_category = previous turn's category, for variety check)
            "last_category": prev_category,
            "consecutive_same": self.consecutive_same,

            # Legacy compat
            "correct_adaptation": adapted,
            "adaptation_stack": self.boss.total_wheel_turns,
        }
        if reason:
            info["reason"] = reason
        return info

    def _finalize(self, state, info, done, action):
        """Compute rewards and return."""
        reward_dict = compute_rewards(info, state, action, done)
        info["reward_breakdown"] = reward_dict
        total_reward = sum(reward_dict.values())

        if self.debug:
            print(f"[T{self.turn_number}] Action: {info['action_name']} | "
                  f"Dealt: {info['damage_dealt']} | Taken: {info['damage_taken']} | "
                  f"BF: {info['black_flash']} | Adapted: {info['adapted']} | "
                  f"Reward: {total_reward:.2f}")

        return state, total_reward, done, info

    def _update_legacy(self, action, category):
        """Update legacy fields for backward compat with API/frontend."""
        self.agent_hp = self.player_hp
        self.enemy_hp = self.boss.hp
        self.last_action = action
        self.last_enemy_attack_type = self.last_boss_attack_name
        self.adaptation_stack = self.boss.total_wheel_turns
        self.resistances = dict(self.boss.resistances)
        if category:
            self.last_adapted_category = category
