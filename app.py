"""
Mahoraga Adaptation Engine — Gradio Dashboard (Phase 1: Static Layout)
======================================================================
A visual turn-by-turn fight dashboard for the Meta RL Hackathon.
This file defines the complete Gradio Blocks layout with mock data.
Phase 2 will wire in state management and live update functions.
"""

import gradio as gr

# ──────────────────────────────────────────────
# MOCK DATA — will be replaced by live state in Phase 2
# ──────────────────────────────────────────────
MOCK_ENEMY_HP = 640
MOCK_AGENT_HP = 780
MOCK_MAX_HP = 1000

MOCK_RES_PHYSICAL = 40
MOCK_RES_CE = 0
MOCK_RES_TECHNIQUE = 60
MOCK_RES_MAX = 80

MOCK_ADAPTATION_STACK = 2
MOCK_HEAL_COOLDOWN = 1

MOCK_TURN_LOG = """\
Turn 1:
  Enemy: → Slash (Physical)
  Mahoraga: → Adapt Physical
  Result: → Damage: 120 | Correct Adaptation: YES | Stack: 1
─────────────────────────────────────────
Turn 2:
  Enemy: → Cursed Blast (CE)
  Mahoraga: → Adapt CE
  Result: → Damage: 150 | Correct Adaptation: YES | Stack: 2
─────────────────────────────────────────
Turn 3:
  Enemy: → Domain Slash (Technique)
  Mahoraga: → Judgment Strike
  Result: → Damage: 0 | Correct Adaptation: NO | Stack: 0
─────────────────────────────────────────
Turn 4:
  Enemy: → Slash (Physical)
  Mahoraga: → Adapt Physical
  Result: → Damage: 72 | Correct Adaptation: YES | Stack: 1
─────────────────────────────────────────
Turn 5:
  Enemy: → Cursed Blast (CE)
  Mahoraga: → Regeneration
  Result: → Damage: 150 | Correct Adaptation: NO | Stack: 1
"""

MOCK_BIG_MOMENT = """\
# ⚡ JUDGMENT STRIKE — ADAPTED! ⚡
### 🔥 350 BURST DAMAGE + 100 STACK BONUS 🔥
### *The wheel has turned. Adaptation complete.*
"""

# ──────────────────────────────────────────────
# CUSTOM CSS — Dark JJK-inspired theme
# ──────────────────────────────────────────────
CUSTOM_CSS = """
/* ── Global ─────────────────────────────── */
.gradio-container {
    background: linear-gradient(145deg, #0a0a12 0%, #12101f 50%, #0d0b18 100%) !important;
    font-family: 'Inter', 'Segoe UI', sans-serif !important;
    min-height: 100vh;
}

/* ── Title Banner ───────────────────────── */
#title-banner {
    text-align: center;
    padding: 18px 0 8px 0;
}
#title-banner h1 {
    font-size: 2.4rem !important;
    font-weight: 800 !important;
    letter-spacing: 4px !important;
    background: linear-gradient(135deg, #c084fc 0%, #f472b6 35%, #fb923c 70%, #facc15 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    text-transform: uppercase;
    margin-bottom: 2px !important;
    filter: drop-shadow(0 0 18px rgba(192, 132, 252, 0.35));
}
#title-banner p {
    color: #a1a1aa !important;
    font-size: 0.85rem !important;
    letter-spacing: 5px;
    text-transform: uppercase;
}

/* ── Card panels ────────────────────────── */
.panel-card {
    background: rgba(17, 15, 28, 0.85) !important;
    border: 1px solid rgba(139, 92, 246, 0.18) !important;
    border-radius: 16px !important;
    padding: 20px 24px !important;
    backdrop-filter: blur(12px);
    box-shadow: 0 4px 30px rgba(0, 0, 0, 0.4), inset 0 1px 0 rgba(139, 92, 246, 0.08);
}

/* ── Section headers ────────────────────── */
.section-label {
    font-size: 0.7rem !important;
    letter-spacing: 4px !important;
    text-transform: uppercase !important;
    color: #8b5cf6 !important;
    font-weight: 700 !important;
    margin-bottom: 6px !important;
}

/* ── HP Bars ────────────────────────────── */
.enemy-hp .progress-bar {
    background: linear-gradient(90deg, #dc2626 0%, #f87171 100%) !important;
    border-radius: 6px !important;
    transition: width 0.6s cubic-bezier(0.34, 1.56, 0.64, 1);
}
.enemy-hp .progress-bar-wrap {
    background: rgba(220, 38, 38, 0.12) !important;
    border-radius: 6px !important;
    border: 1px solid rgba(220, 38, 38, 0.2) !important;
}
.agent-hp .progress-bar {
    background: linear-gradient(90deg, #059669 0%, #34d399 100%) !important;
    border-radius: 6px !important;
    transition: width 0.6s cubic-bezier(0.34, 1.56, 0.64, 1);
}
.agent-hp .progress-bar-wrap {
    background: rgba(5, 150, 105, 0.12) !important;
    border-radius: 6px !important;
    border: 1px solid rgba(5, 150, 105, 0.2) !important;
}

/* ── Resistance Bars ────────────────────── */
.res-physical .progress-bar {
    background: linear-gradient(90deg, #f59e0b 0%, #fbbf24 100%) !important;
}
.res-physical .progress-bar-wrap {
    background: rgba(245, 158, 11, 0.10) !important;
    border: 1px solid rgba(245, 158, 11, 0.18) !important;
}
.res-ce .progress-bar {
    background: linear-gradient(90deg, #6366f1 0%, #a5b4fc 100%) !important;
}
.res-ce .progress-bar-wrap {
    background: rgba(99, 102, 241, 0.10) !important;
    border: 1px solid rgba(99, 102, 241, 0.18) !important;
}
.res-technique .progress-bar {
    background: linear-gradient(90deg, #ec4899 0%, #f9a8d4 100%) !important;
}
.res-technique .progress-bar-wrap {
    background: rgba(236, 72, 153, 0.10) !important;
    border: 1px solid rgba(236, 72, 153, 0.18) !important;
}

/* ── Stat pills ─────────────────────────── */
.stat-pill textarea, .stat-pill input {
    background: rgba(139, 92, 246, 0.08) !important;
    border: 1px solid rgba(139, 92, 246, 0.22) !important;
    border-radius: 12px !important;
    color: #e2e8f0 !important;
    font-size: 1.6rem !important;
    font-weight: 700 !important;
    text-align: center !important;
    padding: 10px !important;
    font-family: 'JetBrains Mono', 'Fira Code', monospace !important;
}

/* ── Turn Log ───────────────────────────── */
#turn-log textarea {
    background: rgba(8, 6, 18, 0.9) !important;
    border: 1px solid rgba(139, 92, 246, 0.12) !important;
    border-radius: 12px !important;
    color: #c4b5fd !important;
    font-family: 'JetBrains Mono', 'Fira Code', monospace !important;
    font-size: 0.78rem !important;
    line-height: 1.65 !important;
    padding: 16px !important;
    scrollbar-width: thin;
    scrollbar-color: #6d28d9 transparent;
}
#turn-log textarea::-webkit-scrollbar { width: 6px; }
#turn-log textarea::-webkit-scrollbar-thumb {
    background: #6d28d9; border-radius: 3px;
}

/* ── Big Moments ────────────────────────── */
#big-moments {
    background: radial-gradient(ellipse at center, rgba(139, 92, 246, 0.12) 0%, rgba(10, 10, 18, 0) 70%) !important;
    border: 2px solid rgba(250, 204, 21, 0.3) !important;
    border-radius: 16px !important;
    padding: 24px !important;
    text-align: center;
    min-height: 120px;
    animation: pulse-glow 2.5s ease-in-out infinite;
}
#big-moments h1 {
    font-size: 1.8rem !important;
    background: linear-gradient(135deg, #facc15 0%, #fb923c 50%, #f472b6 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    font-weight: 900 !important;
    letter-spacing: 2px !important;
}
#big-moments h3 {
    color: #fbbf24 !important;
    font-weight: 600 !important;
}
#big-moments em {
    color: #a78bfa !important;
}

@keyframes pulse-glow {
    0%, 100% { box-shadow: 0 0 15px rgba(250, 204, 21, 0.08), 0 0 40px rgba(139, 92, 246, 0.05); }
    50%      { box-shadow: 0 0 25px rgba(250, 204, 21, 0.18), 0 0 60px rgba(139, 92, 246, 0.12); }
}

/* ── HP value overlay text ──────────────── */
.hp-value {
    font-family: 'JetBrains Mono', monospace !important;
    font-weight: 700 !important;
    font-size: 0.85rem !important;
    letter-spacing: 1px;
}

/* ── Misc tweaks ────────────────────────── */
.gr-button {
    border-radius: 10px !important;
}
footer { display: none !important; }
"""

# ──────────────────────────────────────────────
# THEME
# ──────────────────────────────────────────────
theme = gr.themes.Base(
    primary_hue=gr.themes.colors.violet,
    secondary_hue=gr.themes.colors.fuchsia,
    neutral_hue=gr.themes.colors.slate,
    font=gr.themes.GoogleFont("Inter"),
    font_mono=gr.themes.GoogleFont("JetBrains Mono"),
).set(
    body_background_fill="#0a0a12",
    body_background_fill_dark="#0a0a12",
    block_background_fill="rgba(17,15,28,0.7)",
    block_background_fill_dark="rgba(17,15,28,0.7)",
    block_border_color="rgba(139,92,246,0.15)",
    block_border_color_dark="rgba(139,92,246,0.15)",
    block_label_text_color="#a78bfa",
    block_label_text_color_dark="#a78bfa",
    block_title_text_color="#c4b5fd",
    block_title_text_color_dark="#c4b5fd",
    body_text_color="#e2e8f0",
    body_text_color_dark="#e2e8f0",
    body_text_color_subdued="#94a3b8",
    body_text_color_subdued_dark="#94a3b8",
    border_color_primary="rgba(139,92,246,0.2)",
    border_color_primary_dark="rgba(139,92,246,0.2)",
    input_background_fill="rgba(17,15,28,0.8)",
    input_background_fill_dark="rgba(17,15,28,0.8)",
    shadow_drop="0 4px 24px rgba(0,0,0,0.3)",
    shadow_drop_lg="0 8px 40px rgba(0,0,0,0.4)",
)


# ──────────────────────────────────────────────
# HELPER: HP bar label
# ──────────────────────────────────────────────
def hp_label(name: str, current: int, maximum: int) -> str:
    pct = int(current / maximum * 100)
    return f"{name}  ❤️ {current}/{maximum}  ({pct}%)"


def res_label(name: str, current: int, maximum: int) -> str:
    return f"{name}  🛡️ {current}/{maximum}"


# ──────────────────────────────────────────────
# BUILD THE LAYOUT
# ──────────────────────────────────────────────
with gr.Blocks(
    title="Mahoraga Adaptation Engine",
) as demo:

    # ── Title ──
    with gr.Column(elem_id="title-banner"):
        gr.Markdown("# ☸ Mahoraga Adaptation Engine")
        gr.Markdown("Meta RL Hackathon — Turn-Based Combat Dashboard")

    # ════════════════════════════════════════════
    # TOP ROW: HP Bars
    # ════════════════════════════════════════════
    with gr.Row(equal_height=True):
        # — Enemy HP —
        with gr.Column(scale=1, elem_classes=["panel-card"]):
            gr.Markdown("##### 👹 ENEMY", elem_classes=["section-label"])
            enemy_hp_bar = gr.Slider(
                minimum=0,
                maximum=MOCK_MAX_HP,
                value=MOCK_ENEMY_HP,
                label=hp_label("Enemy", MOCK_ENEMY_HP, MOCK_MAX_HP),
                interactive=False,
                elem_classes=["enemy-hp"],
            )

        # — Agent HP —
        with gr.Column(scale=1, elem_classes=["panel-card"]):
            gr.Markdown("##### ☸ MAHORAGA", elem_classes=["section-label"])
            agent_hp_bar = gr.Slider(
                minimum=0,
                maximum=MOCK_MAX_HP,
                value=MOCK_AGENT_HP,
                label=hp_label("Mahoraga", MOCK_AGENT_HP, MOCK_MAX_HP),
                interactive=False,
                elem_classes=["agent-hp"],
            )

    # ════════════════════════════════════════════
    # MID ROW: Resistances + Stats | Big Moments
    # ════════════════════════════════════════════
    with gr.Row(equal_height=True):

        # ── Left column: Resistances + Counters ──
        with gr.Column(scale=1):
            # Resistance panel
            with gr.Group(elem_classes=["panel-card"]):
                gr.Markdown("##### 🛡️ RESISTANCES", elem_classes=["section-label"])

                res_physical = gr.Slider(
                    minimum=0,
                    maximum=MOCK_RES_MAX,
                    value=MOCK_RES_PHYSICAL,
                    label=res_label("Physical", MOCK_RES_PHYSICAL, MOCK_RES_MAX),
                    interactive=False,
                    elem_classes=["res-physical"],
                )
                res_ce = gr.Slider(
                    minimum=0,
                    maximum=MOCK_RES_MAX,
                    value=MOCK_RES_CE,
                    label=res_label("CE", MOCK_RES_CE, MOCK_RES_MAX),
                    interactive=False,
                    elem_classes=["res-ce"],
                )
                res_technique = gr.Slider(
                    minimum=0,
                    maximum=MOCK_RES_MAX,
                    value=MOCK_RES_TECHNIQUE,
                    label=res_label("Technique", MOCK_RES_TECHNIQUE, MOCK_RES_MAX),
                    interactive=False,
                    elem_classes=["res-technique"],
                )

            # Stats panel
            with gr.Group(elem_classes=["panel-card"]):
                gr.Markdown("##### 📊 COUNTERS", elem_classes=["section-label"])
                with gr.Row():
                    adaptation_stack = gr.Textbox(
                        value=str(MOCK_ADAPTATION_STACK),
                        label="⚡ Adaptation Stack",
                        interactive=False,
                        elem_classes=["stat-pill"],
                    )
                    heal_cooldown = gr.Textbox(
                        value=str(MOCK_HEAL_COOLDOWN),
                        label="💚 Heal Cooldown",
                        interactive=False,
                        elem_classes=["stat-pill"],
                    )

        # ── Right column: Big Moments ──
        with gr.Column(scale=1):
            with gr.Group(elem_classes=["panel-card"]):
                gr.Markdown("##### 🌟 BIG MOMENTS", elem_classes=["section-label"])
                big_moments = gr.Markdown(
                    value=MOCK_BIG_MOMENT,
                    elem_id="big-moments",
                )

    # ════════════════════════════════════════════
    # BOTTOM ROW: Turn Log
    # ════════════════════════════════════════════
    with gr.Group(elem_classes=["panel-card"]):
        gr.Markdown("##### 📜 TURN LOG", elem_classes=["section-label"])
        turn_log = gr.Textbox(
            value=MOCK_TURN_LOG,
            label="",
            lines=18,
            max_lines=30,
            interactive=False,
            elem_id="turn-log",
            show_label=False,
        )

    # ── Footer info ──
    gr.Markdown(
        "<center style='color:#4a4a5a; font-size:0.7rem; padding:8px;'>"
        "Phase 1 · Static Layout · Mock Data · "
        "Awaiting Phase 2 state integration"
        "</center>"
    )


# ──────────────────────────────────────────────
# LAUNCH
# ──────────────────────────────────────────────
if __name__ == "__main__":
    demo.launch(theme=theme, css=CUSTOM_CSS)
