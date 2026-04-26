import { useState, useRef, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import "./index.css";

const API = "";

/* ═══════════════════════════════════════════════════════
   SUBCOMPONENTS
   ═══════════════════════════════════════════════════════ */

/* ── HP Bar ── */
function HpBar({ current, max, color, label }) {
  const pct = Math.max(0, (current / max) * 100);
  const grad =
    color === "red"
      ? "linear-gradient(90deg,#991b1b,#dc2626,#f87171)"
      : "linear-gradient(90deg,#065f46,#059669,#34d399)";
  const glow =
    color === "red"
      ? "rgba(248,113,113,0.35)"
      : "rgba(52,211,153,0.35)";
  return (
    <div>
      <div className="flex justify-between mb-0.5">
        <span className="font-mono text-[10px] text-muted tracking-wider uppercase font-semibold">
          {label}
        </span>
        <span className="font-mono text-[10px] text-text font-bold">
          {current}
          <span className="text-muted">/{max}</span>
          <span className={`ml-1.5 ${pct < 30 ? "text-red" : "text-muted"}`}>
            {pct.toFixed(0)}%
          </span>
        </span>
      </div>
      <div className="w-full h-2 bg-surface-high/80 rounded-full overflow-hidden ghost-border">
        <motion.div
          className="h-full rounded-full"
          style={{ background: grad, boxShadow: `0 0 8px ${glow}` }}
          animate={{ width: `${pct}%` }}
          transition={{ type: "spring", stiffness: 60, damping: 14 }}
        />
      </div>
    </div>
  );
}

/* ── Resistance Row ── */
function ResBar({ label, icon, value, flashing }) {
  const pct = (value / 80) * 100;
  let tag, tc;
  if (value >= 80) { tag = "IMMUNE"; tc = "text-cyan"; }
  else if (value >= 60) { tag = "HARD"; tc = "text-cyan"; }
  else if (value > 0) { tag = `${value}`; tc = "text-amber"; }
  else { tag = "—"; tc = "text-muted/40"; }

  return (
    <motion.div
      className="flex items-center gap-2 p-2 bg-surface/60 rounded-lg ghost-border"
      animate={
        flashing
          ? { backgroundColor: ["rgba(0,246,255,0)", "rgba(0,246,255,0.12)", "rgba(0,246,255,0)"] }
          : {}
      }
      transition={{ duration: 0.5 }}
    >
      <span className="material-symbols-outlined text-outline text-sm">{icon}</span>
      <span className="text-[10px] font-bold tracking-wider uppercase text-muted w-20 shrink-0">
        {label}
      </span>
      <div className="flex-1 h-1.5 bg-surface-high rounded-full overflow-hidden">
        <motion.div
          className="h-full rounded-full bg-cyan"
          animate={{ width: `${pct}%` }}
          transition={{ type: "spring", stiffness: 100, damping: 12 }}
        />
      </div>
      <span className={`text-[10px] font-bold w-14 text-right font-mono ${tc}`}>{tag}</span>
    </motion.div>
  );
}

/* ── Action Button ── */
function Btn({ label, onClick, variant = "default", disabled }) {
  const styles = {
    default: "border-outline-variant/40 text-muted hover:text-text hover:border-cyan/30 hover:bg-cyan-dim",
    danger: "border-red/30 text-red hover:bg-red-dim",
    primary: "border-cyan/30 text-cyan hover:bg-cyan-dim",
    reset: "border-outline/30 text-muted/60 hover:text-muted",
  };
  return (
    <motion.button
      whileHover={{ scale: 1.04 }}
      whileTap={{ scale: 0.93 }}
      onClick={onClick}
      disabled={disabled}
      className={`px-3 py-1.5 rounded-md border font-bold text-[9px] tracking-[0.06em] uppercase transition-all cursor-pointer disabled:opacity-25 disabled:cursor-not-allowed bg-surface/60 ${styles[variant]}`}
    >
      {label}
    </motion.button>
  );
}

/* ── Judgment Overlay ── */
function JudgmentOverlay({ show }) {
  return (
    <AnimatePresence>
      {show && (
        <motion.div
          className="fixed inset-0 z-[100] flex items-center justify-center pointer-events-none"
          initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
        >
          <motion.div className="absolute inset-0 bg-white"
            initial={{ opacity: 0 }} animate={{ opacity: [0, 0.9, 0, 0.5, 0] }}
            transition={{ duration: 0.7 }} />
          <motion.div className="absolute inset-0"
            style={{ background: "radial-gradient(circle,rgba(0,246,255,0.4) 0%,transparent 70%)" }}
            initial={{ opacity: 0 }} animate={{ opacity: [0, 1, 0] }}
            transition={{ duration: 1.5 }} />
          <motion.div className="relative z-10 text-center"
            initial={{ scale: 4, opacity: 0 }} animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.3, opacity: 0 }} transition={{ type: "spring", stiffness: 150, damping: 10 }}
          >
            <div className="text-5xl md:text-7xl font-black tracking-[-0.03em] text-white"
              style={{ textShadow: "0 0 80px rgba(0,246,255,0.9), 0 0 40px rgba(0,246,255,0.6)" }}>
              JUDGMENT STRIKE
            </div>
            <motion.div className="text-base font-mono text-cyan mt-3 tracking-[0.25em] uppercase"
              initial={{ opacity: 0, y: 15 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.25 }}>
              — stack consumed —
            </motion.div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

/* ── Stat Chip (small inline metric) ── */
function StatChip({ label, value, color = "text-text" }) {
  return (
    <div className="bg-surface/60 rounded-md p-2 ghost-border text-center min-w-[70px]">
      <div className="text-[7px] font-bold tracking-wider uppercase text-muted mb-0.5">{label}</div>
      <div className={`font-mono text-xs font-bold ${color}`}>{value}</div>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════
   MAIN APP
   ═══════════════════════════════════════════════════════ */
/* ── Attack category colors ── */
const CAT_COLORS = {
  PHYSICAL: { text: "text-orange-400", bg: "bg-orange-500/15", border: "border-orange-500/30", hex: "#f97316" },
  CE: { text: "text-purple-400", bg: "bg-purple-500/15", border: "border-purple-500/30", hex: "#a855f7" },
  TECHNIQUE: { text: "text-teal-400", bg: "bg-teal-500/15", border: "border-teal-500/30", hex: "#06b6d4" },
};
const catColor = (type) => CAT_COLORS[type] || CAT_COLORS.PHYSICAL;

export default function App() {
  const [state, setState] = useState(null);
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [shakeClass, setShakeClass] = useState("");
  const [flashRes, setFlashRes] = useState(null);
  const [showJudgment, setShowJudgment] = useState(false);
  const [wheelRot, setWheelRot] = useState(0);
  const [adaptFlash, setAdaptFlash] = useState(false);
  const [lastLog, setLastLog] = useState(null);
  const [difficulty, setDifficulty] = useState("hard");
  const [autoPlay, setAutoPlay] = useState(false);
  const [modelStatus, setModelStatus] = useState(null);
  const logRef = useRef(null);
  const prevRes = useRef({ Physical: 0, CE: 0, Technique: 0 });
  const autoRef = useRef(null);

  useEffect(() => {
    if (logRef.current) logRef.current.scrollTop = logRef.current.scrollHeight;
  }, [logs]);

  const triggerShake = useCallback((heavy) => {
    setShakeClass(heavy ? "shake-heavy" : "shake-sm");
    setTimeout(() => setShakeClass(""), heavy ? 500 : 350);
  }, []);

  const MOCK_STATE = {
    enemy_hp: 856, enemy_hp_max: 2000,
    mahoraga_hp: 1400, mahoraga_hp_max: 1500,
    resistances: { Physical: 40, CE: 80, Technique: 15 },
    adaptation_stack: 3, heal_cooldown: 0,
    turn_number: 7, max_turns: 30,
    done: false, done_reason: null, turn_log: null,
    difficulty: "hard",
  };

  async function doReset(diff, clearLogs = true) {
    const d2use = diff || difficulty;
    setLoading(true);
    setAutoPlay(false);
    try {
      const r = await fetch(`${API}/api/reset`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ difficulty: d2use }),
      });
      const d = await r.json();
      setState(d);
    } catch {
      setState({ ...MOCK_STATE, difficulty: d2use });
    }
    if (clearLogs) { setLogs([]); setLastLog(null); }
    setWheelRot(0); prevRes.current = { Physical: 0, CE: 0, Technique: 0 };
    setLoading(false);
  }

  function processStepResult(d) {
    const log = d.turn_log;
    if (log) {
      setLastLog(log);
      if (log.damage_taken > 150) triggerShake(true);
      else if (log.damage_taken > 80) triggerShake(false);
      if (log.correct_adaptation) {
        setAdaptFlash(true);
        setTimeout(() => setAdaptFlash(false), 1200);
      }
      if (log.correct_adaptation) setWheelRot((p) => p + 45);
      else if (log.mahoraga_action === "Judgment Strike" && log.damage_dealt > 0)
        setWheelRot((p) => p + 180);
      else setWheelRot((p) => p + 10);
      if (log.mahoraga_action === "Judgment Strike" && log.damage_dealt > 200) {
        setShowJudgment(true);
        triggerShake(true);
        setTimeout(() => setShowJudgment(false), 2000);
      }
      setLogs((prev) => [...prev, log]);
    }
    if (d.resistances) {
      const p = prevRes.current;
      for (const k of ["Physical", "CE", "Technique"]) {
        if (d.resistances[k] > p[k]) {
          setFlashRes(k);
          setTimeout(() => setFlashRes(null), 500);
          break;
        }
      }
      prevRes.current = { ...d.resistances };
    }
    setState(d);
    setLoading(false);
  }

  async function doStep(action) {
    if (!state || state.done || loading) return;
    setLoading(true);
    try {
      const r = await fetch(`${API}/api/step`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ player_action: action }),
      });
      if (!r.ok) { setLoading(false); return; }
      const d = await r.json();
      processStepResult(d);
    } catch {
      setLoading(false);
    }
  }

  /* ── Auto-play timer ── */
  useEffect(() => {
    if (autoPlay && state && !state.done && !loading) {
      autoRef.current = setTimeout(async () => {
        try {
          const r = await fetch(`${API}/api/step`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ player_action: null })
          });
          if (!r.ok) { setAutoPlay(false); return; }
          const d = await r.json();
          processStepResult(d);
        } catch { setAutoPlay(false); }
      }, 1200);
    }
    return () => clearTimeout(autoRef.current);
  }, [autoPlay, state, loading]);

  /* ── Stop auto-play when game ends ── */
  useEffect(() => {
    if (state?.done) {
      setAutoPlay(false);
      // Auto-reset stats after 3 seconds, but keep combat logs
      const t = setTimeout(() => doReset(null, false), 3000);
      return () => clearTimeout(t);
    }
  }, [state?.done]);

  /* ── Check model status on mount ── */
  useEffect(() => {
    doReset();
    fetch(`${API}/api/model-status`).then(r => r.json()).then(setModelStatus).catch(() => {});
  }, []);

  /* ── Loading state ── */
  if (!state)
    return (
      <div className="h-screen flex items-center justify-center bg-bg">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ repeat: Infinity, duration: 2, ease: "linear" }}
          className="w-10 h-10 border-2 border-cyan border-t-transparent rounded-full"
        />
      </div>
    );

  const done = state.done;

  return (
    <>
      <JudgmentOverlay show={showJudgment} />

      <div className={`h-screen flex flex-col bg-bg grid-bg scanlines relative overflow-hidden ${shakeClass}`}>

        {/* ═══════ HEADER ═══════ */}
        <header className="glass-panel mx-2 mt-1.5 px-4 py-1.5 flex justify-between items-center z-10 shrink-0">
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-cyan animate-pulse" style={{ boxShadow: '0 0 8px rgba(0,246,255,0.6)' }} />
              <span className="text-sm font-black tracking-[0.04em] uppercase text-text">
                MAHORAGA
              </span>
            </div>
            <span className="text-[9px] text-muted tracking-wide hidden sm:inline">
              Adaptive Combat AI • RL + LLM Engine
            </span>
          </div>
          <div className="flex items-center gap-2">
            {autoPlay && (
              <span className="text-[8px] font-bold tracking-widest uppercase text-amber animate-pulse">
                ● AUTO-PLAY
              </span>
            )}
            <span className={`text-[8px] font-bold tracking-wider uppercase px-1.5 py-0.5 rounded ${
              difficulty === "easy" ? "bg-green/10 text-green border border-green/20"
              : difficulty === "medium" ? "bg-amber/10 text-amber border border-amber/20"
              : "bg-red/10 text-red border border-red/20"
            }`}>
              {difficulty}
            </span>
            <span className="font-mono text-[10px] text-muted">
              T{state.turn_number}/{state.max_turns}
            </span>
            <span
              className={`text-[9px] font-bold tracking-[0.1em] uppercase px-2 py-1 rounded-md ${
                done
                  ? "bg-red-dim text-red border border-red/20"
                  : "bg-cyan-dim text-cyan border border-cyan/20"
              }`}
            >
              {done ? state.done_reason || "ENDED" : "LIVE"}
            </span>
          </div>
        </header>

        {/* ═══════ MAIN BENTO GRID ═══════ */}
        <div className="flex-1 grid grid-cols-12 gap-2 px-2 py-1.5 min-h-0 overflow-hidden">

          {/* ── COL 1-5: Left Column (Boss + Player stacked) ── */}
          <div className="col-span-5 flex flex-col gap-2 min-h-0">

            {/* Boss: Mahoraga (LLM-powered adaptive enemy) */}
            <div className="glass-panel p-3 shrink-0 border-l-2 border-l-red/30">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <span className="material-symbols-outlined text-red/60 text-base">smart_toy</span>
                  <span className="text-[11px] font-black tracking-[0.08em] uppercase text-text">
                    MAHORAGA
                  </span>
                  <span className="text-[7px] font-bold tracking-wider uppercase px-1.5 py-0.5 rounded bg-red/10 text-red/60 border border-red/15">
                    LLM BOSS
                  </span>
                </div>
                <span className="text-[8px] font-mono text-muted/50">
                  {state.llm_raw ? 'AI THINKING...' : 'AWAITING'}
                </span>
              </div>
              <HpBar current={state.mahoraga_hp} max={state.mahoraga_hp_max} color="red" label="Boss Integrity" />
              <div className="flex gap-1.5 mt-2">
                <StatChip label="Adapt Stack" value={
                  <motion.span key={state.adaptation_stack} initial={{ scale: 1.5 }} animate={{ scale: 1 }}>
                    {state.adaptation_stack}
                  </motion.span>
                } color="text-cyan" />
                <StatChip
                  label="Heal CD"
                  value={state.heal_cooldown === 0 ? "RDY" : state.heal_cooldown}
                  color={state.heal_cooldown === 0 ? "text-green" : "text-red"}
                />
                <StatChip
                  label="Threat"
                  value={state.adaptation_stack >= 3 ? "MAX" : state.adaptation_stack >= 2 ? "HIGH" : "LOW"}
                  color={state.adaptation_stack >= 3 ? "text-red" : state.adaptation_stack >= 2 ? "text-amber" : "text-green"}
                />
              </div>
            </div>

            {/* Player Status (user-controlled, compact) */}
            <div className="glass-panel p-2.5 shrink-0">
              <div className="flex items-center justify-between mb-1.5">
                <div className="flex items-center gap-2">
                  <span className="material-symbols-outlined text-green/60 text-sm">person</span>
                  <span className="text-[10px] font-bold tracking-[0.12em] uppercase text-green/70">
                    CHALLENGER
                  </span>
                  <span className="text-[7px] font-bold tracking-wider uppercase px-1.5 py-0.5 rounded bg-green/10 text-green/60 border border-green/15">
                    YOU
                  </span>
                </div>
                <span className="font-mono text-[8px] text-muted/40">{difficulty.toUpperCase()} MODE</span>
              </div>
              <HpBar current={state.enemy_hp} max={state.enemy_hp_max} color="green" label="Your HP" />
            </div>

            {/* Resistances */}
            <div className="glass-panel p-3 flex-1 min-h-0 flex flex-col border-l-2 border-l-cyan/20">
              <div className="flex items-center gap-2 mb-2">
                <span className="material-symbols-outlined text-cyan/60 text-base">security</span>
                <span className="text-[10px] font-bold tracking-[0.12em] uppercase text-muted">
                  MAHORAGA RESISTANCES
                </span>
              </div>
              <div className="space-y-1.5">
                <ResBar label="Physical" icon="fitness_center" value={state.resistances?.Physical ?? 0} flashing={flashRes === "Physical"} />
                <ResBar label="Cursed Energy" icon="bolt" value={state.resistances?.CE ?? 0} flashing={flashRes === "CE"} />
                <ResBar label="Technique" icon="precision_manufacturing" value={state.resistances?.Technique ?? 0} flashing={flashRes === "Technique"} />
              </div>
            </div>
          </div>

          {/* ── COL 6-8: Center Column (Wheel + Phase + Tactics) ── */}
          <div className="col-span-3 flex flex-col gap-2 min-h-0">

            {/* Boss AI Phase */}
            <div className="glass-panel p-3 shrink-0 border-l-2 border-l-cyan/20">
              <div className="text-[8px] font-bold tracking-[0.2em] uppercase text-muted/50 mb-1.5">
                BOSS AI INTELLIGENCE PHASE
              </div>
              <div className="flex gap-1">
                {[
                  { n: "I", label: "TUTORIAL", desc: "Always Physical", active: state.turn_number <= 5 },
                  { n: "II", label: "PATTERN", desc: "Cycling + 15% RNG", active: state.turn_number > 5 && state.turn_number <= 15 },
                  { n: "III", label: "ADAPTIVE", desc: "Targets weakness", active: state.turn_number > 15 },
                ].map((ph) => (
                  <div
                    key={ph.n}
                    className={`flex-1 rounded-md p-1.5 text-center border transition-all ${
                      ph.active
                        ? "bg-cyan/10 border-cyan/30 shadow-[0_0_12px_rgba(0,246,255,0.15)]"
                        : "bg-surface/40 border-outline-variant/15 opacity-40"
                    }`}
                  >
                    <div className={`text-xs font-black ${ph.active ? "text-cyan" : "text-muted/40"}`}>
                      {ph.n}
                    </div>
                    <div className={`text-[6px] font-bold tracking-wider uppercase ${ph.active ? "text-text/70" : "text-muted/30"}`}>
                      {ph.label}
                    </div>
                  </div>
                ))}
              </div>
              {difficulty === "easy" && (
                <div className="text-[7px] text-green/60 font-mono mt-1 text-center">LOCKED TO PHASE I</div>
              )}
              {difficulty === "medium" && state.turn_number > 15 && (
                <div className="text-[7px] text-amber/60 font-mono mt-1 text-center">PHASE III DISABLED</div>
              )}
            </div>

            {/* Mahoraga Wheel Visualization */}
            <div className="glass-panel p-3 flex-1 flex flex-col items-center justify-center min-h-0 relative overflow-hidden">
              <div className="relative flex-1 flex items-center justify-center w-full min-h-0">
                <AnimatePresence>
                  {adaptFlash && (
                    <motion.div
                      className="absolute inset-0 flex items-center justify-center pointer-events-none"
                      initial={{ opacity: 1 }} exit={{ opacity: 0 }}
                    >
                      <div className="w-[70%] aspect-square rounded-full border-2 border-cyan/50 adapt-ring"
                        style={{ boxShadow: "0 0 30px rgba(0,246,255,0.3)" }} />
                    </motion.div>
                  )}
                </AnimatePresence>
                <motion.img
                  src="/mahoraga_wheel.svg"
                  alt="Mahoraga Wheel"
                  className="w-full max-w-[200px] aspect-square object-contain wheel-idle"
                  animate={{ rotate: wheelRot }}
                  transition={{ type: "spring", stiffness: 25, damping: 14, mass: 2.5 }}
                  draggable={false}
                />
              </div>
              {/* Compact wheel stats */}
              <div className="flex items-center justify-center gap-3 mt-1">
                <div className="font-mono text-[9px] text-muted">
                  Stack <span className="text-cyan font-bold">{state.adaptation_stack}</span>
                </div>
                <div className="w-px h-3 bg-outline-variant/20" />
                <div className="font-mono text-[9px] text-muted">
                  Rot <span className="text-cyan font-bold">{(wheelRot / 45).toFixed(0)}</span>
                </div>
              </div>
            </div>

            {/* Tactical Summary */}
            <div className="glass-panel p-2.5 shrink-0">
              <div className="text-[7px] font-bold tracking-[0.15em] uppercase text-muted/40 mb-1">YOUR LAST ATTACK</div>
              {lastLog ? (
                <div className="flex items-center gap-2">
                  <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded ${catColor(lastLog.enemy_attack_type).bg} ${catColor(lastLog.enemy_attack_type).text} border ${catColor(lastLog.enemy_attack_type).border}`}>
                    {lastLog.enemy_attack_type}
                  </span>
                  <span className="font-mono text-[9px] text-muted">{lastLog.enemy_subtype}</span>
                  <span className="font-mono text-[9px] text-red ml-auto">-{lastLog.damage_taken}</span>
                </div>
              ) : (
                <div className="text-[8px] text-muted/30 font-mono">NO DATA</div>
              )}
            </div>

            {/* Adaptation Banner */}
            <AnimatePresence mode="wait">
              {lastLog && lastLog.correct_adaptation ? (
                <motion.div
                  key="adapted"
                  className="glass-panel p-3 border-l-2 border-l-cyan shrink-0"
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: 20 }}
                >
                  <div className="flex items-center gap-2">
                    <span className="material-symbols-outlined text-cyan text-sm">published_with_changes</span>
                    <span className="text-[9px] font-bold tracking-[0.1em] uppercase text-cyan">MAHORAGA ADAPTED</span>
                  </div>
                  <div className="text-xs font-black uppercase text-text mt-0.5">
                    YOUR {lastLog.enemy_attack_type} WAS COUNTERED
                  </div>
                  <div className="text-[9px] text-muted mt-0.5">
                    Boss adapted to your attack type.
                  </div>
                </motion.div>
              ) : lastLog ? (
                <motion.div
                  key="not-adapted"
                  className="glass-panel p-3 border-l-2 border-l-outline shrink-0"
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: 20 }}
                >
                  <div className="flex items-center gap-2">
                    <span className="material-symbols-outlined text-muted text-sm">sync_problem</span>
                    <span className="text-[9px] font-bold tracking-[0.1em] uppercase text-muted">
                      MAHORAGA: {lastLog.mahoraga_action}
                    </span>
                  </div>
                  <div className="text-[10px] text-muted/60 mt-0.5 font-mono">
                    You dealt: <span className="text-green">{lastLog.damage_taken}</span>
                    · Boss dealt: <span className="text-red">{lastLog.damage_dealt}</span>
                  </div>
                </motion.div>
              ) : (
                <motion.div
                  key="idle"
                  className="glass-panel p-3 border-l-2 border-l-outline-variant/30 shrink-0"
                  initial={{ opacity: 0 }} animate={{ opacity: 1 }}
                >
                  <div className="text-[9px] text-muted/40 uppercase tracking-wider font-bold text-center">
                    Awaiting engagement...
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          {/* ── COL 9-12: Right Column (Combat Log) ── */}
          <div className="col-span-4 flex flex-col gap-2 min-h-0">
            <div className="glass-panel p-3 flex-1 flex flex-col min-h-0">
              <div className="flex items-center justify-between mb-2 shrink-0">
                <div className="flex items-center gap-2">
                  <span className="material-symbols-outlined text-outline text-base">list_alt</span>
                  <span className="text-[10px] font-bold tracking-[0.12em] uppercase text-muted">
                    COMBAT LOG
                  </span>
                </div>
                <span className="font-mono text-[9px] text-muted/40">{logs.length} events</span>
              </div>
              <div
                ref={logRef}
                className="flex-1 overflow-y-auto bg-bg/40 rounded-lg p-2 ghost-border min-h-0"
              >
                {logs.length === 0 ? (
                  <div className="font-mono text-[9px] text-muted/40 text-center py-8">
                    {">"} AWAITING COMBAT DATA...
                  </div>
                ) : (
                  logs.map((l, i) => (
                    <motion.div
                      key={i}
                      initial={{ opacity: 0, x: -8 }}
                      animate={{ opacity: 1, x: 0 }}
                      className="py-1.5 border-b border-outline-variant/15 last:border-0"
                    >
                      <div className="flex items-center gap-1.5 mb-1">
                        <span className="font-mono text-[9px] text-outline-variant shrink-0 w-6">T{l.turn}</span>
                        <div className="shrink-0" style={{ width: 4, height: 4, borderRadius: "50%", backgroundColor: catColor(l.enemy_attack_type).hex }} />
                        {l.correct_adaptation && (
                          <span className="material-symbols-outlined text-cyan text-[11px]">published_with_changes</span>
                        )}
                        <span className={`font-mono text-[9px] font-bold shrink-0 ml-auto ${l.reward > 0 ? "text-green" : "text-red/60"}`}>
                          {l.reward > 0 ? "+" : ""}{l.reward}
                        </span>
                      </div>
                      {/* Player action line */}
                      <div className="flex items-center gap-1.5 ml-7 mb-0.5">
                        <span className="text-[8px] font-bold tracking-wider uppercase text-green/80 w-8">YOU</span>
                        <span className="text-[9px] text-muted/40">→</span>
                        <span className={`text-[9px] font-bold px-1 py-0.5 rounded ${catColor(l.enemy_attack_type).bg} ${catColor(l.enemy_attack_type).text} border ${catColor(l.enemy_attack_type).border}`}>
                          {l.enemy_attack_type}
                        </span>
                        <span className="font-mono text-[8px] text-muted/50">{l.enemy_subtype}</span>
                        <span className="font-mono text-[9px] text-green ml-auto">-{l.damage_taken} to boss</span>
                      </div>
                      {/* Mahoraga response line */}
                      <div className="flex items-center gap-1.5 ml-7">
                        <span className="text-[8px] font-bold tracking-wider uppercase text-red/80 w-8">BOSS</span>
                        <span className="text-[9px] text-muted/40">→</span>
                        <span className="text-[9px] font-bold text-text/80">{l.mahoraga_action}</span>
                        {l.correct_adaptation && <span className="text-[8px] text-cyan font-bold">ADAPTED!</span>}
                        {l.damage_dealt > 0 && <span className="font-mono text-[9px] text-red ml-auto">-{l.damage_dealt} to you</span>}
                      </div>
                    </motion.div>
                  ))
                )}
              </div>
            </div>
          </div>
        </div>

        {/* ═══════ BOTTOM ACTION BAR ═══════ */}
        <div className="glass-panel mx-2 mb-1.5 px-4 py-2 flex items-center gap-2 flex-wrap z-10 shrink-0">
          {/* Difficulty selector */}
          {["easy", "medium", "hard"].map((d) => (
            <motion.button
              key={d}
              whileTap={{ scale: 0.9 }}
              onClick={() => { setDifficulty(d); doReset(d); }}
              className={`px-2 py-1 rounded-md text-[8px] font-bold tracking-wider uppercase border cursor-pointer transition-all ${
                difficulty === d
                  ? d === "easy" ? "bg-green/15 text-green border-green/40"
                    : d === "medium" ? "bg-amber/15 text-amber border-amber/40"
                    : "bg-red/15 text-red border-red/40"
                  : "bg-surface/40 text-muted/50 border-outline-variant/20 hover:text-muted"
              }`}
            >
              {d === "medium" ? "MED" : d}
            </motion.button>
          ))}

          <div className="w-px h-5 bg-outline-variant/20 mx-0.5" />

          {/* Manual player attacks */}
          <Btn label="⚔ Physical" onClick={() => doStep("PHYSICAL")} disabled={done || autoPlay} />
          <Btn label="⚔ Cursed Energy" onClick={() => doStep("CE")} disabled={done || autoPlay} />
          <Btn label="⚔ Technique" onClick={() => doStep("TECHNIQUE")} disabled={done || autoPlay} />
          <div className="w-px h-5 bg-outline-variant/20 mx-0.5" />

          {/* Auto-play + Reset */}
          <motion.button
            whileTap={{ scale: 0.9 }}
            onClick={() => setAutoPlay(!autoPlay)}
            disabled={done}
            className={`px-3 py-1.5 rounded-md text-[9px] font-bold tracking-wider uppercase border cursor-pointer transition-all disabled:opacity-25 disabled:cursor-not-allowed ${
              autoPlay
                ? "bg-amber/20 text-amber border-amber/40 animate-pulse"
                : "bg-surface/60 text-muted border-outline-variant/30 hover:text-cyan hover:border-cyan/30"
            }`}
          >
            {autoPlay ? "⏸ STOP AUTO" : "▶ AUTO-PLAY"}
          </motion.button>
          <Btn label="Reset" onClick={() => doReset()} variant="reset" />

          {/* Reward indicator */}
          {lastLog && (
            <motion.span
              key={state.turn_number}
              initial={{ opacity: 0, y: -8 }}
              animate={{ opacity: 1, y: 0 }}
              className={`font-mono text-[10px] font-bold ml-auto ${lastLog.reward > 0 ? "text-green" : "text-red"}`}
            >
              {lastLog.reward > 0 ? "+" : ""}
              {lastLog.reward}
            </motion.span>
          )}
        </div>

        {/* ═══════ DONE OVERLAY ═══════ */}
        <AnimatePresence>
          {done && (
            <motion.div
              className="fixed inset-0 z-50 flex items-center justify-center bg-bg/85 backdrop-blur-sm"
              initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            >
              <motion.div
                className="glass-panel p-8 text-center"
                initial={{ scale: 0.7, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                transition={{ type: "spring", stiffness: 200 }}
                style={{ maxWidth: 420 }}
              >
                <div className="text-3xl font-black tracking-tight uppercase text-text mb-2">
                  ENGAGEMENT OVER
                </div>
                <div className="text-sm text-muted mb-1">{state.done_reason}</div>
                <div className="font-mono text-[10px] text-muted mb-5">
                  You: {state.enemy_hp} HP | Mahoraga (Boss): {state.mahoraga_hp} HP | T{state.turn_number}
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
