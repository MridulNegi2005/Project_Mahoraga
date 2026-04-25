import { useState, useRef, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import "./index.css";

const API = "";

/* ═══════════════════════════════════════
   WHEEL OF MAHORAGA — SVG Component
   8-spoke dharma wheel that rotates on adaptation
   ═══════════════════════════════════════ */
function WheelOfMahoraga({ rotation, flashing }) {
  const spokes = 8;
  const r = 90;
  const inner = 25;
  const spokeLines = Array.from({ length: spokes }, (_, i) => {
    const angle = (i * 360) / spokes - 90;
    const rad = (angle * Math.PI) / 180;
    return {
      x1: Math.cos(rad) * inner,
      y1: Math.sin(rad) * inner,
      x2: Math.cos(rad) * r,
      y2: Math.sin(rad) * r,
    };
  });

  // Small decorative circles at spoke tips
  const tips = spokeLines.map((s) => ({ cx: s.x2, cy: s.y2 }));

  return (
    <div className={`relative ${flashing ? "wheel-flash" : "wheel-idle"}`}>
      <motion.svg
        viewBox="-110 -110 220 220"
        className="w-full h-full"
        animate={{ rotate: rotation }}
        transition={{ type: "spring", stiffness: 30, damping: 12, mass: 2 }}
      >
        {/* Outer ring */}
        <circle cx="0" cy="0" r="100" fill="none" stroke="rgba(0,246,255,0.15)" strokeWidth="1" />
        <circle cx="0" cy="0" r="95" fill="none" stroke="rgba(0,246,255,0.25)" strokeWidth="0.5" strokeDasharray="4 4" />
        <circle cx="0" cy="0" r={r} fill="none" stroke="rgba(0,246,255,0.4)" strokeWidth="1.5" />

        {/* Spokes */}
        {spokeLines.map((s, i) => (
          <line
            key={i}
            x1={s.x1} y1={s.y1} x2={s.x2} y2={s.y2}
            stroke="rgba(0,246,255,0.5)"
            strokeWidth="2"
            strokeLinecap="round"
          />
        ))}

        {/* Spoke tip circles */}
        {tips.map((t, i) => (
          <circle key={i} cx={t.cx} cy={t.cy} r="4" fill="rgba(0,246,255,0.3)" stroke="rgba(0,246,255,0.6)" strokeWidth="1" />
        ))}

        {/* Inner hub */}
        <circle cx="0" cy="0" r={inner} fill="rgba(0,246,255,0.08)" stroke="rgba(0,246,255,0.5)" strokeWidth="2" />
        <circle cx="0" cy="0" r="12" fill="rgba(0,246,255,0.15)" stroke="rgba(0,246,255,0.7)" strokeWidth="1.5" />
        <circle cx="0" cy="0" r="4" fill="rgba(0,246,255,0.8)" />

        {/* Decorative arcs between spokes */}
        {Array.from({ length: spokes }, (_, i) => {
          const a1 = (i * 360) / spokes - 90 + 8;
          const a2 = ((i + 1) * 360) / spokes - 90 - 8;
          const r2 = 70;
          const rad1 = (a1 * Math.PI) / 180;
          const rad2 = (a2 * Math.PI) / 180;
          const x1 = Math.cos(rad1) * r2;
          const y1 = Math.sin(rad1) * r2;
          const x2 = Math.cos(rad2) * r2;
          const y2 = Math.sin(rad2) * r2;
          return (
            <path
              key={`arc-${i}`}
              d={`M ${x1} ${y1} A ${r2} ${r2} 0 0 1 ${x2} ${y2}`}
              fill="none"
              stroke="rgba(0,246,255,0.2)"
              strokeWidth="1"
            />
          );
        })}
      </motion.svg>
    </div>
  );
}

/* ═══════════════════════════════════════
   HP BAR — Compact horizontal bar
   ═══════════════════════════════════════ */
function HpBar({ label, current, max, color }) {
  const pct = Math.max(0, (current / max) * 100);
  const isLow = pct < 30;
  const grad = color === "red"
    ? "linear-gradient(90deg, #991b1b, #dc2626, #f87171)"
    : "linear-gradient(90deg, #065f46, #059669, #34d399)";
  const glowColor = color === "red" ? "rgba(248,113,113,0.5)" : "rgba(52,211,153,0.5)";

  return (
    <div className="flex-1">
      <div className="flex justify-between items-baseline mb-1">
        <span className="text-[10px] font-bold tracking-[0.12em] uppercase text-muted">{label}</span>
        <span className={`font-mono text-xs font-bold ${isLow ? "text-red" : "text-text"}`}>{current}<span className="text-muted">/{max}</span></span>
      </div>
      <div className="w-full h-3 bg-panel/80 rounded-full overflow-hidden border border-border-dim">
        <motion.div
          className="h-full rounded-full"
          style={{ background: grad, boxShadow: `0 0 12px ${glowColor}` }}
          animate={{ width: `${pct}%` }}
          transition={{ type: "spring", stiffness: 60, damping: 14 }}
        />
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════
   RESISTANCE MINI-BAR
   ═══════════════════════════════════════ */
function ResBar({ label, value, flashing }) {
  const pct = (value / 80) * 100;
  let tag, tagC;
  if (value >= 80) { tag = "IMMUNE"; tagC = "text-cyan"; }
  else if (value >= 60) { tag = "HARD"; tagC = "text-cyan"; }
  else if (value > 0) { tag = `${value}`; tagC = "text-amber"; }
  else { tag = "VULN"; tagC = "text-red"; }

  return (
    <motion.div
      className="flex items-center gap-2"
      animate={flashing ? {
        backgroundColor: ["rgba(0,246,255,0)", "rgba(0,246,255,0.15)", "rgba(0,246,255,0)"],
      } : {}}
      transition={{ duration: 0.5 }}
      style={{ borderRadius: 6, padding: "4px 6px" }}
    >
      <span className="text-[9px] font-bold tracking-wider uppercase text-muted w-10 shrink-0">{label}</span>
      <div className="flex-1 h-1.5 bg-panel rounded-full overflow-hidden">
        <motion.div
          className="h-full rounded-full bg-cyan"
          animate={{ width: `${pct}%` }}
          transition={{ type: "spring", stiffness: 100, damping: 12 }}
        />
      </div>
      <span className={`text-[9px] font-bold tracking-wider w-10 text-right ${tagC}`}>{tag}</span>
    </motion.div>
  );
}

/* ═══════════════════════════════════════
   ACTION BUTTON
   ═══════════════════════════════════════ */
function Btn({ label, onClick, variant = "default", disabled, small }) {
  const v = {
    default: "border-border-dim text-muted hover:text-text hover:border-cyan/30 hover:bg-cyan-dim",
    danger: "border-red/30 text-red hover:bg-red-dim hover:border-red/50",
    primary: "border-cyan/30 text-cyan hover:bg-cyan-dim hover:border-cyan/50",
    reset: "border-outline/40 text-muted/60 hover:text-muted hover:border-outline",
  };

  return (
    <motion.button
      whileHover={{ scale: 1.05 }}
      whileTap={{ scale: 0.93 }}
      onClick={onClick}
      disabled={disabled}
      className={`${small ? "px-2 py-1.5 text-[9px]" : "px-3 py-2 text-[10px]"} rounded-lg border font-bold tracking-[0.08em] uppercase transition-all cursor-pointer disabled:opacity-25 disabled:cursor-not-allowed bg-surface/60 ${v[variant]}`}
    >
      {label}
    </motion.button>
  );
}

/* ═══════════════════════════════════════
   JUDGMENT STRIKE OVERLAY
   ═══════════════════════════════════════ */
function JudgmentOverlay({ show }) {
  return (
    <AnimatePresence>
      {show && (
        <motion.div className="fixed inset-0 z-[100] flex items-center justify-center pointer-events-none" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
          {/* Flash layers */}
          <motion.div className="absolute inset-0 bg-white" initial={{ opacity: 0 }} animate={{ opacity: [0, 0.9, 0, 0.5, 0] }} transition={{ duration: 0.7 }} />
          <motion.div className="absolute inset-0" style={{ background: "radial-gradient(circle, rgba(0,246,255,0.4) 0%, transparent 70%)" }} initial={{ opacity: 0 }} animate={{ opacity: [0, 1, 0] }} transition={{ duration: 1.5 }} />
          {/* Text */}
          <motion.div className="relative z-10 text-center" initial={{ scale: 4, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} exit={{ scale: 0.3, opacity: 0 }} transition={{ type: "spring", stiffness: 150, damping: 10 }}>
            <div className="text-5xl md:text-7xl font-black tracking-[-0.03em] text-white" style={{ textShadow: "0 0 80px rgba(0,246,255,0.9), 0 0 40px rgba(0,246,255,0.6)" }}>
              JUDGMENT STRIKE
            </div>
            <motion.div className="text-base md:text-lg font-mono text-cyan mt-3 tracking-[0.25em] uppercase" initial={{ opacity: 0, y: 15 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.25 }}>
              — stack consumed —
            </motion.div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}


/* ═══════════════════════════════════════════════════
   ████  MAIN APP  ████
   ═══════════════════════════════════════════════════ */
export default function App() {
  const [state, setState] = useState(null);
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [shakeClass, setShakeClass] = useState("");
  const [flashRes, setFlashRes] = useState(null);
  const [showJudgment, setShowJudgment] = useState(false);
  const [wheelRotation, setWheelRotation] = useState(0);
  const [wheelFlash, setWheelFlash] = useState(false);
  const logRef = useRef(null);
  const prevResRef = useRef({ Physical: 0, CE: 0, Technique: 0 });

  useEffect(() => {
    if (logRef.current) logRef.current.scrollTop = logRef.current.scrollHeight;
  }, [logs]);

  const triggerShake = useCallback((heavy) => {
    setShakeClass(heavy ? "shake-heavy" : "shake-sm");
    setTimeout(() => setShakeClass(""), heavy ? 500 : 350);
  }, []);

  const spinWheel = useCallback((degrees) => {
    setWheelFlash(true);
    setWheelRotation((prev) => prev + degrees);
    setTimeout(() => setWheelFlash(false), 800);
  }, []);

  async function doReset() {
    setLoading(true);
    const res = await fetch(`${API}/api/reset`, { method: "POST" });
    const data = await res.json();
    setState(data);
    setLogs([]);
    setWheelRotation(0);
    prevResRef.current = { Physical: 0, CE: 0, Technique: 0 };
    setLoading(false);
  }

  async function doStep(action) {
    if (!state || state.done || loading) return;
    setLoading(true);
    const res = await fetch(`${API}/api/step`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action }),
    });
    const data = await res.json();
    const log = data.turn_log;

    // ── Shake on damage ──
    if (log) {
      if (log.damage_taken > 150) triggerShake(true);
      else if (log.damage_taken > 50) triggerShake(false);
    }

    // ── Resistance flash ──
    if (data.resistances) {
      const prev = prevResRef.current;
      for (const key of ["Physical", "CE", "Technique"]) {
        if (data.resistances[key] > prev[key]) {
          setFlashRes(key);
          setTimeout(() => setFlashRes(null), 500);
          break;
        }
      }
      prevResRef.current = { ...data.resistances };
    }

    // ── Wheel spin logic ──
    if (log) {
      if (log.correct_adaptation) {
        spinWheel(45); // 1/8 turn per adaptation
      } else if (log.mahoraga_action === "Judgment Strike" && log.damage_dealt > 0) {
        spinWheel(180); // half turn on judgment
      } else if (log.mahoraga_action === "Regeneration") {
        spinWheel(22.5);
      } else {
        spinWheel(10); // small tick per turn
      }
    }

    // ── Judgment Strike overlay ──
    if (log && log.mahoraga_action === "Judgment Strike" && log.damage_dealt > 200) {
      setShowJudgment(true);
      triggerShake(true);
      setTimeout(() => setShowJudgment(false), 2000);
    }

    if (log) setLogs((prev) => [...prev, log]);
    setState(data);
    setLoading(false);
  }

  useEffect(() => { doReset(); }, []);

  if (!state) {
    return (
      <div className="h-screen flex items-center justify-center bg-bg">
        <motion.div animate={{ rotate: 360 }} transition={{ repeat: Infinity, duration: 2, ease: "linear" }} className="w-10 h-10 border-2 border-cyan border-t-transparent rounded-full" />
      </div>
    );
  }

  const done = state.done;

  return (
    <>
      <JudgmentOverlay show={showJudgment} />

      <div className={`h-screen flex flex-col bg-bg grid-bg scanlines relative overflow-hidden ${shakeClass}`}>

        {/* ── HEADER ── */}
        <header className="glass mx-3 mt-2 px-5 py-2 flex justify-between items-center z-10 shrink-0" style={{ borderRadius: 8 }}>
          <div className="flex items-center gap-3">
            <span className="text-sm font-black tracking-[-0.02em] uppercase text-text">AERO-TACTICAL</span>
            <span className="text-[9px] text-muted tracking-wide hidden sm:inline">Mahoraga Adaptation Engine</span>
          </div>
          <div className="flex items-center gap-3">
            <span className="font-mono text-[10px] text-muted">T{state.turn_number}/{state.max_turns}</span>
            <span className={`text-[9px] font-bold tracking-[0.1em] uppercase px-2.5 py-1 rounded-md ${done ? "bg-red-dim text-red border border-red/20" : "bg-cyan-dim text-cyan border border-cyan/20"}`}>
              {done ? state.done_reason || "ENDED" : "LIVE"}
            </span>
          </div>
        </header>

        {/* ── MAIN CONTENT — 3-column viewport-fit ── */}
        <div className="flex-1 flex gap-3 px-3 py-2 min-h-0">

          {/* ──── LEFT COLUMN: Enemy + Resistances ──── */}
          <div className="flex flex-col gap-2 w-[280px] shrink-0">
            {/* Enemy HP */}
            <div className="glass p-3">
              <div className="text-[9px] font-bold tracking-[0.15em] uppercase text-red/70 mb-2">🎯 TARGET: ENEMY</div>
              <HpBar label="" current={state.enemy_hp} max={state.enemy_hp_max} color="red" />
              <div className="flex gap-2 mt-2">
                <div className="flex-1 bg-surface/60 rounded-md p-2 border border-border-dim text-center">
                  <div className="text-[8px] font-bold tracking-wider uppercase text-muted">Threat</div>
                  <div className={`font-mono text-xs font-bold mt-0.5 ${state.enemy_hp < 400 ? "text-red" : state.enemy_hp < 700 ? "text-amber" : "text-cyan"}`}>
                    {state.enemy_hp < 400 ? "CRITICAL" : state.enemy_hp < 700 ? "HIGH" : "NOMINAL"}
                  </div>
                </div>
                <div className="flex-1 bg-surface/60 rounded-md p-2 border border-border-dim text-center">
                  <div className="text-[8px] font-bold tracking-wider uppercase text-muted">Phase</div>
                  <div className="font-mono text-xs font-bold text-text mt-0.5">
                    {state.turn_number <= 5 ? "I" : state.turn_number <= 15 ? "II" : "III"}
                  </div>
                </div>
              </div>
            </div>

            {/* Mahoraga HP */}
            <div className="glass p-3">
              <div className="text-[9px] font-bold tracking-[0.15em] uppercase text-green/70 mb-2">🧠 CORE: MAHORAGA</div>
              <HpBar label="" current={state.mahoraga_hp} max={state.mahoraga_hp_max} color="green" />
              <div className="flex gap-2 mt-2">
                <div className="flex-1 bg-surface/60 rounded-md p-2 border border-border-dim text-center">
                  <div className="text-[8px] font-bold tracking-wider uppercase text-muted">Stack</div>
                  <motion.div className="font-mono text-sm font-bold text-cyan mt-0.5" key={state.adaptation_stack} initial={{ scale: 1.5 }} animate={{ scale: 1 }}>
                    {state.adaptation_stack}
                  </motion.div>
                </div>
                <div className="flex-1 bg-surface/60 rounded-md p-2 border border-border-dim text-center">
                  <div className="text-[8px] font-bold tracking-wider uppercase text-muted">Heal CD</div>
                  <div className={`font-mono text-sm font-bold mt-0.5 ${state.heal_cooldown === 0 ? "text-green" : "text-red"}`}>
                    {state.heal_cooldown === 0 ? "RDY" : state.heal_cooldown}
                  </div>
                </div>
              </div>
            </div>

            {/* Resistances */}
            <div className="glass p-3 flex-1">
              <div className="text-[9px] font-bold tracking-[0.15em] uppercase text-muted mb-2">🛡️ RESISTANCES</div>
              <div className="space-y-1.5">
                <ResBar label="PHYS" value={state.resistances.Physical} flashing={flashRes === "Physical"} />
                <ResBar label="CE" value={state.resistances.CE} flashing={flashRes === "CE"} />
                <ResBar label="TECH" value={state.resistances.Technique} flashing={flashRes === "Technique"} />
              </div>
            </div>
          </div>

          {/* ──── CENTER COLUMN: Wheel + Actions ──── */}
          <div className="flex-1 flex flex-col items-center justify-center gap-3 min-w-0">
            {/* Wheel */}
            <div className="w-[260px] h-[260px] relative">
              <WheelOfMahoraga rotation={wheelRotation} flashing={wheelFlash} />
              {/* Center label overlay */}
              <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                <div className="text-center">
                  <div className="text-[8px] font-bold tracking-[0.2em] uppercase text-cyan/60">WHEEL OF</div>
                  <div className="text-[11px] font-black tracking-tight uppercase text-cyan">MAHORAGA</div>
                </div>
              </div>
            </div>

            {/* Big moment banner */}
            <AnimatePresence>
              {state.turn_log && state.turn_log.correct_adaptation && (
                <motion.div
                  className="glass px-5 py-2 border-l-2 border-l-cyan text-center"
                  initial={{ opacity: 0, scale: 0.8 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.8 }}
                  style={{ maxWidth: 350 }}
                >
                  <div className="text-[9px] font-bold tracking-[0.15em] uppercase text-cyan">ADAPTATION MATCHED</div>
                  <div className="text-sm font-black tracking-tight uppercase text-text mt-0.5">
                    {state.turn_log.enemy_attack_type} COUNTERED
                  </div>
                </motion.div>
              )}
            </AnimatePresence>

            {/* Action buttons */}
            <div className="flex flex-wrap justify-center gap-2 mt-1">
              <Btn label="Adapt Physical" onClick={() => doStep(0)} disabled={done} small />
              <Btn label="Adapt CE" onClick={() => doStep(1)} disabled={done} small />
              <Btn label="Adapt Technique" onClick={() => doStep(2)} disabled={done} small />
              <Btn label="Judgment Strike" onClick={() => doStep(3)} variant="danger" disabled={done} small />
              <Btn label="Regeneration" onClick={() => doStep(4)} variant="primary" disabled={done} small />
              <Btn label="Reset" onClick={doReset} variant="reset" small />
            </div>

            {/* Last reward */}
            {state.turn_log && (
              <motion.div
                key={state.turn_number}
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                className={`font-mono text-xs font-bold ${state.turn_log.reward > 0 ? "text-green" : "text-red"}`}
              >
                {state.turn_log.reward > 0 ? "+" : ""}{state.turn_log.reward} reward
              </motion.div>
            )}
          </div>

          {/* ──── RIGHT COLUMN: Combat Log ──── */}
          <div className="w-[340px] shrink-0 glass p-3 flex flex-col">
            <div className="text-[9px] font-bold tracking-[0.15em] uppercase text-muted mb-2">📋 COMBAT LOG</div>
            <div ref={logRef} className="flex-1 overflow-y-auto bg-bg/40 rounded-lg p-2 border border-border-dim min-h-0">
              {logs.length === 0 ? (
                <div className="font-mono text-[10px] text-muted/50 text-center py-8">{">"} AWAITING ENGAGEMENT...</div>
              ) : (
                logs.map((l, i) => (
                  <motion.div
                    key={i}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    className="font-mono text-[10px] leading-[1.6] py-1 border-b border-border-dim/50 last:border-0"
                  >
                    <span className="text-cyan font-bold">T{l.turn}</span>
                    <span className="text-muted">: </span>
                    <span className="text-red">{l.enemy_subtype}</span>
                    <span className="text-muted"> → </span>
                    <span className="text-green">{l.mahoraga_action}</span>
                    <span className="text-muted"> | </span>
                    <span className="text-amber">{l.damage_dealt}dmg</span>
                    <span className="text-muted"> | </span>
                    <span className={l.correct_adaptation ? "text-cyan font-bold" : "text-red/60"}>
                      {l.correct_adaptation ? "✓" : "✗"}
                    </span>
                    {l.heal_blocked && <span className="text-red ml-1">[CD]</span>}
                  </motion.div>
                ))
              )}
            </div>
          </div>
        </div>

        {/* ── DONE OVERLAY ── */}
        <AnimatePresence>
          {done && (
            <motion.div className="fixed inset-0 z-50 flex items-center justify-center bg-bg/85 backdrop-blur-sm" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
              <motion.div className="glass p-8 text-center" initial={{ scale: 0.7, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} transition={{ type: "spring", stiffness: 200 }} style={{ maxWidth: 420 }}>
                <div className="text-3xl font-black tracking-tight uppercase text-text mb-3">ENGAGEMENT OVER</div>
                <div className="text-sm text-muted mb-1">{state.done_reason}</div>
                <div className="font-mono text-[11px] text-muted mb-5">
                  Enemy: {state.enemy_hp} HP | Mahoraga: {state.mahoraga_hp} HP | Turns: {state.turn_number}
                </div>
                <Btn label="Deploy Again" onClick={doReset} variant="primary" />
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </>
  );
}
