import React, { useState } from 'react';
import { Activity, Flame, Zap, Gauge, AlertTriangle, ShieldCheck } from 'lucide-react';

export default function DigitalTwinMotor({ telemetry, activeFault }) {
  const [hoveredPart, setHoveredPart] = useState(null);

  const faultType = activeFault?.fault_type || 'normal';
  const isBearingFault = faultType === 'bearing_degradation';
  const isOverheating = faultType === 'motor_overheating';
  const isOverload = faultType === 'motor_overload';
  const isVibration = faultType === 'excessive_vibration';
  const isLowPressure = faultType === 'low_pressure';
  const isHealthy = !activeFault;

  const rpm = telemetry?.rpm || 1485;
  const temp = telemetry?.temperature || 52.0;
  const vib = telemetry?.vibration || 1.4;
  const curr = telemetry?.current || 8.8;

  // Spin speed animation duration based on RPM (faster rpm = shorter duration)
  const animDuration = Math.max(0.2, (60 / Math.max(100, rpm)).toFixed(2));

  return (
    <div className="relative p-6 rounded-2xl bg-gradient-to-b from-slate-900 via-slate-900 to-slate-950 border border-slate-800 shadow-xl overflow-hidden">
      {/* Background Grid Pattern */}
      <div className="absolute inset-0 opacity-10 pointer-events-none bg-[radial-gradient(#38bdf8_1px,transparent_1px)] [background-size:16px_16px]"></div>

      {/* Header */}
      <div className="flex justify-between items-center mb-4 relative z-10">
        <div>
          <span className="text-[10px] font-mono font-bold tracking-widest text-sky-400 uppercase">
            PHYSICAL DIGITAL TWIN • 11 kW MOTOR
          </span>
          <h3 className="text-base font-bold text-slate-100 flex items-center gap-2">
            Stator & Drive Train Cross-Section
            {isHealthy ? (
              <span className="flex items-center gap-1 text-[11px] font-mono text-emerald-400 bg-emerald-950/80 px-2 py-0.5 rounded border border-emerald-800/80">
                <ShieldCheck className="w-3.5 h-3.5" /> NOMINAL ALIGNMENT
              </span>
            ) : (
              <span className="flex items-center gap-1 text-[11px] font-mono text-rose-400 bg-rose-950/80 px-2 py-0.5 rounded border border-rose-800/80 animate-pulse">
                <AlertTriangle className="w-3.5 h-3.5" /> FAULT LOCALIZED: {faultType.replace('_', ' ').toUpperCase()}
              </span>
            )}
          </h3>
        </div>

        {/* Hover Inspector Tooltip */}
        <div className="text-right text-xs">
          <span className="text-slate-500 font-mono">Component Focus:</span>
          <div className="font-semibold text-sky-300">
            {hoveredPart || 'Hover over components to inspect specs'}
          </div>
        </div>
      </div>

      {/* Main SVG Schematic */}
      <div className="relative flex justify-center items-center py-4">
        <svg
          viewBox="0 0 760 300"
          className="w-full max-w-3xl h-auto select-none filter drop-shadow-md"
        >
          <defs>
            {/* Gradients */}
            <linearGradient id="statorGrad" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor="#334155" />
              <stop offset="50%" stopColor="#1e293b" />
              <stop offset="100%" stopColor="#0f172a" />
            </linearGradient>

            <linearGradient id="heatGlow" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#ef4444" stopOpacity="0.8" />
              <stop offset="50%" stopColor="#f59e0b" stopOpacity="0.9" />
              <stop offset="100%" stopColor="#ef4444" stopOpacity="0.8" />
            </linearGradient>

            <linearGradient id="shaftGrad" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor="#94a3b8" />
              <stop offset="50%" stopColor="#cbd5e1" />
              <stop offset="100%" stopColor="#64748b" />
            </linearGradient>

            <filter id="glowEffect" x="-20%" y="-20%" width="140%" height="140%">
              <feGaussianBlur stdDeviation="4" result="blur" />
              <feComposite in="SourceGraphic" in2="blur" operator="over" />
            </filter>
          </defs>

          {/* 1. Base Mounting Bedplate */}
          <rect
            x="140"
            y="240"
            width="420"
            height="24"
            rx="4"
            fill="#1e293b"
            stroke="#475569"
            strokeWidth="2"
            onMouseEnter={() => setHoveredPart('Rigid Cast Iron Mounting Bedplate (Torque: 85 Nm)')}
            onMouseLeave={() => setHoveredPart(null)}
          />
          {/* Foundation Anchor Bolts */}
          <circle cx="170" cy="252" r="5" fill="#64748b" />
          <circle cx="530" cy="252" r="5" fill="#64748b" />

          {/* Vibration looseness waves if excessive_vibration */}
          {isVibration && (
            <g className="animate-pulse">
              <path d="M 120 264 Q 140 274 160 264 T 200 264" fill="none" stroke="#ef4444" strokeWidth="2.5" />
              <path d="M 500 264 Q 520 274 540 264 T 580 264" fill="none" stroke="#ef4444" strokeWidth="2.5" />
            </g>
          )}

          {/* 2. Main Stator Housing (Cooling Fins Body) */}
          <rect
            x="200"
            y="60"
            width="300"
            height="170"
            rx="12"
            fill={isOverheating ? "url(#heatGlow)" : "url(#statorGrad)"}
            stroke={isOverheating ? "#ef4444" : (isOverload ? "#38bdf8" : "#475569")}
            strokeWidth={isOverheating || isOverload ? "3.5" : "2"}
            filter={isOverheating ? "url(#glowEffect)" : undefined}
            className="transition-all duration-700 cursor-pointer"
            onMouseEnter={() => setHoveredPart(`Stator Stamping Core & Class F Winding (${temp}°C)`)}
            onMouseLeave={() => setHoveredPart(null)}
          />

          {/* Stator Heat Dissipation Fins Lines */}
          {[80, 100, 120, 140, 160, 180, 200].map((yPos, i) => (
            <line
              key={i}
              x1="205"
              y1={yPos}
              x2="495"
              y2={yPos}
              stroke={isOverheating ? "#fed7aa" : "#334155"}
              strokeWidth="2"
              strokeDasharray="4 2"
            />
          ))}

          {/* Overheating Heat Waves */}
          {isOverheating && (
            <g className="animate-bounce" style={{ animationDuration: '1.2s' }}>
              <path d="M 230 48 Q 240 35 250 48 T 270 48" fill="none" stroke="#f97316" strokeWidth="2.5" />
              <path d="M 330 48 Q 340 35 350 48 T 370 48" fill="none" stroke="#f97316" strokeWidth="2.5" />
              <path d="M 430 48 Q 440 35 450 48 T 470 48" fill="none" stroke="#f97316" strokeWidth="2.5" />
            </g>
          )}

          {/* Overload Electric Arcs / Current Flux */}
          {isOverload && (
            <g className="animate-pulse">
              <rect x="220" y="80" width="260" height="130" fill="none" stroke="#38bdf8" strokeWidth="2" strokeDasharray="6 4" />
              <text x="350" y="150" fill="#38bdf8" fontSize="11" fontFamily="monospace" textAnchor="middle" fontWeight="bold">
                HIGH CURRENT SLIP: {curr} A
              </text>
            </g>
          )}

          {/* 3. Terminal Box (Top of Motor) */}
          <rect
            x="310"
            y="26"
            width="80"
            height="36"
            rx="4"
            fill="#1e293b"
            stroke="#64748b"
            strokeWidth="1.5"
            onMouseEnter={() => setHoveredPart('IP55 Terminal Box - 400V 3-Phase Delta Connection')}
            onMouseLeave={() => setHoveredPart(null)}
          />
          <circle cx="350" cy="44" r="7" fill="#0284c7" />
          <line x1="345" y1="44" x2="355" y2="44" stroke="#fff" strokeWidth="2" />
          <line x1="350" y1="39" x2="350" y2="49" stroke="#fff" strokeWidth="2" />

          {/* 4. Drive Shaft (Through-center) */}
          <rect
            x="80"
            y="132"
            width="600"
            height="26"
            rx="3"
            fill="url(#shaftGrad)"
            stroke="#475569"
            strokeWidth="1.5"
            onMouseEnter={() => setHoveredPart(`High-Tensile Alloy Steel Rotor Shaft (Speed: ${rpm} RPM)`)}
            onMouseLeave={() => setHoveredPart(null)}
          />
          {/* Keyway Slot on Drive Output */}
          <rect x="620" y="140" width="40" height="6" fill="#334155" />

          {/* 5. Non-Drive-End (NDE) Bearing & Cooling Fan Cowl (Left) */}
          {/* Fan Cowl */}
          <path
            d="M 140 70 L 200 70 L 200 220 L 140 220 Q 120 145 140 70 Z"
            fill="#1e293b"
            stroke="#475569"
            strokeWidth="2"
            onMouseEnter={() => setHoveredPart('Non-Drive End Protective Cowl & External Blower')}
            onMouseLeave={() => setHoveredPart(null)}
          />
          {/* Fan Impeller Blades */}
          <g transform="translate(160, 145)">
            <circle cx="0" cy="0" r="28" fill="none" stroke="#64748b" strokeWidth="1" strokeDasharray="3 3" />
            <path
              d="M -18 -18 L 18 18 M -18 18 L 18 -18"
              stroke="#38bdf8"
              strokeWidth="4"
              strokeLinecap="round"
              className="origin-center"
              style={{
                animation: `spin ${animDuration}s linear infinite`,
                transformOrigin: '160px 145px'
              }}
            />
          </g>

          {/* 6. Drive-End (DE) Bearing Housing (Right) */}
          <g
            className="cursor-pointer"
            onMouseEnter={() => setHoveredPart(`Drive-End Deep Groove Ball Bearing (SKF 6308-2Z | Vib: ${vib} mm/s)`)}
            onMouseLeave={() => setHoveredPart(null)}
          >
            {/* Bearing Cap */}
            <rect
              x="500"
              y="90"
              width="50"
              height="110"
              rx="6"
              fill={isBearingFault ? "#7f1d1d" : "#334155"}
              stroke={isBearingFault ? "#ef4444" : "#64748b"}
              strokeWidth={isBearingFault ? "3" : "1.5"}
              filter={isBearingFault ? "url(#glowEffect)" : undefined}
            />

            {/* Rolling Elements (Balls) */}
            <circle cx="525" cy="115" r="7" fill={isBearingFault ? "#f87171" : "#94a3b8"} />
            <circle cx="525" cy="145" r="7" fill={isBearingFault ? "#f87171" : "#94a3b8"} />
            <circle cx="525" cy="175" r="7" fill={isBearingFault ? "#f87171" : "#94a3b8"} />

            {/* Bearing Fault Shockwave Animation */}
            {isBearingFault && (
              <g className="animate-ping" style={{ transformOrigin: '525px 145px' }}>
                <circle cx="525" cy="145" r="28" fill="none" stroke="#ef4444" strokeWidth="2.5" />
                <circle cx="525" cy="145" r="42" fill="none" stroke="#f59e0b" strokeWidth="1.5" />
              </g>
            )}
          </g>

          {/* 7. Auxiliary Cooling / Lubrication Line (Bottom Pipe) */}
          <path
            d="M 230 236 L 230 250 L 480 250 L 480 236"
            fill="none"
            stroke={isLowPressure ? "#ef4444" : "#0284c7"}
            strokeWidth="3.5"
            strokeDasharray={isLowPressure ? "5 3" : undefined}
            onMouseEnter={() => setHoveredPart(`Auxiliary Cooling Oil Distribution Pipe (Pressure: ${telemetry?.pressure || 4.2} bar)`)}
            onMouseLeave={() => setHoveredPart(null)}
          />

          {/* Labels & Callouts */}
          <text x="160" y="275" fill="#94a3b8" fontSize="10" fontFamily="sans-serif" textAnchor="middle">
            COOLING FAN
          </text>
          <text x="350" y="224" fill="#cbd5e1" fontSize="11" fontFamily="monospace" textAnchor="middle" fontWeight="bold">
            STATOR CORE & WINDINGS
          </text>
          <text x="525" y="224" fill={isBearingFault ? "#f87171" : "#cbd5e1"} fontSize="11" fontFamily="monospace" textAnchor="middle" fontWeight="bold">
            DE BEARING
          </text>
          <text x="650" y="124" fill="#38bdf8" fontSize="10" fontFamily="monospace" textAnchor="middle">
            SHAFT OUTPUT
          </text>
        </svg>
      </div>

      {/* Sensor Overlay Badges */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-2 pt-3 border-t border-slate-800/80 text-xs">
        <div className="flex items-center space-x-2 bg-slate-950/60 p-2 rounded-lg border border-slate-800">
          <Flame className={`w-4 h-4 ${temp > 75 ? 'text-rose-400' : 'text-slate-400'}`} />
          <div>
            <span className="text-[10px] text-slate-500 font-mono">HOUSING THERMAL</span>
            <div className="font-mono font-bold text-slate-200">{temp} °C</div>
          </div>
        </div>

        <div className="flex items-center space-x-2 bg-slate-950/60 p-2 rounded-lg border border-slate-800">
          <Activity className={`w-4 h-4 ${vib > 4.5 ? 'text-amber-400' : 'text-slate-400'}`} />
          <div>
            <span className="text-[10px] text-slate-500 font-mono">DE BEARING VIB</span>
            <div className="font-mono font-bold text-slate-200">{vib} mm/s</div>
          </div>
        </div>

        <div className="flex items-center space-x-2 bg-slate-950/60 p-2 rounded-lg border border-slate-800">
          <Zap className={`w-4 h-4 ${curr > 11.5 ? 'text-sky-400' : 'text-slate-400'}`} />
          <div>
            <span className="text-[10px] text-slate-500 font-mono">STATOR CURRENT</span>
            <div className="font-mono font-bold text-slate-200">{curr} A</div>
          </div>
        </div>

        <div className="flex items-center space-x-2 bg-slate-950/60 p-2 rounded-lg border border-slate-800">
          <Gauge className={`w-4 h-4 ${rpm < 1440 ? 'text-amber-400' : 'text-emerald-400'}`} />
          <div>
            <span className="text-[10px] text-slate-500 font-mono">SHAFT SPEED</span>
            <div className="font-mono font-bold text-slate-200">{rpm} RPM</div>
          </div>
        </div>
      </div>
    </div>
  );
}
