class MahoragaEnv:
    def __init__(self):
        self.max_hp = 1000
        self.max_turns = 25
        self.reset()

    def reset(self):
        self.agent_hp = self.max_hp
        self.enemy_hp = self.max_hp
        self.resistances = {"slash": 0, "fire": 0, "energy": 0}
        self.current_turn = 0
        self.last_action = None
        self.last_enemy_move = None
        return self._get_obs()

    def _get_obs(self):
        return {
            "agent_hp": self.agent_hp,
            "enemy_hp": self.enemy_hp,
            "resistances": self.resistances.copy(),
            "last_action": self.last_action,
            "last_enemy_move": self.last_enemy_move
        }

    def _update_resistance(self, main_type):
        for res_type in self.resistances:
            if res_type == main_type:
                self.resistances[res_type] += 40
            else:
                self.resistances[res_type] -= 20
            self.resistances[res_type] = max(0, min(80, self.resistances[res_type]))

    def step(self, action):
        if action not in [0, 1, 2, 3, 4]:
            raise ValueError("Invalid action")

        self.current_turn += 1
        self.last_action = action

        if action == 0:
            self._update_resistance("slash")
        elif action == 1:
            self._update_resistance("fire")
        elif action == 2:
            self._update_resistance("energy")
        elif action == 3:
            damage = 350 if self.resistances["slash"] > 60 else 100
            self.enemy_hp = max(0, self.enemy_hp - damage)
            self.resistances = {"slash": 0, "fire": 0, "energy": 0}
        elif action == 4:
            self.agent_hp = min(self.max_hp, self.agent_hp + 300)
            self.resistances = {"slash": 0, "fire": 0, "energy": 0}

        if self.enemy_hp <= 0:
            return self._get_obs(), 0.0, True, {"reason": "Enemy defeated"}

        self.last_enemy_move = "slash"
        enemy_damage = 100 * (1 - self.resistances["slash"] / 100.0)
        self.agent_hp = max(0, int(self.agent_hp - enemy_damage))

        done = False
        info = {}
        if self.agent_hp <= 0:
            done = True
            info = {"reason": "Agent defeated"}
        elif self.current_turn >= self.max_turns:
            done = True
            info = {"reason": "Turn limit reached"}

        return self._get_obs(), 0.0, done, info
