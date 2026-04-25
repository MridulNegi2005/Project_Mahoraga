"""
Mahoraga Adaptation Engine — Aero-Tactical Combat Dashboard
============================================================
Stitch-inspired 'Midnight Stealth' UI using Gradio Blocks.
Fully wired to the live MahoragaEnv with interactive action buttons.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

import gradio as gr
from env.mahoraga_env import MahoragaEnv
from utils.constants import MAX_HP, ENEMY_HP

# ──────────────────────────────────────────────
# CONSTANTS
# ──────────────────────────────────────────────
ACTION_NAMES = {
    0: "Adapt PHYSICAL",
    1: "Adapt CE",
    2: "Adapt TECHNIQUE",
    3: "Judgment Strike",
    4: "Regeneration",
    None: "(Wasted Turn)"
}

# ──────────────────────────────────────────────
# AERO-TACTICAL MIDNIGHT STEALTH CSS
# Ported from Stitch design system
# ──────────────────────────────────────────────
CUSTOM_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;900&display=swap');
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700&display=swap');

/* ─── GLOBAL OVERRIDES ─── */
.gradio-container {
    background: #0b1120 !important;
    font-family: 'Inter', sans-serif !important;
    min-height: 100vh;
}
.dark {
    --body-background-fill: #0b1120 !important;
    --block-background-fill: transparent !important;
}

/* ─── HEADER BAR ─── */
#header-bar {
    background: rgba(11, 17, 32, 0.8) !important;
    backdrop-filter: blur(12px);
    border-bottom: 1px solid rgba(71, 85, 105, 0.5) !important;
    padding: 12px 24px !important;
    margin-bottom: 24px !important;
}
#header-bar h1 {
    font-size: 1.1rem !important;
    font-weight: 900 !important;
    letter-spacing: -0.02em !important;
    color: #f8fafc !important;
    text-transform: uppercase !important;
    margin: 0 !important;
}
#header-bar p {
    color: #94a3b8 !important;
    font-size: 0.8rem !important;
    margin: 0 !important;
}

/* ─── STATUS BADGE ─── */
.status-badge {
    background: #00f6ff !important;
    color: #000000 !important;
    font-size: 0.65rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.05em !important;
    padding: 6px 14px !important;
    border-radius: 2px !important;
    text-transform: uppercase !important;
    display: inline-block !important;
}
.status-badge-danger {
    background: #f87171 !important;
}

/* ─── GLASS PANEL CARDS ─── */
.glass-panel {
    background: rgba(15, 23, 42, 0.65) !important;
    backdrop-filter: blur(12px) !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    border-radius: 8px !important;
    padding: 24px !important;
    box-shadow: none !important;
}
.glass-panel-accent {
    background: rgba(15, 23, 42, 0.65) !important;
    backdrop-filter: blur(12px) !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    border-left: 4px solid #1e293b !important;
    border-radius: 8px !important;
    padding: 32px !important;
    box-shadow: none !important;
}

/* ─── SECTION HEADERS ─── */
.section-header {
    font-size: 0.7rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.05em !important;
    text-transform: uppercase !important;
    color: #94a3b8 !important;
    padding-bottom: 12px !important;
    border-bottom: 1px solid rgba(51, 65, 85, 0.3) !important;
    margin-bottom: 16px !important;
}

/* ─── HP BARS ─── */
.hp-bar-enemy .progress-bar { background: #00f6ff !important; }
.hp-bar-enemy .progress-bar-wrap {
    background: #1e293b !important;
    border: none !important;
    border-radius: 9999px !important;
    height: 8px !important;
}
.hp-bar-agent .progress-bar { background: #00f6ff !important; }
.hp-bar-agent .progress-bar-wrap {
    background: #1e293b !important;
    border: none !important;
    border-radius: 9999px !important;
    height: 8px !important;
}

/* ─── RESISTANCE BARS (thin, subtle) ─── */
.res-bar .progress-bar-wrap {
    background: #1e293b !important;
    border: none !important;
    border-radius: 9999px !important;
    height: 6px !important;
}
.res-physical .progress-bar { background: #f59e0b !important; }
.res-ce .progress-bar { background: #818cf8 !important; }
.res-technique .progress-bar { background: #f87171 !important; }

/* ─── STAT CELLS (mono data) ─── */
.stat-cell textarea, .stat-cell input {
    background: #0f172a !important;
    border: 1px solid rgba(51, 65, 85, 0.2) !important;
    border-radius: 8px !important;
    color: #f8fafc !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 1.5rem !important;
    font-weight: 700 !important;
    text-align: center !important;
    padding: 16px !important;
}
.stat-cell-sm textarea, .stat-cell-sm input {
    background: #0f172a !important;
    border: 1px solid rgba(51, 65, 85, 0.2) !important;
    border-radius: 8px !important;
    color: #00f6ff !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.85rem !important;
    font-weight: 600 !important;
    text-align: center !important;
    padding: 10px !important;
}

/* ─── HP LABELS ─── */
.hp-label {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 1.4rem !important;
    font-weight: 700 !important;
    color: #f8fafc !important;
}
.hp-label-sub {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.75rem !important;
    font-weight: 600 !important;
    color: #00f6ff !important;
    letter-spacing: 0.1em !important;
}

/* ─── TURN LOG ─── */
#turn-log textarea {
    background: #020617 !important;
    border: 1px solid rgba(51, 65, 85, 0.2) !important;
    border-radius: 8px !important;
    color: #cbd5e1 !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.75rem !important;
    line-height: 1.7 !important;
    padding: 16px !important;
}

/* ─── BIG MOMENTS ─── */
#big-moments {
    min-height: 120px;
    display: flex;
    flex-direction: column;
    justify-content: center;
}
#big-moments h1 {
    font-size: 2.5rem !important;
    font-weight: 700 !important;
    letter-spacing: -0.02em !important;
    color: #f8fafc !important;
    text-transform: uppercase !important;
    line-height: 1.1 !important;
    margin-bottom: 8px !important;
}
#big-moments h3 {
    font-size: 0.7rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
    color: #00f6ff !important;
    margin-bottom: 12px !important;
}
#big-moments p {
    color: #94a3b8 !important;
    font-size: 0.85rem !important;
    max-width: 600px !important;
}

/* ─── ACTION BUTTONS ─── */
.action-btn button {
    background: rgba(15, 23, 42, 0.65) !important;
    backdrop-filter: blur(8px) !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    color: #f8fafc !important;
    border-radius: 4px !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.05em !important;
    font-size: 0.7rem !important;
    padding: 10px 16px !important;
    transition: all 0.2s ease !important;
}
.action-btn button:hover {
    background: rgba(30, 41, 59, 0.8) !important;
    border-color: rgba(255, 255, 255, 0.2) !important;
}
.btn-primary button {
    background: #0ea5e9 !important;
    color: #020617 !important;
    border: 1px solid #0ea5e9 !important;
}
.btn-primary button:hover {
    opacity: 0.9 !important;
}
.btn-danger button {
    background: rgba(127, 29, 29, 0.6) !important;
    border: 1px solid rgba(248, 113, 113, 0.3) !important;
    color: #fca5a5 !important;
}
.btn-danger button:hover {
    background: rgba(127, 29, 29, 0.8) !important;
}
.btn-reset button {
    background: transparent !important;
    border: 1px solid rgba(71, 85, 105, 0.5) !important;
    color: #94a3b8 !important;
}
.btn-reset button:hover {
    background: rgba(30, 41, 59, 0.5) !important;
    color: #f8fafc !important;
}

/* ─── GRADIO OVERRIDES ─── */
.gradio-container .prose { max-width: none !important; }
.gradio-container .prose h1, .gradio-container .prose h2,
.gradio-container .prose h3, .gradio-container .prose p {
    margin: 0 !important;
}
label { color: #94a3b8 !important; font-size: 0.7rem !important; letter-spacing: 0.05em !important; text-transform: uppercase !important; font-weight: 600 !important; }
footer { display: none !important; }
.svelte-1ed2p3z { border: none !important; }
"""

# ──────────────────────────────────────────────
# THEME
# ──────────────────────────────────────────────
theme = gr.themes.Base(
    font=gr.themes.GoogleFont("Inter"),
    font_mono=gr.themes.GoogleFont("JetBrains Mono"),
).set(
    body_background_fill="#0b1120",
    block_background_fill="transparent",
    block_border_color="transparent",
    body_text_color="#f8fafc",
    block_title_text_color="#94a3b8",
)

# ──────────────────────────────────────────────
# GAME LOGIC
# ──────────────────────────────────────────────

# Global env (simple approach matching teammate's pattern)
env = None
combat_log = []


def format_integrity(current, max_hp):
    pct = current / max_hp * 100 if max_hp > 0 else 0
    return f"{pct:.1f}% INTEGRITY"


def format_hp_display(current, max_hp):
    return f"{current} / {max_hp}"


def res_status(val):
    if val >= 80:
        return "IMMUNE"
    elif val >= 60:
        return f"{val}/80  HARDENED"
    elif val > 0:
        return f"{val}/80  MITIGATING"
    else:
        return "0/80  VULNERABLE"


def reset_env():
    global env, combat_log
    env = MahoragaEnv()
    state = env.reset()
    combat_log = ["[SYS] INITIALIZING ADAPTATION ENGINE...\n"]

    return (
        # HP values + labels
        gr.update(value=state["enemy_hp"], label=f"Enemy HP: {state['enemy_hp']}/{ENEMY_HP}"),
        format_hp_display(state["enemy_hp"], ENEMY_HP),
        format_integrity(state["enemy_hp"], ENEMY_HP),
        gr.update(value=state["agent_hp"], label=f"Mahoraga HP: {state['agent_hp']}/{MAX_HP}"),
        format_hp_display(state["agent_hp"], MAX_HP),
        format_integrity(state["agent_hp"], MAX_HP),
        # Resistances
        gr.update(value=state["resistances"]["physical"]),
        res_status(state["resistances"]["physical"]),
        gr.update(value=state["resistances"]["ce"]),
        res_status(state["resistances"]["ce"]),
        gr.update(value=state["resistances"]["technique"]),
        res_status(state["resistances"]["technique"]),
        # Counters
        "0",
        "READY",
        "0",
        "0.00",
        # Big Moments
        "### TACTICAL ANALYSIS UPDATE\n# AWAITING ENGAGEMENT\nSurveillance feed initialized. Monitoring Subject Alpha engagement parameters.",
        # Turn Log
        "\n".join(combat_log),
        # Status badge
        "SYSTEM READY",
    )


def take_action(action_idx):
    global env, combat_log

    if env is None:
        return reset_env()

    state, reward, done, info = env.step(action_idx)

    # Build log entry
    action_name = ACTION_NAMES.get(env.last_action, "Unknown")
    entry = f"[ENEMY] {state['last_enemy_subtype']} ({state['last_enemy_attack_type']}) -> {info['damage_taken']} DMG\n"
    entry += f"[MAHORAGA] {action_name}"
    if info.get("correct_adaptation"):
        entry += " -> ADAPTATION MATCHED"
    if info.get("damage_dealt", 0) > 0:
        entry += f" -> {info['damage_dealt']} DMG DEALT"
    if info.get("heal_on_cooldown"):
        entry += " -> BLOCKED (COOLDOWN)"
    entry += f"\n[RESULT] Reward: {reward:.2f} | Stack: {info['adaptation_stack']}\n"

    if done:
        entry += f"\n{'='*45}\n"
        entry += f"ENGAGEMENT TERMINATED: {info.get('reason', 'Unknown')}\n"
        entry += f"Final: Mahoraga {state['agent_hp']} HP | Enemy {state['enemy_hp']} HP\n"
        entry += f"{'='*45}\n"

    combat_log.append(entry)

    # Cooldown text
    cd = env.heal_cooldown_counter
    cooldown_text = f"{cd} TURNS" if cd > 0 else "READY"

    # Big Moments
    big_moment = "### TACTICAL ANALYSIS UPDATE\n# COMBAT IN PROGRESS\nMonitoring real-time engagement telemetry."
    if done:
        big_moment = f"### ENGAGEMENT TERMINATED\n# {info.get('reason', 'Unknown').upper()}\nFinal state: Mahoraga {state['agent_hp']} HP | Enemy {state['enemy_hp']} HP. Reset to deploy again."
    elif action_idx == 3 and info.get("damage_dealt", 0) > 0:
        big_moment = f"### TACTICAL ANALYSIS UPDATE\n# JUDGMENT STRIKE - EXECUTED\nSubject deployed decisive strike dealing {info['damage_dealt']} damage. Defensive parameters reset."
    elif info.get("correct_adaptation"):
        big_moment = f"### TACTICAL ANALYSIS UPDATE\n# ADAPTATION COMPLETE\nSubject has successfully analyzed and developed countermeasures to the incoming {state['last_enemy_attack_type']} attack pattern."

    # Status badge
    status = "ACTIVE ENGAGEMENT" if not done else "ENGAGEMENT ENDED"

    return (
        gr.update(value=state["enemy_hp"], label=f"Enemy HP: {state['enemy_hp']}/{ENEMY_HP}"),
        format_hp_display(state["enemy_hp"], ENEMY_HP),
        format_integrity(state["enemy_hp"], ENEMY_HP),
        gr.update(value=state["agent_hp"], label=f"Mahoraga HP: {state['agent_hp']}/{MAX_HP}"),
        format_hp_display(state["agent_hp"], MAX_HP),
        format_integrity(state["agent_hp"], MAX_HP),
        gr.update(value=state["resistances"]["physical"]),
        res_status(state["resistances"]["physical"]),
        gr.update(value=state["resistances"]["ce"]),
        res_status(state["resistances"]["ce"]),
        gr.update(value=state["resistances"]["technique"]),
        res_status(state["resistances"]["technique"]),
        str(info["adaptation_stack"]),
        cooldown_text,
        str(state["turn_number"]),
        f"{reward:.2f}",
        big_moment,
        "\n".join(combat_log),
        status,
    )


# ──────────────────────────────────────────────
# BUILD LAYOUT
# ──────────────────────────────────────────────
with gr.Blocks(title="Mahoraga Adaptation Engine") as demo:

    # ── TOP BAR ──
    with gr.Row(elem_id="header-bar"):
        with gr.Column(scale=4):
            gr.Markdown("# AERO-TACTICAL")
            gr.Markdown("Mahoraga Adaptation Engine — Meta RL Hackathon")
        with gr.Column(scale=1):
            status_badge = gr.Textbox(value="SYSTEM READY", interactive=False, show_label=False, elem_classes=["stat-cell-sm"])

    # ══════════════════════════════════════════
    # ROW 1: TARGET STATUS (8) | CORE STATS (4)
    # ══════════════════════════════════════════
    with gr.Row(equal_height=True):
        # ── Enemy Card (8 cols) ──
        with gr.Column(scale=2, elem_classes=["glass-panel"]):
            gr.Markdown("🎯 Target Status: Enemy", elem_classes=["section-header"])
            with gr.Row():
                with gr.Column(scale=3):
                    enemy_hp_bar = gr.Slider(minimum=0, maximum=ENEMY_HP, value=ENEMY_HP,
                                             label=f"Enemy HP: {ENEMY_HP}/{ENEMY_HP}",
                                             interactive=False, elem_classes=["hp-bar-enemy"])
                with gr.Column(scale=1):
                    enemy_hp_display = gr.Textbox(value=format_hp_display(ENEMY_HP, ENEMY_HP),
                                                  label="HP", interactive=False, elem_classes=["stat-cell"])
            enemy_integrity = gr.Textbox(value="100.0% INTEGRITY", interactive=False,
                                         show_label=False, elem_classes=["stat-cell-sm"])

            with gr.Row():
                turn_display = gr.Textbox(value="0", label="Turn", interactive=False, elem_classes=["stat-cell-sm"])
                reward_display = gr.Textbox(value="0.00", label="Last Reward", interactive=False, elem_classes=["stat-cell-sm"])
                threat_display = gr.Textbox(value="READY", label="Threat Level", interactive=False, elem_classes=["stat-cell-sm"])

        # ── Mahoraga Card (4 cols) ──
        with gr.Column(scale=1, elem_classes=["glass-panel"]):
            gr.Markdown("🧠 Core: Mahoraga", elem_classes=["section-header"])
            agent_hp_bar = gr.Slider(minimum=0, maximum=MAX_HP, value=MAX_HP,
                                     label=f"Mahoraga HP: {MAX_HP}/{MAX_HP}",
                                     interactive=False, elem_classes=["hp-bar-agent"])
            agent_hp_display = gr.Textbox(value=format_hp_display(MAX_HP, MAX_HP),
                                          label="HP", interactive=False, elem_classes=["stat-cell"])
            agent_integrity = gr.Textbox(value="100.0% INTEGRITY", interactive=False,
                                         show_label=False, elem_classes=["stat-cell-sm"])
            with gr.Row():
                adapt_stack = gr.Textbox(value="0", label="Adaptation Stack", interactive=False, elem_classes=["stat-cell-sm"])
                heal_cd = gr.Textbox(value="READY", label="Heal Cooldown", interactive=False, elem_classes=["stat-cell-sm"])

    # ══════════════════════════════════════════
    # ROW 2: BIG MOMENTS (full width)
    # ══════════════════════════════════════════
    with gr.Group(elem_classes=["glass-panel-accent"]):
        big_moments = gr.Markdown(
            value="### TACTICAL ANALYSIS UPDATE\n# AWAITING ENGAGEMENT\nSurveillance feed initialized. Monitoring Subject Alpha engagement parameters.",
            elem_id="big-moments"
        )

    # ══════════════════════════════════════════
    # ROW 3: RESISTANCES (6) | TURN LOG (6)
    # ══════════════════════════════════════════
    with gr.Row(equal_height=True):
        # ── Resistances ──
        with gr.Column(scale=1):
            with gr.Group(elem_classes=["glass-panel"]):
                gr.Markdown("🛡️ Active Resistances", elem_classes=["section-header"])

                gr.Markdown("**PHYSICAL**")
                res_phys_bar = gr.Slider(minimum=0, maximum=80, value=0, label="Physical",
                                         interactive=False, elem_classes=["res-bar", "res-physical"])
                res_phys_status = gr.Textbox(value="0/80  VULNERABLE", interactive=False,
                                             show_label=False, elem_classes=["stat-cell-sm"])

                gr.Markdown("**CURSED ENERGY**")
                res_ce_bar = gr.Slider(minimum=0, maximum=80, value=0, label="CE",
                                       interactive=False, elem_classes=["res-bar", "res-ce"])
                res_ce_status = gr.Textbox(value="0/80  VULNERABLE", interactive=False,
                                           show_label=False, elem_classes=["stat-cell-sm"])

                gr.Markdown("**TECHNIQUE**")
                res_tech_bar = gr.Slider(minimum=0, maximum=80, value=0, label="Technique",
                                          interactive=False, elem_classes=["res-bar", "res-technique"])
                res_tech_status = gr.Textbox(value="0/80  VULNERABLE", interactive=False,
                                              show_label=False, elem_classes=["stat-cell-sm"])

            # ── ACTION PANEL ──
            with gr.Group(elem_classes=["glass-panel"]):
                gr.Markdown("⚡ Manual Override", elem_classes=["section-header"])
                with gr.Row():
                    btn_phys = gr.Button("Adapt Physical", elem_classes=["action-btn"])
                    btn_ce = gr.Button("Adapt CE", elem_classes=["action-btn"])
                    btn_tech = gr.Button("Adapt Technique", elem_classes=["action-btn"])
                with gr.Row():
                    btn_judgment = gr.Button("Judgment Strike", elem_classes=["action-btn", "btn-danger"])
                    btn_regen = gr.Button("Regeneration", elem_classes=["action-btn", "btn-primary"])
                with gr.Row():
                    btn_reset = gr.Button("Reset Deployment", elem_classes=["action-btn", "btn-reset"])

        # ── Turn Log ──
        with gr.Column(scale=1):
            with gr.Group(elem_classes=["glass-panel"]):
                gr.Markdown("📋 Turn Log", elem_classes=["section-header"])
                turn_log = gr.Textbox(value="", label="", lines=20, max_lines=30,
                                      interactive=False, elem_id="turn-log", show_label=False)

    # ──────────────────────────────────────────
    # EVENT BINDINGS
    # ──────────────────────────────────────────
    all_outputs = [
        enemy_hp_bar, enemy_hp_display, enemy_integrity,
        agent_hp_bar, agent_hp_display, agent_integrity,
        res_phys_bar, res_phys_status,
        res_ce_bar, res_ce_status,
        res_tech_bar, res_tech_status,
        adapt_stack, heal_cd,
        turn_display, reward_display,
        big_moments, turn_log, status_badge,
    ]

    btn_phys.click(fn=lambda: take_action(0), outputs=all_outputs)
    btn_ce.click(fn=lambda: take_action(1), outputs=all_outputs)
    btn_tech.click(fn=lambda: take_action(2), outputs=all_outputs)
    btn_judgment.click(fn=lambda: take_action(3), outputs=all_outputs)
    btn_regen.click(fn=lambda: take_action(4), outputs=all_outputs)
    btn_reset.click(fn=reset_env, outputs=all_outputs)

    demo.load(fn=reset_env, outputs=all_outputs)


# ──────────────────────────────────────────────
# LAUNCH
# ──────────────────────────────────────────────
if __name__ == "__main__":
    demo.launch(theme=theme, css=CUSTOM_CSS, share=False)
