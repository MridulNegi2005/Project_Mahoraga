import os
import sys
import gradio as gr

# Add project_mahoraga to path so we can import the environment
sys.path.append(os.path.join(os.path.dirname(__file__), "project_mahoraga"))
from env.mahoraga_env import MahoragaEnv

# ──────────────────────────────────────────────
# TACTICAL BRUTALISM CSS (Shadcn/ui inspired)
# ──────────────────────────────────────────────
CUSTOM_CSS = """
/* Global */
.gradio-container {
    background: #09090b !important;
    font-family: 'Inter', sans-serif !important;
    min-height: 100vh;
}

/* Title Banner */
#title-banner {
    text-align: center;
    padding: 16px 0;
}
#title-banner h1 {
    font-size: 2rem !important;
    font-weight: 800 !important;
    color: #f4f4f5 !important;
    text-transform: uppercase;
    letter-spacing: 2px !important;
    margin-bottom: 4px !important;
}
#title-banner p {
    color: #a1a1aa !important;
    font-size: 0.85rem !important;
    letter-spacing: 4px;
    text-transform: uppercase;
}

/* Cards */
.panel-card {
    background: #18181b !important;
    border: 1px solid #27272a !important;
    border-radius: 6px !important;
    padding: 20px !important;
    box-shadow: none !important;
}

/* Section headers */
.section-label {
    font-size: 0.75rem !important;
    letter-spacing: 2px !important;
    text-transform: uppercase !important;
    color: #a1a1aa !important;
    font-weight: 600 !important;
    margin-bottom: 8px !important;
}

/* HP Bars */
.enemy-hp .progress-bar { background: #ef4444 !important; transition: width 0.3s ease; }
.enemy-hp .progress-bar-wrap { background: #450a0a !important; border: 1px solid #7f1d1d !important; border-radius: 4px !important; }

.agent-hp .progress-bar { background: #10b981 !important; transition: width 0.3s ease; }
.agent-hp .progress-bar-wrap { background: #064e3b !important; border: 1px solid #065f46 !important; border-radius: 4px !important; }

/* Resistance Bars */
.res-physical .progress-bar { background: #f59e0b !important; transition: width 0.3s ease; }
.res-physical .progress-bar-wrap { background: #451a03 !important; border: 1px solid #78350f !important; border-radius: 4px !important; }

.res-ce .progress-bar { background: #6366f1 !important; transition: width 0.3s ease; }
.res-ce .progress-bar-wrap { background: #312e81 !important; border: 1px solid #3730a3 !important; border-radius: 4px !important; }

.res-technique .progress-bar { background: #ec4899 !important; transition: width 0.3s ease; }
.res-technique .progress-bar-wrap { background: #831843 !important; border: 1px solid #9d174d !important; border-radius: 4px !important; }

/* Stat pills */
.stat-pill textarea, .stat-pill input {
    background: #09090b !important;
    border: 1px solid #27272a !important;
    border-radius: 4px !important;
    color: #f4f4f5 !important;
    font-size: 2rem !important;
    font-weight: 700 !important;
    text-align: center !important;
    padding: 12px !important;
    font-family: 'JetBrains Mono', monospace !important;
}

/* Turn Log */
#turn-log textarea {
    background: #09090b !important;
    border: 1px solid #27272a !important;
    border-radius: 4px !important;
    color: #d4d4d8 !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.8rem !important;
    line-height: 1.6 !important;
    padding: 16px !important;
}

/* Big Moments */
#big-moments {
    background: #09090b !important;
    border: 1px solid #27272a !important;
    border-radius: 6px !important;
    padding: 24px !important;
    text-align: center;
    min-height: 140px;
    display: flex;
    flex-direction: column;
    justify-content: center;
}
#big-moments h1 {
    font-size: 1.6rem !important;
    color: #f4f4f5 !important;
    font-weight: 800 !important;
    letter-spacing: 1px !important;
    margin-bottom: 8px !important;
}
#big-moments h3 {
    color: #a1a1aa !important;
    font-weight: 500 !important;
    font-size: 1rem !important;
}
#big-moments em {
    color: #8b5cf6 !important;
    font-style: normal !important;
}

/* Buttons */
.action-btn {
    background: #18181b !important;
    border: 1px solid #3f3f46 !important;
    color: #f4f4f5 !important;
    border-radius: 4px !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 1px !important;
    font-size: 0.75rem !important;
    transition: all 0.2s ease !important;
}
.action-btn:hover {
    background: #27272a !important;
    border-color: #52525b !important;
}
.primary-btn {
    background: #10b981 !important;
    color: #022c22 !important;
    border: 1px solid #059669 !important;
}
.primary-btn:hover {
    background: #34d399 !important;
}
.danger-btn {
    background: #ef4444 !important;
    color: #450a0a !important;
    border: 1px solid #b91c1c !important;
}
.danger-btn:hover {
    background: #f87171 !important;
}

footer { display: none !important; }
"""

# ──────────────────────────────────────────────
# THEME OVERRIDE (Minimalist base)
# ──────────────────────────────────────────────
theme = gr.themes.Base(
    font=gr.themes.GoogleFont("Inter"),
    font_mono=gr.themes.GoogleFont("JetBrains Mono"),
).set(
    body_background_fill="#09090b",
    block_background_fill="#18181b",
    block_border_color="#27272a",
    body_text_color="#f4f4f5",
    block_title_text_color="#a1a1aa",
)

# ──────────────────────────────────────────────
# GAME LOGIC WRAPPER
# ──────────────────────────────────────────────

ACTION_MAP = {
    0: "Adapt Physical",
    1: "Adapt CE",
    2: "Adapt Technique",
    3: "Judgment Strike",
    4: "Regeneration"
}

def hp_label(name: str, current: int, maximum: int) -> str:
    pct = int((current / maximum) * 100) if maximum > 0 else 0
    return f"{name} ({current}/{maximum} — {pct}%)"

def res_label(name: str, current: int, maximum: int) -> str:
    return f"{name} ({current}/{maximum})"

def format_turn_log(turn: int, enemy_type: str, enemy_subtype: str, action_name: str, damage: int, correct: bool, stack: int) -> str:
    correct_str = "YES" if correct else "NO"
    return f"""Turn {turn}:
  Enemy: → {enemy_subtype} ({enemy_type})
  Mahoraga: → {action_name}
  Result: → Damage: {damage} | Correct Adaptation: {correct_str} | Stack: {stack}
─────────────────────────────────────────
"""

def init_game():
    env = MahoragaEnv()
    state = env.reset()
    # Return UI updates for reset state
    return (
        env,
        env.max_hp, # max hp constant
        state["enemy_hp"],
        state["agent_hp"],
        hp_label("ENEMY", state["enemy_hp"], env.max_hp),
        hp_label("MAHORAGA", state["agent_hp"], env.max_hp),
        state["resistances"]["physical"],
        res_label("Physical", state["resistances"]["physical"], 80),
        state["resistances"]["ce"],
        res_label("CE", state["resistances"]["ce"], 80),
        state["resistances"]["technique"],
        res_label("Technique", state["resistances"]["technique"], 80),
        str(state["adaptation_stack"]),
        "0", # Heal cooldown
        "INITIALIZING COMBAT PROTOCOLS...\n─────────────────────────────────────────\n",
        "### AWAITING ACTION\n_Combat simulator initialized._"
    )

def step_game(env, heal_cooldown_val, log_text, action_idx):
    if env is None:
        return [gr.update()] * 15 # Do nothing if env not initialized

    # Handle cooldowns simply
    heal_cd = int(heal_cooldown_val)
    if action_idx == 4 and heal_cd > 0:
        return [gr.update()] * 15 # Cannot heal yet
    
    if action_idx == 4:
        heal_cd = 3 # Reset cooldown to 3
    elif heal_cd > 0:
        heal_cd -= 1

    # Record state before action
    agent_hp_before = env.agent_hp
    enemy_hp_before = env.enemy_hp
    stack_before = env.adaptation_stack
    
    # Step environment
    state, reward, done, info = env.step(action_idx)
    
    # Calculate deltas for logging
    enemy_attack = state["last_enemy_attack_type"] or "NONE"
    enemy_sub = state["last_enemy_subtype"] or "NONE"
    
    # Determine if adaptation was correct (stack increased)
    correct_adapt = (state["adaptation_stack"] > stack_before)
    damage_taken = agent_hp_before - state["agent_hp"]

    # Append to log
    new_log = log_text + format_turn_log(
        state["turn_number"],
        enemy_attack,
        enemy_sub,
        ACTION_MAP[action_idx],
        damage_taken,
        correct_adapt,
        state["adaptation_stack"]
    )

    # Big Moments text
    big_moment_str = "### COMBAT IN PROGRESS"
    if done:
        big_moment_str = f"# SIMULATION ENDED\n### Reason: {info.get('reason', 'Unknown')}\n*Reset to play again.*"
    elif action_idx == 3:
        # Judgment Strike fired
        damage_dealt = enemy_hp_before - state["enemy_hp"]
        big_moment_str = f"# ⚡ JUDGMENT STRIKE ⚡\n### 🔥 {damage_dealt} DAMAGE DEALT 🔥\n*The wheel has turned.*"
    elif correct_adapt:
        big_moment_str = f"# ADAPTATION SUCCESSFUL\n### Stack Increased\n*Agent successfully adapted to {enemy_attack}.*"

    return (
        env,
        str(heal_cd),
        state["enemy_hp"],
        state["agent_hp"],
        hp_label("ENEMY", state["enemy_hp"], env.max_hp),
        hp_label("MAHORAGA", state["agent_hp"], env.max_hp),
        state["resistances"]["physical"],
        res_label("Physical", state["resistances"]["physical"], 80),
        state["resistances"]["ce"],
        res_label("CE", state["resistances"]["ce"], 80),
        state["resistances"]["technique"],
        res_label("Technique", state["resistances"]["technique"], 80),
        str(state["adaptation_stack"]),
        new_log,
        big_moment_str
    )

# ──────────────────────────────────────────────
# BUILD THE LAYOUT
# ──────────────────────────────────────────────
with gr.Blocks(title="Mahoraga Adaptation Engine") as demo:

    # State variables
    env_state = gr.State()
    max_hp_state = gr.State(1000)

    # ── Title ──
    with gr.Column(elem_id="title-banner"):
        gr.Markdown("# Mahoraga Adaptation Engine")
        gr.Markdown("Meta RL Hackathon — Tactical Dashboard")

    # ════════════════════════════════════════════
    # TOP ROW: HP Bars
    # ════════════════════════════════════════════
    with gr.Row(equal_height=True):
        # — Enemy HP —
        with gr.Column(scale=1, elem_classes=["panel-card"]):
            gr.Markdown("ENEMY", elem_classes=["section-label"])
            enemy_hp_bar = gr.Slider(
                minimum=0, maximum=1000, value=1000, label="Enemy HP", 
                interactive=False, elem_classes=["enemy-hp"]
            )

        # — Agent HP —
        with gr.Column(scale=1, elem_classes=["panel-card"]):
            gr.Markdown("MAHORAGA", elem_classes=["section-label"])
            agent_hp_bar = gr.Slider(
                minimum=0, maximum=1000, value=1000, label="Mahoraga HP",
                interactive=False, elem_classes=["agent-hp"]
            )

    # ════════════════════════════════════════════
    # MID ROW: Resistances + Counters | Big Moments
    # ════════════════════════════════════════════
    with gr.Row(equal_height=True):

        # ── Left column ──
        with gr.Column(scale=1):
            # Resistances
            with gr.Group(elem_classes=["panel-card"]):
                gr.Markdown("RESISTANCES", elem_classes=["section-label"])
                res_physical = gr.Slider(minimum=0, maximum=80, value=0, label="Physical", interactive=False, elem_classes=["res-physical"])
                res_ce = gr.Slider(minimum=0, maximum=80, value=0, label="CE", interactive=False, elem_classes=["res-ce"])
                res_technique = gr.Slider(minimum=0, maximum=80, value=0, label="Technique", interactive=False, elem_classes=["res-technique"])

            # Counters
            with gr.Group(elem_classes=["panel-card"]):
                gr.Markdown("COUNTERS", elem_classes=["section-label"])
                with gr.Row():
                    adaptation_stack = gr.Textbox(value="0", label="Adaptation Stack", interactive=False, elem_classes=["stat-pill"])
                    heal_cooldown = gr.Textbox(value="0", label="Heal Cooldown", interactive=False, elem_classes=["stat-pill"])

        # ── Right column ──
        with gr.Column(scale=1):
            with gr.Group(elem_classes=["panel-card"]):
                gr.Markdown("BIG MOMENTS", elem_classes=["section-label"])
                big_moments = gr.Markdown(value="### AWAITING ACTION\n_Combat simulator initialized._", elem_id="big-moments")

            # Actions Panel
            with gr.Group(elem_classes=["panel-card"]):
                gr.Markdown("MANUAL OVERRIDE (ACTIONS)", elem_classes=["section-label"])
                with gr.Row():
                    btn_adapt_phys = gr.Button("Adapt Physical", elem_classes=["action-btn"])
                    btn_adapt_ce = gr.Button("Adapt CE", elem_classes=["action-btn"])
                    btn_adapt_tech = gr.Button("Adapt Technique", elem_classes=["action-btn"])
                with gr.Row():
                    btn_judgment = gr.Button("Judgment Strike", elem_classes=["action-btn", "danger-btn"])
                    btn_regen = gr.Button("Regeneration", elem_classes=["action-btn", "primary-btn"])
                with gr.Row():
                    btn_reset = gr.Button("Reset Simulator", elem_classes=["action-btn"])

    # ════════════════════════════════════════════
    # BOTTOM ROW: Turn Log
    # ════════════════════════════════════════════
    with gr.Group(elem_classes=["panel-card"]):
        gr.Markdown("TURN LOG", elem_classes=["section-label"])
        turn_log = gr.Textbox(value="", label="", lines=12, max_lines=20, interactive=False, elem_id="turn-log", show_label=False)

    # ──────────────────────────────────────────────
    # EVENT BINDINGS
    # ──────────────────────────────────────────────
    
    outputs = [
        env_state, heal_cooldown, 
        enemy_hp_bar, agent_hp_bar, enemy_hp_bar, agent_hp_bar, # Need to update both value and label? Slider only accepts value updates directly. 
        # Wait, gr.update(value=..., label=...) is better
    ]
    
    outputs_full = [
        env_state, heal_cooldown,
        enemy_hp_bar, agent_hp_bar,
        res_physical, res_ce, res_technique,
        adaptation_stack, turn_log, big_moments
    ]

    # Redefine step wrapper to return kwargs for sliders so we can update value and label
    def step_wrapper(env, heal_cd, log, action_idx):
        if env is None: return [gr.update()]*10
        (new_env, new_heal_cd, 
         e_hp, a_hp, e_hp_lbl, a_hp_lbl, 
         r_p, r_p_lbl, r_c, r_c_lbl, r_t, r_t_lbl, 
         new_stack, new_log, new_bm) = step_game(env, heal_cd, log, action_idx)
        
        return [
            new_env,
            new_heal_cd,
            gr.update(value=e_hp, label=e_hp_lbl),
            gr.update(value=a_hp, label=a_hp_lbl),
            gr.update(value=r_p, label=r_p_lbl),
            gr.update(value=r_c, label=r_c_lbl),
            gr.update(value=r_t, label=r_t_lbl),
            new_stack,
            new_log,
            new_bm
        ]

    def reset_wrapper():
        (new_env, max_hp, 
         e_hp, a_hp, e_hp_lbl, a_hp_lbl, 
         r_p, r_p_lbl, r_c, r_c_lbl, r_t, r_t_lbl, 
         new_stack, new_heal_cd, new_log, new_bm) = init_game()
         
        return [
            new_env,
            new_heal_cd,
            gr.update(value=e_hp, maximum=max_hp, label=e_hp_lbl),
            gr.update(value=a_hp, maximum=max_hp, label=a_hp_lbl),
            gr.update(value=r_p, label=r_p_lbl),
            gr.update(value=r_c, label=r_c_lbl),
            gr.update(value=r_t, label=r_t_lbl),
            new_stack,
            new_log,
            new_bm
        ]

    # Bind load event to init
    demo.load(
        reset_wrapper,
        inputs=[],
        outputs=outputs_full
    )

    # Bind buttons
    btn_adapt_phys.click(fn=lambda e, h, l: step_wrapper(e, h, l, 0), inputs=[env_state, heal_cooldown, turn_log], outputs=outputs_full)
    btn_adapt_ce.click(fn=lambda e, h, l: step_wrapper(e, h, l, 1), inputs=[env_state, heal_cooldown, turn_log], outputs=outputs_full)
    btn_adapt_tech.click(fn=lambda e, h, l: step_wrapper(e, h, l, 2), inputs=[env_state, heal_cooldown, turn_log], outputs=outputs_full)
    btn_judgment.click(fn=lambda e, h, l: step_wrapper(e, h, l, 3), inputs=[env_state, heal_cooldown, turn_log], outputs=outputs_full)
    btn_regen.click(fn=lambda e, h, l: step_wrapper(e, h, l, 4), inputs=[env_state, heal_cooldown, turn_log], outputs=outputs_full)
    
    btn_reset.click(fn=reset_wrapper, inputs=[], outputs=outputs_full)

# ──────────────────────────────────────────────
# LAUNCH
# ──────────────────────────────────────────────
if __name__ == "__main__":
    demo.launch(theme=theme, css=CUSTOM_CSS)
