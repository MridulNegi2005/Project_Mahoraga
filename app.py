"""
Mahoraga Adaptation Engine — Aero-Tactical Dashboard
Inline CSS (no Tailwind CDN) for Gradio gr.HTML compatibility.
"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

import gradio as gr
from env.mahoraga_env import MahoragaEnv
from utils.constants import MAX_HP, ENEMY_HP

ACTION_NAMES = {0:"Adapt PHYSICAL", 1:"Adapt CE", 2:"Adapt TECHNIQUE",
                3:"Judgment Strike", 4:"Regeneration", None:"(Wasted Turn)"}
env = None
combat_log = []

# ── DESIGN TOKENS ──
BG = "#0b1120"
SURFACE = "#0f172a"
PANEL = "rgba(15,23,42,0.65)"
BORDER = "rgba(255,255,255,0.1)"
CYAN = "#00f6ff"
TEXT = "#f8fafc"
MUTED = "#94a3b8"
OUTLINE = "#475569"
RED = "#f87171"
DARK = "#020617"

def gp(extra=""):
    """Glass panel style"""
    return f"background:{PANEL};backdrop-filter:blur(12px);border:1px solid {BORDER};border-radius:8px;padding:24px;{extra}"

def label_s():
    return f"font-size:12px;font-weight:600;letter-spacing:0.05em;text-transform:uppercase;color:{MUTED};margin:0"

def mono_s(color=TEXT):
    return f"font-family:monospace;font-size:14px;font-weight:500;color:{color};margin:0"

def heading_s(size="24px"):
    return f"font-size:{size};font-weight:600;color:{TEXT};margin:0"

def res_badge(val):
    if val >= 80: return "IMMUNE", CYAN
    elif val >= 60: return f"{val}/80 HARDENED", CYAN
    elif val > 0: return f"{val}/80 MITIGATING", MUTED
    return "VULNERABLE", MUTED

def threat(pct):
    if pct < 40: return "CRITICAL", RED
    if pct < 70: return "HIGH", "#f59e0b"
    return "NOMINAL", CYAN

def log_html(entries):
    h = ""
    for e in reversed(entries[-10:]):
        lines = e.strip().split("\n")
        if not lines: continue
        tag = "LOG"
        tc = MUTED
        if "[ENEMY]" in lines[0]: tag, tc = "INCOMING ATTACK", RED
        elif "[MAHORAGA]" in lines[0]: tag, tc = "AGENT ACTION", CYAN
        elif "[RESULT]" in lines[0]: tag, tc = "RESULT", MUTED
        elif "[SYS]" in lines[0]: tag, tc = "SYSTEM", CYAN
        elif "TERMINATED" in lines[0] or "===" in lines[0]: tag, tc = "ENGAGEMENT END", RED
        body = "<br>".join(lines)
        h += f'''<div style="display:flex;gap:12px;padding:6px 0;border-left:1px solid rgba(51,65,85,0.3)">
          <div style="padding-left:12px">
            <div style="{label_s()}color:{tc}">{tag}</div>
            <div style="font-family:monospace;font-size:11px;color:{TEXT};white-space:pre-wrap;margin-top:4px">{body}</div>
          </div></div>'''
    return h


def render(ehp, ahp, rp, rc, rt, stk, cd, turn, rew, btitle, bdesc, status):
    ep = ehp/ENEMY_HP*100
    ap = ahp/MAX_HP*100
    ps, pc = res_badge(rp)
    cs, cc = res_badge(rc)
    ts, tc = res_badge(rt)
    tl, tlc = threat(ep)
    cdt = f"{cd} TURNS" if cd > 0 else "READY"
    sc = CYAN if "READY" in status or "ACTIVE" in status else RED
    lh = log_html(combat_log)

    return f'''
<div style="background:{BG};color:{TEXT};font-family:Inter,sans-serif;padding:24px;min-height:90vh">
<!-- HEADER -->
<div style="{gp('display:flex;justify-content:space-between;align-items:center;padding:12px 24px;margin-bottom:20px')}">
  <div>
    <div style="font-size:18px;font-weight:900;letter-spacing:-0.02em;color:{TEXT};text-transform:uppercase">AERO-TACTICAL</div>
    <div style="font-size:12px;color:{MUTED}">Mahoraga Adaptation Engine — Meta RL Hackathon</div>
  </div>
  <div style="background:{sc};color:#000;font-size:12px;font-weight:700;letter-spacing:0.05em;padding:8px 16px;border-radius:2px;text-transform:uppercase">{status}</div>
</div>

<!-- ROW 1: ENEMY + MAHORAGA -->
<div style="display:grid;grid-template-columns:2fr 1fr;gap:20px;margin-bottom:20px">
  <!-- ENEMY -->
  <div style="{gp()}">
    <div style="display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid rgba(51,65,85,0.3);padding-bottom:16px;margin-bottom:16px">
      <div style="{heading_s()}">🎯 Target Status: Enemy</div>
      <div style="{mono_s(OUTLINE)}">HP: {ehp}/{ENEMY_HP}</div>
    </div>
    <div style="display:flex;justify-content:space-between;margin-bottom:8px">
      <span style="{label_s()}">Structural Integrity</span>
      <span style="{mono_s()}">{ep:.1f}%</span>
    </div>
    <div style="width:100%;height:8px;background:#1e293b;border-radius:9999px;overflow:hidden;margin-bottom:20px">
      <div style="height:100%;width:{ep:.1f}%;background:{CYAN};border-radius:9999px;transition:width 0.5s"></div>
    </div>
    <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px">
      <div style="background:{SURFACE};padding:16px;border-radius:8px;border:1px solid rgba(51,65,85,0.2)">
        <div style="{label_s()}margin-bottom:8px">Turn</div>
        <div style="font-family:monospace;font-size:18px;color:{TEXT}">{turn}</div>
      </div>
      <div style="background:{SURFACE};padding:16px;border-radius:8px;border:1px solid rgba(51,65,85,0.2)">
        <div style="{label_s()}margin-bottom:8px">Last Reward</div>
        <div style="font-family:monospace;font-size:18px;color:{TEXT}">{rew}</div>
      </div>
      <div style="background:{SURFACE};padding:16px;border-radius:8px;border:1px solid rgba(51,65,85,0.2)">
        <div style="{label_s()}margin-bottom:8px">Threat Level</div>
        <div style="font-family:monospace;font-size:18px;font-weight:700;color:{tlc}">{tl}</div>
      </div>
    </div>
  </div>
  <!-- MAHORAGA -->
  <div style="{gp()}">
    <div style="border-bottom:1px solid rgba(51,65,85,0.3);padding-bottom:16px;margin-bottom:16px">
      <div style="{heading_s('18px')}">🧠 Core: Mahoraga</div>
    </div>
    <div style="display:flex;justify-content:space-between;margin-bottom:8px">
      <span style="{label_s()}">Integrity</span>
      <span style="{mono_s()}">{ap:.1f}% ({ahp}/{MAX_HP})</span>
    </div>
    <div style="width:100%;height:8px;background:#1e293b;border-radius:9999px;overflow:hidden;margin-bottom:16px">
      <div style="height:100%;width:{ap:.1f}%;background:{CYAN};border-radius:9999px;transition:width 0.5s"></div>
    </div>
    <div style="background:{SURFACE};padding:12px;border-radius:8px;border:1px solid rgba(51,65,85,0.2);display:flex;justify-content:space-between;margin-bottom:8px">
      <span style="{label_s()}">Adaptation Stack</span>
      <span style="{mono_s(CYAN)}font-weight:700">{stk}</span>
    </div>
    <div style="background:{SURFACE};padding:12px;border-radius:8px;border:1px solid rgba(51,65,85,0.2);display:flex;justify-content:space-between">
      <span style="{label_s()}">Heal Cooldown</span>
      <span style="{mono_s()}">{cdt}</span>
    </div>
  </div>
</div>

<!-- BIG MOMENTS -->
<div style="{gp('border-left:4px solid #1e293b;padding:32px;margin-bottom:20px;display:flex;justify-content:space-between;align-items:center;background:linear-gradient(to right,#0b1120,#020617)')}">
  <div>
    <div style="{label_s()}color:{CYAN};letter-spacing:0.1em;margin-bottom:8px">TACTICAL ANALYSIS UPDATE</div>
    <div style="font-size:36px;font-weight:700;color:{TEXT};letter-spacing:-0.02em;text-transform:uppercase;line-height:1.1">{btitle}</div>
    <div style="color:{MUTED};margin-top:12px;max-width:600px">{bdesc}</div>
  </div>
</div>

<!-- ROW 3: RESISTANCES + TURN LOG -->
<div style="display:grid;grid-template-columns:1fr 1fr;gap:20px">
  <!-- RESISTANCES -->
  <div style="{gp()}">
    <div style="border-bottom:1px solid rgba(51,65,85,0.3);padding-bottom:16px;margin-bottom:16px">
      <div style="{heading_s('18px')}">🛡️ Active Resistances</div>
    </div>
    <div style="display:flex;flex-direction:column;gap:8px">
      <div style="background:{SURFACE};padding:12px;border-radius:8px;border:1px solid rgba(51,65,85,0.2);display:flex;justify-content:space-between;align-items:center">
        <span style="color:{TEXT}">Physical</span>
        <span style="{label_s()}color:{pc};background:#1e293b;padding:4px 8px;border-radius:4px">{ps}</span>
      </div>
      <div style="background:{SURFACE};padding:12px;border-radius:8px;border:1px solid rgba(51,65,85,0.2);display:flex;justify-content:space-between;align-items:center">
        <span style="color:{TEXT}">Cursed Energy</span>
        <span style="{label_s()}color:{cc};background:#1e293b;padding:4px 8px;border-radius:4px">{cs}</span>
      </div>
      <div style="background:{SURFACE};padding:12px;border-radius:8px;border:1px solid rgba(51,65,85,0.2);display:flex;justify-content:space-between;align-items:center">
        <span style="color:{TEXT}">Technique</span>
        <span style="{label_s()}color:{tc};background:#1e293b;padding:4px 8px;border-radius:4px">{ts}</span>
      </div>
    </div>
  </div>
  <!-- TURN LOG -->
  <div style="{gp('max-height:320px;display:flex;flex-direction:column')}">
    <div style="border-bottom:1px solid rgba(51,65,85,0.3);padding-bottom:16px;margin-bottom:12px">
      <div style="{heading_s('18px')}">📋 Turn Log</div>
    </div>
    <div style="flex:1;overflow-y:auto">{lh}</div>
  </div>
</div>
</div>'''


def reset_env():
    global env, combat_log
    env = MahoragaEnv()
    env.reset()
    combat_log = ["[SYS] INITIALIZING ADAPTATION ENGINE..."]
    return render(ENEMY_HP, MAX_HP, 0, 0, 0, 0, 0, 0, "0.00",
                  "AWAITING ENGAGEMENT", "Surveillance feed initialized. Monitoring Subject Alpha engagement parameters.",
                  "SYSTEM READY")

def take_action(action_idx):
    global env, combat_log
    if env is None: return reset_env()
    state, reward, done, info = env.step(action_idx)
    an = ACTION_NAMES.get(env.last_action, "Unknown")
    e = f"[ENEMY] {state['last_enemy_subtype']} ({state['last_enemy_attack_type']}) -> {info['damage_taken']} DMG\n[MAHORAGA] {an}"
    if info.get("correct_adaptation"): e += " -> ADAPTATION MATCHED"
    if info.get("damage_dealt", 0) > 0: e += f" -> {info['damage_dealt']} DMG DEALT"
    if info.get("heal_on_cooldown"): e += " -> BLOCKED (COOLDOWN)"
    e += f"\n[RESULT] Reward: {reward:.2f} | Stack: {info['adaptation_stack']}"
    combat_log.append(e)
    if done:
        combat_log.append(f"ENGAGEMENT TERMINATED: {info.get('reason','Unknown')}\nFinal: Mahoraga {state['agent_hp']} HP | Enemy {state['enemy_hp']} HP")
    bt, bd = "COMBAT IN PROGRESS", "Monitoring real-time engagement telemetry."
    if done: bt, bd = info.get('reason','Unknown').upper(), f"Final: Mahoraga {state['agent_hp']} HP | Enemy {state['enemy_hp']} HP."
    elif action_idx == 3 and info.get("damage_dealt",0) > 0: bt, bd = "JUDGMENT STRIKE - EXECUTED", f"Decisive strike dealing {info['damage_dealt']} damage."
    elif info.get("correct_adaptation"): bt, bd = "ADAPTATION COMPLETE", f"Countermeasures developed for {state['last_enemy_attack_type']} attacks."
    st = "ACTIVE ENGAGEMENT" if not done else "ENGAGEMENT ENDED"
    return render(state["enemy_hp"], state["agent_hp"],
        state["resistances"]["physical"], state["resistances"]["ce"], state["resistances"]["technique"],
        info["adaptation_stack"], env.heal_cooldown_counter, state["turn_number"], f"{reward:.2f}", bt, bd, st)

CSS = """
.gradio-container { background: #0b1120 !important; }
footer { display: none !important; }
.action-btn button { background:rgba(15,23,42,0.65)!important;backdrop-filter:blur(8px)!important;border:1px solid rgba(255,255,255,0.1)!important;color:#f8fafc!important;border-radius:4px!important;font-weight:600!important;text-transform:uppercase!important;letter-spacing:0.05em!important;font-size:0.7rem!important;transition:all 0.2s!important }
.action-btn button:hover { background:rgba(30,41,59,0.8)!important;border-color:rgba(255,255,255,0.2)!important }
.btn-danger button { background:rgba(127,29,29,0.6)!important;border:1px solid rgba(248,113,113,0.3)!important;color:#fca5a5!important }
.btn-primary button { background:#0ea5e9!important;color:#020617!important;border:1px solid #0ea5e9!important }
.btn-reset button { background:transparent!important;border:1px solid rgba(71,85,105,0.5)!important;color:#94a3b8!important }
"""

with gr.Blocks(title="Mahoraga Adaptation Engine") as demo:
    dashboard = gr.HTML(value=reset_env())
    with gr.Row():
        b0 = gr.Button("Adapt Physical", elem_classes=["action-btn"])
        b1 = gr.Button("Adapt CE", elem_classes=["action-btn"])
        b2 = gr.Button("Adapt Technique", elem_classes=["action-btn"])
        b3 = gr.Button("Judgment Strike", elem_classes=["action-btn","btn-danger"])
        b4 = gr.Button("Regeneration", elem_classes=["action-btn","btn-primary"])
    with gr.Row():
        br = gr.Button("Reset Deployment", elem_classes=["action-btn","btn-reset"])
    b0.click(fn=lambda: take_action(0), outputs=dashboard)
    b1.click(fn=lambda: take_action(1), outputs=dashboard)
    b2.click(fn=lambda: take_action(2), outputs=dashboard)
    b3.click(fn=lambda: take_action(3), outputs=dashboard)
    b4.click(fn=lambda: take_action(4), outputs=dashboard)
    br.click(fn=reset_env, outputs=dashboard)

if __name__ == "__main__":
    demo.launch(share=False, css=CSS)
