import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

import gradio as gr
from env.mahoraga_env import MahoragaEnv

ACTION_NAMES = {
    0: "Adapt PHYSICAL",
    1: "Adapt CE",
    2: "Adapt TECHNIQUE",
    3: "Judgment Strike",
    4: "Regeneration",
    None: "(Wasted Turn)"
}

# Global env instance
env = None
combat_log = []


def reset_env():
    """Reset environment and return initial UI state."""
    global env, combat_log
    env = MahoragaEnv()
    state = env.reset()
    combat_log = ["=== NEW EPISODE STARTED ===\n"]

    return (
        format_hp(state["agent_hp"], 1200),      # agent_hp
        format_hp(state["enemy_hp"], 1000),       # enemy_hp
        format_resistances(state["resistances"]), # resistances
        "0",                                       # stack
        "Ready",                                   # cooldown
        "\n".join(combat_log),                     # log
        "0.00",                                    # reward
        "0",                                       # turn
        gr.update(interactive=True),               # action buttons
    )


def take_action(action):
    """Execute one step and return updated UI state."""
    global env, combat_log

    if env is None:
        return reset_env()

    state, reward, done, info = env.step(action)

    # Build log entry
    entry = f"Turn {state['turn_number']}:\n"
    entry += f"  Enemy:\n"
    entry += f"    → {state['last_enemy_subtype']} ({state['last_enemy_attack_type']})\n"
    entry += f"  Mahoraga:\n"
    entry += f"    → {ACTION_NAMES.get(env.last_action, 'Unknown')}\n"
    entry += f"  Result:\n"
    entry += f"    → Damage: {info['damage_taken']} | "
    entry += f"Correct Adaptation: {'YES' if info.get('correct_adaptation') else 'NO'} | "
    entry += f"Stack: {info['adaptation_stack']}\n"
    entry += f"    → Reward: {reward:.2f}\n"

    if info.get("heal_on_cooldown"):
        entry += f"    ⚠️ HEAL BLOCKED (on cooldown)\n"

    if done:
        entry += f"\n{'='*40}\n"
        entry += f"EPISODE ENDED — {info.get('reason', 'Unknown')}\n"
        entry += f"Final: Agent {state['agent_hp']} HP | Enemy {state['enemy_hp']} HP\n"
        entry += f"{'='*40}\n"

    combat_log.append(entry)

    cooldown_text = f"{env.heal_cooldown_counter} turns" if env.heal_cooldown_counter > 0 else "Ready"

    return (
        format_hp(state["agent_hp"], 1200),
        format_hp(state["enemy_hp"], 1000),
        format_resistances(state["resistances"]),
        str(info["adaptation_stack"]),
        cooldown_text,
        "\n".join(combat_log),
        f"{reward:.2f}",
        str(state["turn_number"]),
        gr.update(interactive=not done),
    )


def format_hp(current, max_hp):
    """Format HP display."""
    pct = current / max_hp * 100
    return f"{current} / {max_hp}  ({pct:.0f}%)"


def format_resistances(res):
    """Format resistance display."""
    return f"Physical: {res['physical']}  |  CE: {res['ce']}  |  Technique: {res['technique']}"


# Build UI
with gr.Blocks(
    title="Project Mahoraga",
    theme=gr.themes.Soft(primary_hue="blue", secondary_hue="orange"),
    css="""
    .combat-log { font-family: monospace; font-size: 13px; }
    .stat-box { font-size: 16px; font-weight: bold; }
    """
) as demo:
    gr.Markdown("# ⚔️ Project Mahoraga — Combat Arena")
    gr.Markdown("*Adaptive RL Environment — Interactive UI*")

    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("### 🛡️ Mahoraga (Agent)")
            agent_hp = gr.Textbox(label="Agent HP", value="1200 / 1200  (100%)", interactive=False, elem_classes="stat-box")
            resistances = gr.Textbox(label="Resistances", value="Physical: 0  |  CE: 0  |  Technique: 0", interactive=False)
            stack = gr.Textbox(label="Adaptation Stack", value="0", interactive=False)
            cooldown = gr.Textbox(label="Heal Cooldown", value="Ready", interactive=False)

        with gr.Column(scale=1):
            gr.Markdown("### 👹 Enemy")
            enemy_hp = gr.Textbox(label="Enemy HP", value="1000 / 1000  (100%)", interactive=False, elem_classes="stat-box")
            turn = gr.Textbox(label="Turn", value="0", interactive=False)
            reward = gr.Textbox(label="Last Reward", value="0.00", interactive=False)

    gr.Markdown("### 🎮 Actions")
    with gr.Row():
        btn_adapt_phys = gr.Button("0: Adapt Physical", variant="secondary")
        btn_adapt_ce = gr.Button("1: Adapt CE", variant="secondary")
        btn_adapt_tech = gr.Button("2: Adapt Technique", variant="secondary")
        btn_judgment = gr.Button("3: Judgment Strike", variant="primary")
        btn_heal = gr.Button("4: Regeneration", variant="secondary")

    with gr.Row():
        btn_reset = gr.Button("🔄 Reset Episode", variant="stop")

    gr.Markdown("### 📜 Combat Log")
    log = gr.Textbox(label="", value="Press Reset to start.", lines=15, interactive=False, elem_classes="combat-log")

    # Outputs list (same order for all callbacks)
    outputs = [agent_hp, enemy_hp, resistances, stack, cooldown, log, reward, turn, btn_judgment]

    # Wire buttons
    btn_adapt_phys.click(fn=lambda: take_action(0), outputs=outputs)
    btn_adapt_ce.click(fn=lambda: take_action(1), outputs=outputs)
    btn_adapt_tech.click(fn=lambda: take_action(2), outputs=outputs)
    btn_judgment.click(fn=lambda: take_action(3), outputs=outputs)
    btn_heal.click(fn=lambda: take_action(4), outputs=outputs)
    btn_reset.click(fn=reset_env, outputs=outputs)

if __name__ == "__main__":
    demo.launch(share=False)
