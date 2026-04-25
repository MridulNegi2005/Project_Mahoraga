import { useState, useRef, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import "./index.css";

const API = "";

/* ── Small Wheel indicator ── */
function MiniWheel({ rotation, size = 48 }) {
  const s = 8, r = 18, inner = 7;
  const spokes = Array.from({ length: s }, (_, i) => {
    const a = (i * 360) / s - 90, rad = (a * Math.PI) / 180;
    return { x1: Math.cos(rad)*inner, y1: Math.sin(rad)*inner, x2: Math.cos(rad)*r, y2: Math.sin(rad)*r };
  });
  return (
    <motion.svg viewBox="-24 -24 48 48" width={size} height={size} animate={{ rotate: rotation }} transition={{ type:"spring", stiffness:30, damping:12, mass:2 }}>
      <circle cx="0" cy="0" r="22" fill="none" stroke="rgba(0,246,255,0.15)" strokeWidth="0.5"/>
      <circle cx="0" cy="0" r={r} fill="none" stroke="rgba(0,246,255,0.35)" strokeWidth="1"/>
      {spokes.map((s,i)=><line key={i} x1={s.x1} y1={s.y1} x2={s.x2} y2={s.y2} stroke="rgba(0,246,255,0.5)" strokeWidth="1.5" strokeLinecap="round"/>)}
      <circle cx="0" cy="0" r={inner} fill="rgba(0,246,255,0.08)" stroke="rgba(0,246,255,0.5)" strokeWidth="1"/>
      <circle cx="0" cy="0" r="3" fill="rgba(0,246,255,0.7)"/>
    </motion.svg>
  );
}

/* ── Battle Arena with attack animations ── */
function BattleArena({ lastLog, shakeEnemy, shakeMahoraga, adaptFlash }) {
  return (
    <div className="relative w-full h-full overflow-hidden rounded-xl" style={{ background:"linear-gradient(180deg, #0a0f1e 0%, #111827 40%, #1a1a2e 100%)" }}>
      {/* Grid floor lines */}
      <svg className="absolute inset-0 w-full h-full opacity-20">
        {Array.from({length:12},(_,i)=>{
          const y = 55 + i*5;
          const spread = 10 + i*8;
          return <line key={i} x1={`${50-spread}%`} y1={`${y}%`} x2={`${50+spread}%`} y2={`${y}%`} stroke="rgba(0,246,255,0.3)" strokeWidth="0.5"/>;
        })}
      </svg>

      {/* Enemy sprite (top-right area) */}
      <motion.div className="absolute" style={{ top:"12%", right:"18%" }}
        animate={shakeEnemy ? { x:[0,-8,8,-6,4,-2,0], y:[0,-2,3,-1,2,0,0] } : { x:0,y:0 }}
        transition={{ duration:0.4 }}
      >
        <div className="text-center">
          <div className="text-5xl mb-1" style={{ filter:"drop-shadow(0 0 20px rgba(248,113,113,0.5))" }}>👹</div>
          <div className="text-[9px] font-bold tracking-[0.15em] uppercase text-red/80 bg-bg/60 px-2 py-0.5 rounded backdrop-blur">ENEMY</div>
        </div>
      </motion.div>

      {/* Mahoraga sprite (bottom-left area) */}
      <motion.div className="absolute" style={{ bottom:"15%", left:"18%" }}
        animate={shakeMahoraga ? { x:[0,-6,6,-4,3,-1,0], y:[0,2,-3,1,-2,0,0] } : { x:0,y:0 }}
        transition={{ duration:0.4 }}
      >
        <div className="text-center">
          <div className="text-5xl mb-1" style={{ filter:"drop-shadow(0 0 20px rgba(0,246,255,0.5))" }}>⚙️</div>
          <div className="text-[9px] font-bold tracking-[0.15em] uppercase text-cyan/80 bg-bg/60 px-2 py-0.5 rounded backdrop-blur">MAHORAGA</div>
        </div>
      </motion.div>

      {/* Adaptation shield effect */}
      <AnimatePresence>
        {adaptFlash && (
          <motion.div className="absolute" style={{ bottom:"12%", left:"15%" }}
            initial={{ scale:0, opacity:0 }} animate={{ scale:1.5, opacity:[0,0.8,0] }} exit={{ opacity:0 }}
            transition={{ duration:0.7 }}
          >
            <div className="w-24 h-24 rounded-full border-2 border-cyan" style={{ boxShadow:"0 0 30px rgba(0,246,255,0.5), inset 0 0 20px rgba(0,246,255,0.2)" }}/>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Attack projectile: Enemy → Mahoraga */}
      <AnimatePresence>
        {lastLog && lastLog.damage_taken > 0 && shakeEnemy === false && shakeMahoraga && (
          <motion.div className="absolute w-4 h-4 rounded-full bg-red" style={{ boxShadow:"0 0 20px rgba(248,113,113,0.8), 0 0 40px rgba(248,113,113,0.4)", top:"25%", right:"25%" }}
            initial={{ x:0, y:0, scale:1 }}
            animate={{ x:"-200%", y:"180%", scale:[1,1.5,0.8] }}
            transition={{ duration:0.4, ease:"easeIn" }}
          />
        )}
      </AnimatePresence>

      {/* Attack projectile: Mahoraga → Enemy (Judgment/damage) */}
      <AnimatePresence>
        {lastLog && lastLog.damage_dealt > 0 && shakeEnemy && (
          <motion.div className="absolute w-5 h-5 rounded-full bg-cyan" style={{ boxShadow:"0 0 25px rgba(0,246,255,0.9), 0 0 50px rgba(0,246,255,0.5)", bottom:"25%", left:"25%" }}
            initial={{ x:0, y:0, scale:1 }}
            animate={{ x:"200%", y:"-180%", scale:[1,2,0.5] }}
            transition={{ duration:0.35, ease:"easeIn" }}
          />
        )}
      </AnimatePresence>

      {/* Turn indicator */}
      <div className="absolute top-3 left-1/2 -translate-x-1/2 text-[9px] font-bold tracking-[0.2em] uppercase text-muted/40">
        {lastLog ? `TURN ${lastLog.turn}` : "READY"}
      </div>

      {/* Damage numbers floating up */}
      <AnimatePresence>
        {lastLog && lastLog.damage_taken > 0 && (
          <motion.div className="absolute font-mono text-lg font-black text-red" style={{ bottom:"30%", left:"22%" }}
            initial={{ opacity:1, y:0 }} animate={{ opacity:0, y:-40 }} transition={{ duration:1 }} key={`dt-${lastLog.turn}`}
          >-{lastLog.damage_taken}</motion.div>
        )}
      </AnimatePresence>
      <AnimatePresence>
        {lastLog && lastLog.damage_dealt > 0 && (
          <motion.div className="absolute font-mono text-lg font-black text-cyan" style={{ top:"22%", right:"22%" }}
            initial={{ opacity:1, y:0 }} animate={{ opacity:0, y:-40 }} transition={{ duration:1 }} key={`dd-${lastLog.turn}`}
          >-{lastLog.damage_dealt}</motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

/* ── HP Bar ── */
function HpBar({ current, max, color }) {
  const pct = Math.max(0,(current/max)*100);
  const grad = color==="red" ? "linear-gradient(90deg,#991b1b,#dc2626,#f87171)" : "linear-gradient(90deg,#065f46,#059669,#34d399)";
  const glow = color==="red" ? "rgba(248,113,113,0.4)" : "rgba(52,211,153,0.4)";
  return (
    <div>
      <div className="flex justify-between mb-0.5">
        <span className="font-mono text-[10px] text-text font-bold">{current}<span className="text-muted">/{max}</span></span>
        <span className={`font-mono text-[10px] ${pct<30?"text-red":"text-muted"}`}>{pct.toFixed(0)}%</span>
      </div>
      <div className="w-full h-2.5 bg-panel/80 rounded-full overflow-hidden border border-border-dim">
        <motion.div className="h-full rounded-full" style={{ background:grad, boxShadow:`0 0 10px ${glow}` }}
          animate={{ width:`${pct}%` }} transition={{ type:"spring", stiffness:60, damping:14 }}/>
      </div>
    </div>
  );
}

/* ── Resistance mini ── */
function ResBar({ label, value, flashing }) {
  const pct=(value/80)*100;
  let tag,tc;
  if(value>=80){tag="IMMUNE";tc="text-cyan";}else if(value>=60){tag="HARD";tc="text-cyan";}else if(value>0){tag=`${value}`;tc="text-amber";}else{tag="—";tc="text-muted/40";}
  return (
    <motion.div className="flex items-center gap-1.5" animate={flashing?{backgroundColor:["rgba(0,246,255,0)","rgba(0,246,255,0.15)","rgba(0,246,255,0)"]}:{}} transition={{duration:0.5}} style={{borderRadius:4,padding:"2px 4px"}}>
      <span className="text-[8px] font-bold tracking-wider uppercase text-muted w-8 shrink-0">{label}</span>
      <div className="flex-1 h-1 bg-panel rounded-full overflow-hidden">
        <motion.div className="h-full rounded-full bg-cyan" animate={{width:`${pct}%`}} transition={{type:"spring",stiffness:100,damping:12}}/>
      </div>
      <span className={`text-[8px] font-bold w-10 text-right ${tc}`}>{tag}</span>
    </motion.div>
  );
}

/* ── Action button ── */
function Btn({ label, onClick, variant="default", disabled }) {
  const v = { default:"border-border-dim text-muted hover:text-text hover:border-cyan/30 hover:bg-cyan-dim", danger:"border-red/30 text-red hover:bg-red-dim", primary:"border-cyan/30 text-cyan hover:bg-cyan-dim", reset:"border-outline/40 text-muted/60 hover:text-muted" };
  return (
    <motion.button whileHover={{scale:1.05}} whileTap={{scale:0.93}} onClick={onClick} disabled={disabled}
      className={`px-3 py-2 rounded-lg border font-bold text-[9px] tracking-[0.06em] uppercase transition-all cursor-pointer disabled:opacity-25 disabled:cursor-not-allowed bg-surface/60 ${v[variant]}`}>
      {label}
    </motion.button>
  );
}

/* ── Judgment overlay ── */
function JudgmentOverlay({ show }) {
  return (
    <AnimatePresence>
      {show && (
        <motion.div className="fixed inset-0 z-[100] flex items-center justify-center pointer-events-none" initial={{opacity:0}} animate={{opacity:1}} exit={{opacity:0}}>
          <motion.div className="absolute inset-0 bg-white" initial={{opacity:0}} animate={{opacity:[0,0.9,0,0.5,0]}} transition={{duration:0.7}}/>
          <motion.div className="absolute inset-0" style={{background:"radial-gradient(circle,rgba(0,246,255,0.4) 0%,transparent 70%)"}} initial={{opacity:0}} animate={{opacity:[0,1,0]}} transition={{duration:1.5}}/>
          <motion.div className="relative z-10 text-center" initial={{scale:4,opacity:0}} animate={{scale:1,opacity:1}} exit={{scale:0.3,opacity:0}} transition={{type:"spring",stiffness:150,damping:10}}>
            <div className="text-5xl md:text-7xl font-black tracking-[-0.03em] text-white" style={{textShadow:"0 0 80px rgba(0,246,255,0.9), 0 0 40px rgba(0,246,255,0.6)"}}>JUDGMENT STRIKE</div>
            <motion.div className="text-base font-mono text-cyan mt-3 tracking-[0.25em] uppercase" initial={{opacity:0,y:15}} animate={{opacity:1,y:0}} transition={{delay:0.25}}>— stack consumed —</motion.div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

/* ═══════ MAIN APP ═══════ */
export default function App() {
  const [state, setState] = useState(null);
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [shakeClass, setShakeClass] = useState("");
  const [flashRes, setFlashRes] = useState(null);
  const [showJudgment, setShowJudgment] = useState(false);
  const [wheelRot, setWheelRot] = useState(0);
  const [shakeEnemy, setShakeEnemy] = useState(false);
  const [shakeMahoraga, setShakeMahoraga] = useState(false);
  const [adaptFlash, setAdaptFlash] = useState(false);
  const [lastLog, setLastLog] = useState(null);
  const logRef = useRef(null);
  const prevRes = useRef({Physical:0,CE:0,Technique:0});

  useEffect(()=>{ if(logRef.current) logRef.current.scrollTop=logRef.current.scrollHeight; },[logs]);

  const triggerShake = useCallback((heavy)=>{
    setShakeClass(heavy?"shake-heavy":"shake-sm");
    setTimeout(()=>setShakeClass(""),heavy?500:350);
  },[]);

  async function doReset(){
    setLoading(true);
    const r=await fetch(`${API}/api/reset`,{method:"POST"});
    const d=await r.json(); setState(d); setLogs([]); setLastLog(null);
    setWheelRot(0); prevRes.current={Physical:0,CE:0,Technique:0}; setLoading(false);
  }

  async function doStep(action){
    if(!state||state.done||loading) return;
    setLoading(true);
    const r=await fetch(`${API}/api/step`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({action})});
    const d=await r.json(); const log=d.turn_log;

    if(log){
      setLastLog(log);
      // Enemy attacks mahoraga — shake mahoraga sprite
      if(log.damage_taken>0){ setShakeMahoraga(true); setTimeout(()=>setShakeMahoraga(false),450); }
      // Mahoraga deals damage — shake enemy sprite
      if(log.damage_dealt>0){ setShakeEnemy(true); setTimeout(()=>setShakeEnemy(false),450); }
      // Screen shake on heavy hits
      if(log.damage_taken>150) triggerShake(true); else if(log.damage_taken>80) triggerShake(false);
      // Adaptation flash
      if(log.correct_adaptation){ setAdaptFlash(true); setTimeout(()=>setAdaptFlash(false),700); }
      // Wheel spin
      if(log.correct_adaptation) setWheelRot(p=>p+45);
      else if(log.mahoraga_action==="Judgment Strike"&&log.damage_dealt>0) setWheelRot(p=>p+180);
      else setWheelRot(p=>p+10);
      // Judgment overlay
      if(log.mahoraga_action==="Judgment Strike"&&log.damage_dealt>200){ setShowJudgment(true); triggerShake(true); setTimeout(()=>setShowJudgment(false),2000); }
    }

    // Resistance flash
    if(d.resistances){ const p=prevRes.current;
      for(const k of ["Physical","CE","Technique"]){ if(d.resistances[k]>p[k]){ setFlashRes(k); setTimeout(()=>setFlashRes(null),500); break; } }
      prevRes.current={...d.resistances};
    }

    if(log) setLogs(prev=>[...prev,log]);
    setState(d); setLoading(false);
  }

  useEffect(()=>{doReset();},[]);

  if(!state) return <div className="h-screen flex items-center justify-center bg-bg"><motion.div animate={{rotate:360}} transition={{repeat:Infinity,duration:2,ease:"linear"}} className="w-10 h-10 border-2 border-cyan border-t-transparent rounded-full"/></div>;

  const done=state.done;

  return (
    <>
      <JudgmentOverlay show={showJudgment}/>
      <div className={`h-screen flex flex-col bg-bg grid-bg scanlines relative overflow-hidden ${shakeClass}`}>

        {/* HEADER */}
        <header className="glass mx-2 mt-1.5 px-4 py-1.5 flex justify-between items-center z-10 shrink-0" style={{borderRadius:8}}>
          <div className="flex items-center gap-3">
            <span className="text-sm font-black tracking-[-0.02em] uppercase text-text">AERO-TACTICAL</span>
            <span className="text-[9px] text-muted tracking-wide hidden sm:inline">Mahoraga Adaptation Engine</span>
          </div>
          <div className="flex items-center gap-3">
            <span className="font-mono text-[10px] text-muted">T{state.turn_number}/{state.max_turns}</span>
            <span className={`text-[9px] font-bold tracking-[0.1em] uppercase px-2 py-1 rounded-md ${done?"bg-red-dim text-red border border-red/20":"bg-cyan-dim text-cyan border border-cyan/20"}`}>
              {done?state.done_reason||"ENDED":"LIVE"}
            </span>
          </div>
        </header>

        {/* MAIN: Left stats | Center arena | Right log */}
        <div className="flex-1 flex gap-2 px-2 py-1.5 min-h-0">

          {/* LEFT: Stats */}
          <div className="flex flex-col gap-1.5 w-[220px] shrink-0">
            <div className="glass p-2.5">
              <div className="text-[8px] font-bold tracking-[0.15em] uppercase text-red/70 mb-1.5">🎯 ENEMY</div>
              <HpBar current={state.enemy_hp} max={state.enemy_hp_max} color="red"/>
              <div className="flex gap-1.5 mt-1.5">
                <div className="flex-1 bg-surface/60 rounded p-1.5 border border-border-dim text-center">
                  <div className="text-[7px] font-bold tracking-wider uppercase text-muted">Threat</div>
                  <div className={`font-mono text-[10px] font-bold ${state.enemy_hp<400?"text-red":state.enemy_hp<700?"text-amber":"text-cyan"}`}>{state.enemy_hp<400?"CRIT":state.enemy_hp<700?"HIGH":"NOM"}</div>
                </div>
                <div className="flex-1 bg-surface/60 rounded p-1.5 border border-border-dim text-center">
                  <div className="text-[7px] font-bold tracking-wider uppercase text-muted">Phase</div>
                  <div className="font-mono text-[10px] font-bold text-text">{state.turn_number<=5?"I":state.turn_number<=15?"II":"III"}</div>
                </div>
              </div>
            </div>

            <div className="glass p-2.5">
              <div className="flex items-center gap-2 mb-1.5">
                <div className="text-[8px] font-bold tracking-[0.15em] uppercase text-green/70 flex-1">🧠 MAHORAGA</div>
                <MiniWheel rotation={wheelRot} size={28}/>
              </div>
              <HpBar current={state.mahoraga_hp} max={state.mahoraga_hp_max} color="green"/>
              <div className="flex gap-1.5 mt-1.5">
                <div className="flex-1 bg-surface/60 rounded p-1.5 border border-border-dim text-center">
                  <div className="text-[7px] font-bold tracking-wider uppercase text-muted">Stack</div>
                  <motion.div className="font-mono text-xs font-bold text-cyan" key={state.adaptation_stack} initial={{scale:1.5}} animate={{scale:1}}>{state.adaptation_stack}</motion.div>
                </div>
                <div className="flex-1 bg-surface/60 rounded p-1.5 border border-border-dim text-center">
                  <div className="text-[7px] font-bold tracking-wider uppercase text-muted">Heal</div>
                  <div className={`font-mono text-xs font-bold ${state.heal_cooldown===0?"text-green":"text-red"}`}>{state.heal_cooldown===0?"RDY":state.heal_cooldown}</div>
                </div>
              </div>
            </div>

            <div className="glass p-2.5 flex-1">
              <div className="text-[8px] font-bold tracking-[0.15em] uppercase text-muted mb-1.5">🛡️ RESISTANCES</div>
              <div className="space-y-1">
                <ResBar label="PHYS" value={state.resistances.Physical} flashing={flashRes==="Physical"}/>
                <ResBar label="CE" value={state.resistances.CE} flashing={flashRes==="CE"}/>
                <ResBar label="TECH" value={state.resistances.Technique} flashing={flashRes==="Technique"}/>
              </div>
            </div>
          </div>

          {/* CENTER: Battle Arena */}
          <div className="flex-1 flex flex-col gap-1.5 min-w-0">
            <div className="flex-1 glass p-1 overflow-hidden">
              <BattleArena lastLog={lastLog} shakeEnemy={shakeEnemy} shakeMahoraga={shakeMahoraga} adaptFlash={adaptFlash}/>
            </div>

            {/* Adaptation banner */}
            <AnimatePresence>
              {lastLog && lastLog.correct_adaptation && (
                <motion.div className="glass px-4 py-1.5 border-l-2 border-l-cyan flex items-center gap-3" initial={{opacity:0,x:-20}} animate={{opacity:1,x:0}} exit={{opacity:0}}>
                  <span className="text-[9px] font-bold tracking-[0.12em] uppercase text-cyan">ADAPTED</span>
                  <span className="text-xs font-black uppercase text-text">{lastLog.enemy_attack_type} COUNTERED</span>
                </motion.div>
              )}
            </AnimatePresence>

            {/* Actions + reward */}
            <div className="glass px-3 py-2 flex items-center gap-2 flex-wrap">
              <Btn label="Adapt Physical" onClick={()=>doStep(0)} disabled={done}/>
              <Btn label="Adapt CE" onClick={()=>doStep(1)} disabled={done}/>
              <Btn label="Adapt Technique" onClick={()=>doStep(2)} disabled={done}/>
              <Btn label="Judgment Strike" onClick={()=>doStep(3)} variant="danger" disabled={done}/>
              <Btn label="Regeneration" onClick={()=>doStep(4)} variant="primary" disabled={done}/>
              <Btn label="Reset" onClick={doReset} variant="reset"/>
              {lastLog && <motion.span key={state.turn_number} initial={{opacity:0,y:-8}} animate={{opacity:1,y:0}} className={`font-mono text-[10px] font-bold ml-auto ${lastLog.reward>0?"text-green":"text-red"}`}>{lastLog.reward>0?"+":""}{lastLog.reward}</motion.span>}
            </div>
          </div>

          {/* RIGHT: Log */}
          <div className="w-[260px] shrink-0 glass p-2.5 flex flex-col">
            <div className="text-[8px] font-bold tracking-[0.15em] uppercase text-muted mb-1.5">📋 COMBAT LOG</div>
            <div ref={logRef} className="flex-1 overflow-y-auto bg-bg/40 rounded-lg p-2 border border-border-dim min-h-0">
              {logs.length===0 ? <div className="font-mono text-[9px] text-muted/40 text-center py-6">{">"} AWAITING...</div> :
                logs.map((l,i)=>(
                  <motion.div key={i} initial={{opacity:0,x:-8}} animate={{opacity:1,x:0}} className="font-mono text-[9px] leading-[1.7] py-0.5 border-b border-border-dim/40 last:border-0">
                    <span className="text-cyan font-bold">T{l.turn}</span><span className="text-muted">: </span>
                    <span className="text-red">{l.enemy_subtype}</span><span className="text-muted"> → </span>
                    <span className="text-green">{l.mahoraga_action}</span><span className="text-muted"> | </span>
                    <span className="text-amber">{l.damage_dealt}d</span><span className="text-muted"> | </span>
                    <span className={l.correct_adaptation?"text-cyan font-bold":"text-red/50"}>{l.correct_adaptation?"✓":"✗"}</span>
                  </motion.div>
                ))
              }
            </div>
          </div>
        </div>

        {/* Done overlay */}
        <AnimatePresence>
          {done&&(<motion.div className="fixed inset-0 z-50 flex items-center justify-center bg-bg/85 backdrop-blur-sm" initial={{opacity:0}} animate={{opacity:1}} exit={{opacity:0}}>
            <motion.div className="glass p-8 text-center" initial={{scale:0.7,opacity:0}} animate={{scale:1,opacity:1}} transition={{type:"spring",stiffness:200}} style={{maxWidth:400}}>
              <div className="text-3xl font-black tracking-tight uppercase text-text mb-2">ENGAGEMENT OVER</div>
              <div className="text-sm text-muted mb-1">{state.done_reason}</div>
              <div className="font-mono text-[10px] text-muted mb-4">Enemy: {state.enemy_hp} HP | Mahoraga: {state.mahoraga_hp} HP | T{state.turn_number}</div>
              <Btn label="Deploy Again" onClick={doReset} variant="primary"/>
            </motion.div>
          </motion.div>)}
        </AnimatePresence>
      </div>
    </>
  );
}
