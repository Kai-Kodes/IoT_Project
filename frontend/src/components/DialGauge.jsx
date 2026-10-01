import React from 'react';

export default function DialGauge({
  label,
  value,
  min = 0,
  max = 100,
  unit = '',
  warningThreshold,
  criticalThreshold,
  icon: Icon
}) {
  const numericValue = typeof value === 'number' ? value : parseFloat(value) || 0;
  const clamped = Math.min(Math.max(numericValue, min), max);
  const percentage = (clamped - min) / (max - min);

  // Gauge angles from -120 to +120 degrees (240 deg arc)
  const angle = -120 + percentage * 240;

  // Determine state color
  let arcColor = '#10b981'; // Green
  let textColor = 'text-emerald-400';
  if (criticalThreshold !== undefined && numericValue >= criticalThreshold) {
    arcColor = '#ef4444'; // Red
    textColor = 'text-rose-400';
  } else if (warningThreshold !== undefined && numericValue >= warningThreshold) {
    arcColor = '#f59e0b'; // Amber
    textColor = 'text-amber-400';
  }

  // Calculate needle endpoints
  const radius = 42;
  const cx = 60;
  const cy = 60;
  const rad = (angle * Math.PI) / 180;
  const nx = cx + radius * Math.sin(rad);
  const ny = cy - radius * Math.cos(rad);

  return (
    <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 flex flex-col items-center justify-between shadow-sm">
      <div className="w-full flex justify-between items-center text-xs mb-1">
        <span className="text-slate-400 font-medium">{label}</span>
        {Icon && <Icon className={`w-3.5 h-3.5 ${textColor}`} />}
      </div>

      <div className="relative w-32 h-24 flex items-center justify-center">
        <svg viewBox="0 0 120 90" className="w-full h-full overflow-visible">
          {/* Background Arc */}
          <path
            d="M 23 75 A 45 45 0 1 1 97 75"
            fill="none"
            stroke="#1e293b"
            strokeWidth="8"
            strokeLinecap="round"
          />

          {/* Active Arc (Approximated with strokeDasharray) */}
          <path
            d="M 23 75 A 45 45 0 1 1 97 75"
            fill="none"
            stroke={arcColor}
            strokeWidth="8"
            strokeLinecap="round"
            strokeDasharray="210"
            strokeDashoffset={210 - percentage * 210}
            className="transition-all duration-500 ease-out"
          />

          {/* Center Pivot Point */}
          <circle cx={cx} cy={cy} r="4" fill="#cbd5e1" />

          {/* Needle Line */}
          <line
            x1={cx}
            y1={cy}
            x2={nx}
            y2={ny}
            stroke="#cbd5e1"
            strokeWidth="2.5"
            strokeLinecap="round"
            className="transition-all duration-300 ease-out"
          />
        </svg>

        {/* Value Overlay */}
        <div className="absolute bottom-0 text-center font-mono">
          <span className={`text-base font-bold ${textColor}`}>
            {value !== null && value !== undefined ? value : '--'}
          </span>
          <span className="text-[10px] text-slate-500 ml-1">{unit}</span>
        </div>
      </div>

      <div className="w-full flex justify-between text-[9px] font-mono text-slate-500 mt-1">
        <span>{min}{unit}</span>
        <span>{max}{unit}</span>
      </div>
    </div>
  );
}
