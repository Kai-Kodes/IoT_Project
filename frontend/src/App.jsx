import React, { useState, useEffect, useRef } from 'react';
import {
  Activity,
  AlertTriangle,
  CheckCircle,
  Database,
  Cpu,
  Flame,
  Gauge,
  Radio,
  RefreshCw,
  Server,
  ShieldAlert,
  Sliders,
  Terminal,
  Wrench,
  Zap,
  Info,
  Layers,
  FileText,
  Volume2,
  VolumeX,
  MessageSquare,
  Printer,
  ChevronRight,
  ExternalLink
} from 'lucide-react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine
} from 'recharts';

import DigitalTwinMotor from './components/DigitalTwinMotor.jsx';
import VivaAssistantChat from './components/VivaAssistantChat.jsx';
import DialGauge from './components/DialGauge.jsx';
import { playAlarmSound } from './components/AudioAlarm.js';

export default function App() {
  const [activeTab, setActiveTab] = useState('overview');
  const [telemetryHistory, setTelemetryHistory] = useState([]);
  const [currentTelemetry, setCurrentTelemetry] = useState(null);
  const [activeFault, setActiveFault] = useState(null);
  const [latestDiagnosis, setLatestDiagnosis] = useState(null);
  const [healthStatus, setHealthStatus] = useState(null);
  const [faultHistory, setFaultHistory] = useState([]);
  const [isConnected, setIsConnected] = useState(false);
  const [simState, setSimState] = useState('normal');
  const [isInjecting, setIsInjecting] = useState(false);
  const [audioEnabled, setAudioEnabled] = useState(false);
  const [lastUpdated, setLastUpdated] = useState(new Date());

  const prevFaultRef = useRef(null);

  // Setup Server-Sent Events (SSE) Stream
  useEffect(() => {
    let eventSource = null;

    const connectSSE = () => {
      eventSource = new EventSource('/api/telemetry/stream');

      eventSource.onopen = () => {
        setIsConnected(true);
      };

      eventSource.onmessage = (event) => {
        try {
          const packet = JSON.parse(event.data);
          if (packet.type === 'telemetry') {
            const sample = packet.data;
            setCurrentTelemetry(sample);
            setLastUpdated(new Date());

            // Audio alert on new fault transition
            if (packet.active_fault && !prevFaultRef.current) {
              if (audioEnabled) {
                playAlarmSound(packet.active_fault.severity);
              }
            }
            prevFaultRef.current = packet.active_fault;
            setActiveFault(packet.active_fault);

            setTelemetryHistory((prev) => {
              const timeLabel = new Date(sample.timestamp).toLocaleTimeString([], {
                hour12: false,
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit'
              });
              const next = [...prev, { ...sample, timeLabel }];
              return next.length > 50 ? next.slice(next.length - 50) : next;
            });
          } else if (packet.type === 'diagnosis') {
            setLatestDiagnosis(packet.data);
          }
        } catch (err) {
          console.error('SSE parse error:', err);
        }
      };

      eventSource.onerror = (err) => {
        console.warn('SSE stream reconnecting in 3s...', err);
        setIsConnected(false);
        eventSource.close();
        setTimeout(connectSSE, 3000);
      };
    };

    connectSSE();

    return () => {
      if (eventSource) eventSource.close();
    };
  }, [audioEnabled]);

  // Poll Health & Initial Data
  const fetchHealthAndData = async () => {
    try {
      const [healthRes, diagRes, faultsRes, histRes] = await Promise.all([
        fetch('/api/health').then((r) => r.json()),
        fetch('/api/diagnosis/latest').then((r) => r.json()),
        fetch('/api/faults?limit=20').then((r) => r.json()),
        fetch('/api/telemetry/history?limit=40').then((r) => r.json()),
      ]);

      setHealthStatus(healthRes);
      if (diagRes && diagRes.fault_title) setLatestDiagnosis(diagRes);
      if (faultsRes) setFaultHistory(faultsRes);
      if (histRes && histRes.length > 0) {
        const formatted = histRes.map((h) => ({
          ...h,
          timeLabel: new Date(h.timestamp).toLocaleTimeString([], {
            hour12: false,
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
          }),
        }));
        setTelemetryHistory(formatted);
        setCurrentTelemetry(formatted[formatted.length - 1]);
      }
    } catch (e) {
      console.warn('Initial fetch error:', e);
    }
  };

  useEffect(() => {
    fetchHealthAndData();
    const interval = setInterval(fetchHealthAndData, 5000);
    return () => clearInterval(interval);
  }, []);

  // Simulator controls
  const handleFaultInjection = async (faultType) => {
    setIsInjecting(true);
    try {
      await fetch('/api/simulation/fault', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ command: 'inject_fault', fault_type: faultType }),
      });
      setSimState(faultType);
      setTimeout(fetchHealthAndData, 1200);
    } catch (e) {
      console.error('Fault injection failed:', e);
    } finally {
      setIsInjecting(false);
    }
  };

  const handleResetSimulation = async () => {
    setIsInjecting(true);
    try {
      await fetch('/api/simulation/reset', { method: 'POST' });
      setSimState('normal');
      setActiveFault(null);
      prevFaultRef.current = null;
      setTimeout(fetchHealthAndData, 1000);
    } catch (e) {
      console.error('Reset failed:', e);
    } finally {
      setIsInjecting(false);
    }
  };

  return (
    <div className="flex flex-col min-h-screen bg-slate-950 text-slate-100 selection:bg-sky-500 selection:text-white">
      {/* Top SCADA Navbar */}
      <header className="sticky top-0 z-50 bg-slate-900/90 backdrop-blur border-b border-slate-800 px-6 py-3 flex items-center justify-between shadow-md">
        <div className="flex items-center space-x-3">
          <div className="p-2 rounded-xl bg-sky-500/10 border border-sky-500/30 text-sky-400">
            <Cpu className="w-6 h-6 animate-pulse" />
          </div>
          <div>
            <h1 className="font-bold text-lg text-slate-100 flex items-center gap-2">
              P_311: IoT Fault Diagnosis Assistant
              <span className="text-[10px] px-2 py-0.5 rounded font-mono bg-sky-950 text-sky-300 border border-sky-800">
                EDGE CONTROL ROOM
              </span>
            </h1>
            <p className="text-xs text-slate-400 font-mono">
              Unit: {healthStatus?.active_machine || 'MOTOR-001'} | 11 kW Induction Motor | DebSheronin Debian Linux
            </p>
          </div>
        </div>

        {/* System Health Badges & Audio Alarm Controls */}
        <div className="flex items-center space-x-3 text-xs">
          {/* Audio Chime Toggle */}
          <button
            onClick={() => {
              const next = !audioEnabled;
              setAudioEnabled(next);
              if (next) playAlarmSound('warning');
            }}
            title={audioEnabled ? "Disable SCADA Audio Chime" : "Enable SCADA Audio Chime"}
            className={`px-2.5 py-1 rounded-md border flex items-center gap-1.5 transition ${
              audioEnabled
                ? 'bg-amber-950/80 border-amber-700 text-amber-300'
                : 'bg-slate-900 border-slate-800 text-slate-500 hover:text-slate-300'
            }`}
          >
            {audioEnabled ? <Volume2 className="w-3.5 h-3.5 text-amber-400 animate-pulse" /> : <VolumeX className="w-3.5 h-3.5" />}
            <span className="font-mono">{audioEnabled ? 'Alarm Sound ON' : 'Mute'}</span>
          </button>

          {/* MQTT Status */}
          <div className={`px-2.5 py-1 rounded-md border flex items-center gap-1.5 ${
            healthStatus?.mqtt_broker
              ? 'bg-emerald-950/60 border-emerald-800/80 text-emerald-300'
              : 'bg-rose-950/60 border-rose-800/80 text-rose-300'
          }`}>
            <Radio className="w-3.5 h-3.5" />
            <span>MQTT {healthStatus?.mqtt_broker ? '1883' : 'Offline'}</span>
          </div>

          {/* Database Status (PostgreSQL) */}
          <div className={`px-2.5 py-1 rounded-md border flex items-center gap-1.5 ${
            healthStatus?.database
              ? 'bg-blue-950/60 border-blue-800/80 text-blue-300'
              : 'bg-rose-950/60 border-rose-800/80 text-rose-300'
          }`}>
            <Database className="w-3.5 h-3.5" />
            <span>{healthStatus?.database_type === 'postgresql' ? 'Postgres 5433' : 'SQLite'}</span>
          </div>

          {/* Local LLM Status */}
          <div className={`px-2.5 py-1 rounded-md border flex items-center gap-1.5 ${
            healthStatus?.ollama_llm
              ? 'bg-violet-950/60 border-violet-800/80 text-violet-300'
              : 'bg-amber-950/60 border-amber-800/80 text-amber-300'
          }`}>
            <Terminal className="w-3.5 h-3.5" />
            <span>
              {healthStatus?.ollama_llm ? `Ollama (${healthStatus?.model_name || '1.5b'})` : 'LLM Fallback Active'}
            </span>
          </div>

          {/* Live SSE Pulse */}
          <div className={`px-2.5 py-1 rounded-md border flex items-center gap-1.5 ${
            isConnected ? 'bg-sky-950/60 border-sky-800/80 text-sky-300' : 'bg-amber-950/60 border-amber-800/80 text-amber-300'
          }`}>
            <span className={`w-2 h-2 rounded-full ${isConnected ? 'bg-sky-400 animate-ping' : 'bg-amber-400'}`}></span>
            <span>{isConnected ? '1 Hz Stream' : 'Connecting...'}</span>
          </div>

          {/* Grafana Direct Link */}
          <a
            href={healthStatus?.grafana_url || 'http://localhost:3000/d/p311-telemetry-dash'}
            target="_blank"
            rel="noopener noreferrer"
            className="px-3 py-1.5 rounded-lg border bg-gradient-to-r from-orange-600/30 to-amber-600/20 border-orange-500/50 text-orange-200 hover:text-white hover:border-orange-400 hover:from-orange-600/50 transition flex items-center gap-1.5 font-medium shadow-sm ml-2"
            title="Open Grafana SCADA Telemetry Dashboard (Port 3000)"
          >
            <span className="w-2 h-2 rounded-full bg-orange-400"></span>
            <span>Grafana SCADA</span>
            <ExternalLink className="w-3.5 h-3.5 opacity-80" />
          </a>
        </div>
      </header>

      {/* Main Tabs Navigation */}
      <nav className="bg-slate-900/40 border-b border-slate-800/80 px-6 py-2 flex items-center space-x-2 overflow-x-auto">
        {[
          { id: 'overview', label: 'Overview & Digital Twin', icon: Layers },
          { id: 'telemetry', label: 'Live Telemetry & Gauges', icon: Activity },
          { id: 'faults', label: 'Fault Audit Log', icon: ShieldAlert },
          { id: 'diagnosis', label: 'AI Diagnosis & Evidence', icon: Wrench },
          { id: 'viva', label: 'Viva AI Tutor & Q&A', icon: MessageSquare },
          { id: 'simulator', label: 'Fault Simulator', icon: Sliders },
        ].map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center space-x-2 px-4 py-2 rounded-xl text-sm font-medium transition-all ${
                isActive
                  ? 'bg-sky-600/20 text-sky-300 border border-sky-500/40 shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
              }`}
            >
              <Icon className="w-4 h-4" />
              <span>{tab.label}</span>
              {tab.id === 'faults' && activeFault && (
                <span className="w-2 h-2 rounded-full bg-rose-500 animate-ping"></span>
              )}
            </button>
          );
        })}
        <div className="ml-auto flex items-center pl-4">
          <a
            href={healthStatus?.grafana_url || 'http://localhost:3000/d/p311-telemetry-dash'}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold bg-orange-500/10 text-orange-300 border border-orange-500/30 hover:bg-orange-500/20 hover:text-white transition-all shadow-sm"
          >
            <span>Open Grafana SCADA (Port 3000)</span>
            <ExternalLink className="w-3.5 h-3.5" />
          </a>
        </div>
      </nav>

      {/* Content Container */}
      <main className="flex-1 p-6 max-w-7xl w-full mx-auto space-y-6">
        {activeTab === 'overview' && (
          <OverviewTab
            telemetry={currentTelemetry}
            activeFault={activeFault}
            latestDiagnosis={latestDiagnosis}
            setActiveTab={setActiveTab}
            simState={simState}
            onReset={handleResetSimulation}
          />
        )}

        {activeTab === 'telemetry' && (
          <TelemetryTab telemetryHistory={telemetryHistory} current={currentTelemetry} />
        )}

        {activeTab === 'faults' && (
          <FaultsTab
            faultHistory={faultHistory}
            activeFault={activeFault}
            onSelectDiagnosis={() => setActiveTab('diagnosis')}
          />
        )}

        {activeTab === 'diagnosis' && (
          <DiagnosisTab
            diagnosis={latestDiagnosis}
            activeFault={activeFault}
            telemetry={currentTelemetry}
            onNavigateSimulator={() => setActiveTab('simulator')}
          />
        )}

        {activeTab === 'viva' && (
          <VivaAssistantChat
            telemetry={currentTelemetry}
            activeFault={activeFault}
            diagnosis={latestDiagnosis}
          />
        )}

        {activeTab === 'simulator' && (
          <SimulatorTab
            simState={simState}
            isInjecting={isInjecting}
            onInject={handleFaultInjection}
            onReset={handleResetSimulation}
            activeFault={activeFault}
            telemetry={currentTelemetry}
          />
        )}
      </main>

      {/* Footer */}
      <footer className="mt-auto border-t border-slate-900 bg-slate-950 px-6 py-4 text-center text-xs text-slate-500 flex justify-between items-center">
        <span>Knowledge-Driven IoT Fault Diagnosis Assistant (P_311) • ISO 10816-3 Standard</span>
        <span className="font-mono text-slate-400">
          Last Packet: {lastUpdated ? lastUpdated.toLocaleTimeString() : 'Waiting for telemetry...'}
        </span>
      </footer>
    </div>
  );
}

// -------------------------------------------------------------
// TAB 1: OVERVIEW & DIGITAL TWIN
// -------------------------------------------------------------
function OverviewTab({ telemetry, activeFault, latestDiagnosis, setActiveTab, simState, onReset }) {
  const isHealthy = !activeFault;

  return (
    <div className="space-y-6">
      {/* Machine Status Banner */}
      <div className={`p-5 rounded-2xl border flex flex-col md:flex-row items-start md:items-center justify-between gap-4 transition-all shadow-lg ${
        isHealthy
          ? 'bg-emerald-950/30 border-emerald-800/50 text-emerald-200'
          : 'bg-rose-950/40 border-rose-800/60 text-rose-200'
      }`}>
        <div className="flex items-center space-x-4">
          <div className={`p-3.5 rounded-2xl ${
            isHealthy ? 'bg-emerald-500/20 text-emerald-400' : 'bg-rose-500/20 text-rose-400 animate-pulse'
          }`}>
            {isHealthy ? <CheckCircle className="w-8 h-8" /> : <AlertTriangle className="w-8 h-8" />}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-xl font-bold">
                {isHealthy ? 'System Operating Normally' : `Active Fault: ${activeFault?.fault_type?.replace('_', ' ').toUpperCase()}`}
              </h2>
              <span className={`px-2.5 py-0.5 rounded-full text-xs font-semibold uppercase ${
                isHealthy ? 'bg-emerald-900 text-emerald-300' : 'bg-rose-900 text-rose-300'
              }`}>
                {isHealthy ? 'HEALTHY' : activeFault?.severity}
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-1">
              {isHealthy
                ? 'All sensor telemetry within ISO 10816 vibration & thermal baseline parameters.'
                : `Triggered Rules: ${activeFault?.triggered_rules?.join(', ')}`}
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-3">
          {!isHealthy && (
            <button
              onClick={() => setActiveTab('diagnosis')}
              className="px-4 py-2 bg-rose-600 hover:bg-rose-500 text-white text-xs font-bold rounded-xl shadow transition flex items-center gap-1.5"
            >
              <span>Inspect AI Diagnosis</span>
              <ChevronRight className="w-3.5 h-3.5" />
            </button>
          )}
          <button
            onClick={() => setActiveTab('simulator')}
            className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold rounded-xl border border-slate-700 transition"
          >
            Fault Simulator
          </button>
        </div>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
        <KpiCard
          label="Bearing Temperature"
          value={telemetry ? `${telemetry.temperature} °C` : '--'}
          sub="Limit: 75 °C"
          icon={Flame}
          status={telemetry?.temperature > 75 ? (telemetry?.temperature > 95 ? 'critical' : 'warning') : 'normal'}
        />
        <KpiCard
          label="Vibration RMS"
          value={telemetry ? `${telemetry.vibration} mm/s` : '--'}
          sub="ISO Limit: 4.5 mm/s"
          icon={Activity}
          status={telemetry?.vibration > 4.5 ? (telemetry?.vibration > 7.1 ? 'critical' : 'warning') : 'normal'}
        />
        <KpiCard
          label="Motor Current"
          value={telemetry ? `${telemetry.current} A` : '--'}
          sub="Rated FLA: 9.0 A"
          icon={Zap}
          status={telemetry?.current > 11.5 ? 'warning' : 'normal'}
        />
        <KpiCard
          label="Shaft Speed"
          value={telemetry ? `${telemetry.rpm} RPM` : '--'}
          sub="Nominal: 1485 RPM"
          icon={Gauge}
          status={telemetry?.rpm < 1440 ? 'warning' : 'normal'}
        />
        <KpiCard
          label="Lube/Cooling Pressure"
          value={telemetry ? `${telemetry.pressure} bar` : '--'}
          sub="Nominal: 3.8 - 4.5"
          icon={Gauge}
          status={telemetry?.pressure < 3.0 ? 'warning' : 'normal'}
        />
      </div>

      {/* Interactive Physical Digital Twin Schematic */}
      <DigitalTwinMotor telemetry={telemetry} activeFault={activeFault} />

      {/* Latest Diagnosis Summary */}
      {latestDiagnosis && (
        <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-4 shadow-lg">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div className="flex items-center space-x-3">
              <div className="p-2.5 rounded-xl bg-sky-500/10 text-sky-400">
                <Wrench className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-base font-bold text-slate-100 flex items-center gap-2">
                  {latestDiagnosis.fault_title}
                  <span className={`text-[10px] px-2 py-0.5 rounded font-mono ${
                    latestDiagnosis.is_fallback
                      ? 'bg-amber-950 text-amber-300 border border-amber-800'
                      : 'bg-violet-950 text-violet-300 border border-violet-800'
                  }`}>
                    {latestDiagnosis.is_fallback ? 'Rule-Based Fallback' : 'Ollama Local LLM'}
                  </span>
                </h3>
                <p className="text-xs text-slate-400">
                  Confidence: {Math.round((latestDiagnosis.confidence || 0.85) * 100)}% | Execution Time: {latestDiagnosis.execution_time_ms} ms
                </p>
              </div>
            </div>
            <button
              onClick={() => setActiveTab('diagnosis')}
              className="text-xs text-sky-400 hover:text-sky-300 font-semibold flex items-center gap-1"
            >
              <span>View Full Diagnostic Report</span>
              <ChevronRight className="w-3.5 h-3.5" />
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
            <div className="space-y-1.5">
              <span className="font-semibold text-slate-300">Likely Root Causes:</span>
              <ul className="list-disc pl-5 space-y-1 text-slate-400">
                {latestDiagnosis.likely_causes?.slice(0, 3).map((cause, idx) => (
                  <li key={idx}>{cause}</li>
                ))}
              </ul>
            </div>
            <div className="space-y-1.5">
              <span className="font-semibold text-slate-300">Recommended Checks:</span>
              <ul className="list-disc pl-5 space-y-1 text-slate-400">
                {latestDiagnosis.recommended_checks?.slice(0, 3).map((chk, idx) => (
                  <li key={idx}>{chk}</li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function KpiCard({ label, value, sub, icon: Icon, status = 'normal' }) {
  const statusColors = {
    normal: 'border-slate-800 bg-slate-900/60 text-slate-200',
    warning: 'border-amber-800/80 bg-amber-950/20 text-amber-200',
    critical: 'border-rose-800/80 bg-rose-950/30 text-rose-200 animate-pulse',
  };

  const iconColors = {
    normal: 'text-sky-400',
    warning: 'text-amber-400',
    critical: 'text-rose-400',
  };

  return (
    <div className={`p-4 rounded-xl border ${statusColors[status]} transition-all flex flex-col justify-between shadow-sm`}>
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs text-slate-400 font-medium">{label}</span>
        <Icon className={`w-4 h-4 ${iconColors[status]}`} />
      </div>
      <div>
        <div className="text-xl font-mono font-bold">{value}</div>
        <div className="text-[10px] text-slate-500 font-mono mt-1">{sub}</div>
      </div>
    </div>
  );
}

// -------------------------------------------------------------
// TAB 2: LIVE TELEMETRY & GAUGES
// -------------------------------------------------------------
function TelemetryTab({ telemetryHistory, current }) {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-bold text-slate-100">Live Continuous Telemetry & Analog Meters</h2>
          <p className="text-xs text-slate-400">1 Hz synchronized industrial sensor streams with ISO reference limits</p>
        </div>
        <div className="text-xs font-mono bg-slate-900 px-3 py-1.5 rounded-lg border border-slate-800 text-slate-300">
          Sliding Window: {telemetryHistory.length} Samples
        </div>
      </div>

      {/* Row of Industrial Dial Meters */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <DialGauge
          label="Bearing Temperature"
          value={current?.temperature}
          min={30}
          max={120}
          unit="°C"
          warningThreshold={75}
          criticalThreshold={95}
          icon={Flame}
        />
        <DialGauge
          label="Vibration RMS"
          value={current?.vibration}
          min={0}
          max={15}
          unit="mm/s"
          warningThreshold={4.5}
          criticalThreshold={7.1}
          icon={Activity}
        />
        <DialGauge
          label="Stator Current"
          value={current?.current}
          min={0}
          max={20}
          unit="A"
          warningThreshold={11.5}
          criticalThreshold={13.5}
          icon={Zap}
        />
        <DialGauge
          label="Cooling Pressure"
          value={current?.pressure}
          min={0}
          max={6}
          unit="bar"
          warningThreshold={3.0}
          criticalThreshold={2.0}
          icon={Gauge}
        />
      </div>

      {/* Recharts Time Series Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Temperature Chart */}
        <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 shadow-md">
          <div className="flex justify-between items-center mb-3">
            <span className="text-sm font-semibold text-rose-300 flex items-center gap-1.5">
              <Flame className="w-4 h-4" /> Stator / Bearing Temperature (°C)
            </span>
            <span className="text-xs font-mono text-slate-400">Current: {current?.temperature} °C</span>
          </div>
          <div className="h-56">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={telemetryHistory}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="timeLabel" stroke="#64748b" tick={{ fontSize: 10 }} />
                <YAxis stroke="#64748b" domain={[30, 120]} tick={{ fontSize: 10 }} />
                <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', fontSize: '12px' }} />
                <ReferenceLine y={75} stroke="#f59e0b" strokeDasharray="3 3" label={{ value: 'Warning 75°C', fill: '#f59e0b', fontSize: 10 }} />
                <ReferenceLine y={95} stroke="#ef4444" strokeDasharray="3 3" label={{ value: 'Trip 95°C', fill: '#ef4444', fontSize: 10 }} />
                <Line type="monotone" dataKey="temperature" stroke="#f43f5e" strokeWidth={2} dot={false} isAnimationActive={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Vibration Chart */}
        <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 shadow-md">
          <div className="flex justify-between items-center mb-3">
            <span className="text-sm font-semibold text-amber-300 flex items-center gap-1.5">
              <Activity className="w-4 h-4" /> Vibration Velocity RMS (mm/s - ISO 10816)
            </span>
            <span className="text-xs font-mono text-slate-400">Current: {current?.vibration} mm/s</span>
          </div>
          <div className="h-56">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={telemetryHistory}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="timeLabel" stroke="#64748b" tick={{ fontSize: 10 }} />
                <YAxis stroke="#64748b" domain={[0, 15]} tick={{ fontSize: 10 }} />
                <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', fontSize: '12px' }} />
                <ReferenceLine y={2.8} stroke="#10b981" strokeDasharray="3 3" label={{ value: 'Zone B 2.8', fill: '#10b981', fontSize: 10 }} />
                <ReferenceLine y={4.5} stroke="#f59e0b" strokeDasharray="3 3" label={{ value: 'Zone C Alert 4.5', fill: '#f59e0b', fontSize: 10 }} />
                <ReferenceLine y={7.1} stroke="#ef4444" strokeDasharray="3 3" label={{ value: 'Zone D Trip 7.1', fill: '#ef4444', fontSize: 10 }} />
                <Line type="monotone" dataKey="vibration" stroke="#f59e0b" strokeWidth={2} dot={false} isAnimationActive={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Current Chart */}
        <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 shadow-md">
          <div className="flex justify-between items-center mb-3">
            <span className="text-sm font-semibold text-sky-300 flex items-center gap-1.5">
              <Zap className="w-4 h-4" /> Motor Stator Current (Amperes)
            </span>
            <span className="text-xs font-mono text-slate-400">Current: {current?.current} A</span>
          </div>
          <div className="h-56">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={telemetryHistory}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="timeLabel" stroke="#64748b" tick={{ fontSize: 10 }} />
                <YAxis stroke="#64748b" domain={[5, 20]} tick={{ fontSize: 10 }} />
                <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', fontSize: '12px' }} />
                <ReferenceLine y={9.0} stroke="#38bdf8" strokeDasharray="3 3" label={{ value: 'Rated 9.0 A', fill: '#38bdf8', fontSize: 10 }} />
                <ReferenceLine y={13.5} stroke="#ef4444" strokeDasharray="3 3" label={{ value: 'Overload 13.5 A', fill: '#ef4444', fontSize: 10 }} />
                <Line type="monotone" dataKey="current" stroke="#38bdf8" strokeWidth={2} dot={false} isAnimationActive={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Speed (RPM) Chart */}
        <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 shadow-md">
          <div className="flex justify-between items-center mb-3">
            <span className="text-sm font-semibold text-emerald-300 flex items-center gap-1.5">
              <Gauge className="w-4 h-4" /> Rotational Shaft Speed (RPM)
            </span>
            <span className="text-xs font-mono text-slate-400">Current: {current?.rpm} RPM</span>
          </div>
          <div className="h-56">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={telemetryHistory}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="timeLabel" stroke="#64748b" tick={{ fontSize: 10 }} />
                <YAxis stroke="#64748b" domain={[1350, 1550]} tick={{ fontSize: 10 }} />
                <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', fontSize: '12px' }} />
                <ReferenceLine y={1485} stroke="#10b981" strokeDasharray="3 3" label={{ value: 'Rated 1485', fill: '#10b981', fontSize: 10 }} />
                <Line type="monotone" dataKey="rpm" stroke="#10b981" strokeWidth={2} dot={false} isAnimationActive={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
}

// -------------------------------------------------------------
// TAB 3: FAULTS AUDIT LOG
// -------------------------------------------------------------
function FaultsTab({ faultHistory, activeFault, onSelectDiagnosis }) {
  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-lg font-bold text-slate-100">Deterministic Fault Event Log</h2>
          <p className="text-xs text-slate-400">Complete audit trail of rule triggers and multi-sensor evidence snapshots</p>
        </div>
      </div>

      <div className="overflow-x-auto rounded-2xl border border-slate-800 bg-slate-900 shadow-md">
        <table className="w-full text-left text-xs">
          <thead className="bg-slate-800/80 text-slate-300 uppercase tracking-wider font-semibold border-b border-slate-700">
            <tr>
              <th className="px-4 py-3">Event ID</th>
              <th className="px-4 py-3">Timestamp</th>
              <th className="px-4 py-3">Fault Classification</th>
              <th className="px-4 py-3">Severity</th>
              <th className="px-4 py-3">Triggered Rules</th>
              <th className="px-4 py-3">Sensor Snapshot</th>
              <th className="px-4 py-3 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800 font-mono text-slate-300">
            {faultHistory.length === 0 ? (
              <tr>
                <td colSpan="7" className="px-4 py-8 text-center text-slate-500 font-sans">
                  No fault events recorded yet. Run a simulator fault mode to generate events.
                </td>
              </tr>
            ) : (
              faultHistory.map((item) => (
                <tr key={item.id} className="hover:bg-slate-800/40 transition">
                  <td className="px-4 py-3 font-bold text-sky-400">{item.id}</td>
                  <td className="px-4 py-3 text-slate-400">
                    {new Date(item.timestamp).toLocaleTimeString()}
                  </td>
                  <td className="px-4 py-3 font-sans font-medium text-slate-200">
                    {item.fault_type?.replace('_', ' ').toUpperCase()}
                  </td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                      item.severity === 'critical'
                        ? 'bg-rose-950 text-rose-300 border border-rose-800'
                        : 'bg-amber-950 text-amber-300 border border-amber-800'
                    }`}>
                      {item.severity}
                    </span>
                  </td>
                  <td className="px-4 py-3 font-sans">
                    <div className="flex flex-wrap gap-1">
                      {item.triggered_rules?.map((r, i) => (
                        <span key={i} className="px-1.5 py-0.5 rounded bg-slate-800 text-[10px] text-slate-300 border border-slate-700">
                          {r}
                        </span>
                      ))}
                    </div>
                  </td>
                  <td className="px-4 py-3 text-[11px] text-slate-400">
                    T: {item.sensor_evidence?.temperature}°C | V: {item.sensor_evidence?.vibration} mm/s | I: {item.sensor_evidence?.current} A
                  </td>
                  <td className="px-4 py-3 text-right font-sans">
                    <button
                      onClick={onSelectDiagnosis}
                      className="px-2.5 py-1 bg-sky-600/30 hover:bg-sky-600/50 text-sky-300 rounded-lg text-xs transition"
                    >
                      View Diagnosis
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// -------------------------------------------------------------
// TAB 4: DIAGNOSIS & EXPLAINABLE EVIDENCE
// -------------------------------------------------------------
function DiagnosisTab({ diagnosis, activeFault, telemetry, onNavigateSimulator }) {
  const [checkedItems, setCheckedItems] = useState({});

  const toggleCheck = (idx) => {
    setCheckedItems((prev) => ({ ...prev, [idx]: !prev[idx] }));
  };

  if (!diagnosis || !diagnosis.fault_title) {
    return (
      <div className="p-12 text-center rounded-2xl bg-slate-900 border border-slate-800 space-y-4 shadow-lg">
        <Wrench className="w-12 h-12 text-slate-600 mx-auto" />
        <h3 className="text-base font-semibold text-slate-300">No AI Diagnosis Generated Yet</h3>
        <p className="text-xs text-slate-500 max-w-md mx-auto">
          The system continuously evaluates telemetry. Inject a fault via the Simulator tab to trigger deterministic detection, RAG retrieval, and AI diagnosis.
        </p>
        <button
          onClick={onNavigateSimulator}
          className="px-4 py-2 bg-sky-600 hover:bg-sky-500 text-white rounded-xl text-xs font-semibold"
        >
          Open Simulator Controls
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Diagnosis Header with Work Order Export Button */}
      <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 flex flex-col md:flex-row justify-between items-start md:items-center gap-4 shadow-xl">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className={`px-2.5 py-0.5 rounded text-xs font-bold uppercase ${
              diagnosis.severity === 'critical'
                ? 'bg-rose-950 text-rose-300 border border-rose-800'
                : 'bg-amber-950 text-amber-300 border border-amber-800'
            }`}>
              {diagnosis.severity}
            </span>
            <span className={`px-2 py-0.5 rounded text-xs font-mono ${
              diagnosis.is_fallback
                ? 'bg-amber-950/80 text-amber-300 border border-amber-800'
                : 'bg-violet-950/80 text-violet-300 border border-violet-800'
            }`}>
              {diagnosis.is_fallback ? 'Rule-Based Fallback' : 'Ollama Local LLM'}
            </span>
            <span className="text-xs text-slate-400 font-mono">
              Latency: {diagnosis.execution_time_ms} ms
            </span>
          </div>
          <h2 className="text-2xl font-bold text-slate-100">{diagnosis.fault_title}</h2>
          <p className="text-xs text-slate-400 mt-1">
            Generated at {new Date(diagnosis.timestamp).toLocaleTimeString()} for Machine: {diagnosis.machine_id}
          </p>
        </div>

        <div className="flex items-center gap-3">
          <a
            href={`/api/reports/work-order?machine_id=${diagnosis.machine_id}`}
            target="_blank"
            rel="noreferrer"
            className="flex items-center gap-1.5 px-3.5 py-2 bg-sky-600/30 hover:bg-sky-600/50 text-sky-300 border border-sky-500/40 rounded-xl text-xs font-bold transition shadow-sm"
          >
            <Printer className="w-3.5 h-3.5" />
            <span>Print Work Order</span>
          </a>

          <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 text-center min-w-[120px]">
            <span className="text-[10px] text-slate-500 uppercase tracking-wider font-semibold">Diagnostic Confidence</span>
            <div className="text-2xl font-mono font-bold text-sky-400 mt-0.5">
              {Math.round((diagnosis.confidence || 0.85) * 100)}%
            </div>
          </div>
        </div>
      </div>

      {/* Measured Telemetry vs Baseline Reference Table */}
      <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-3 shadow-md">
        <h3 className="text-sm font-bold text-slate-200 flex items-center gap-2">
          <Activity className="w-4 h-4 text-sky-400" />
          Measured Sensor Evidence (Ground Truth)
        </h3>
        <p className="text-xs text-slate-400">
          The local LLM is constrained strictly to these physical sensor measurements without hallucination.
        </p>

        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3 pt-2">
          <div className="p-3 bg-slate-950 rounded-xl border border-slate-800">
            <span className="text-[10px] text-slate-500 uppercase font-mono">Temperature</span>
            <div className="text-base font-mono font-bold text-rose-300">{diagnosis.sensor_evidence?.temperature} °C</div>
            <div className="text-[10px] text-slate-500">Norm: 45-65 °C</div>
          </div>
          <div className="p-3 bg-slate-950 rounded-xl border border-slate-800">
            <span className="text-[10px] text-slate-500 uppercase font-mono">Vibration</span>
            <div className="text-base font-mono font-bold text-amber-300">{diagnosis.sensor_evidence?.vibration} mm/s</div>
            <div className="text-[10px] text-slate-500">ISO: &lt; 2.8 mm/s</div>
          </div>
          <div className="p-3 bg-slate-950 rounded-xl border border-slate-800">
            <span className="text-[10px] text-slate-500 uppercase font-mono">Current</span>
            <div className="text-base font-mono font-bold text-sky-300">{diagnosis.sensor_evidence?.current} A</div>
            <div className="text-[10px] text-slate-500">Rated: 9.0 A</div>
          </div>
          <div className="p-3 bg-slate-950 rounded-xl border border-slate-800">
            <span className="text-[10px] text-slate-500 uppercase font-mono">Speed (RPM)</span>
            <div className="text-base font-mono font-bold text-emerald-300">{diagnosis.sensor_evidence?.rpm}</div>
            <div className="text-[10px] text-slate-500">Rated: 1485</div>
          </div>
          <div className="p-3 bg-slate-950 rounded-xl border border-slate-800">
            <span className="text-[10px] text-slate-500 uppercase font-mono">Pressure</span>
            <div className="text-base font-mono font-bold text-slate-300">{diagnosis.sensor_evidence?.pressure} bar</div>
            <div className="text-[10px] text-slate-500">Norm: 3.8-4.5</div>
          </div>
          <div className="p-3 bg-slate-950 rounded-xl border border-slate-800">
            <span className="text-[10px] text-slate-500 uppercase font-mono">Voltage</span>
            <div className="text-base font-mono font-bold text-slate-300">{diagnosis.sensor_evidence?.voltage} V</div>
            <div className="text-[10px] text-slate-500">Nom: 230/400V</div>
          </div>
        </div>
      </div>

      {/* Likely Root Causes & Interactive Diagnostic Checks */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Likely Causes */}
        <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-4 shadow-md">
          <h3 className="text-sm font-bold text-slate-200 flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-amber-400" />
            Plausible Root Causes
          </h3>
          <ul className="space-y-2 text-xs">
            {diagnosis.likely_causes?.map((cause, i) => (
              <li key={i} className="flex items-start space-x-2 text-slate-300 p-3 rounded-xl bg-slate-950/60 border border-slate-800">
                <span className="text-sky-400 font-bold">•</span>
                <span>{cause}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* Interactive Recommended Checks Checklist */}
        <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-4 shadow-md">
          <h3 className="text-sm font-bold text-slate-200 flex items-center gap-2">
            <Wrench className="w-4 h-4 text-emerald-400" />
            Recommended Diagnostic Checks (Maintenance Checklist)
          </h3>
          <div className="space-y-2 text-xs">
            {diagnosis.recommended_checks?.map((chk, i) => (
              <label
                key={i}
                onClick={() => toggleCheck(i)}
                className={`flex items-start space-x-3 p-3 rounded-xl border cursor-pointer transition select-none ${
                  checkedItems[i]
                    ? 'bg-emerald-950/30 border-emerald-800/60 text-emerald-200'
                    : 'bg-slate-950/60 border-slate-800 text-slate-300 hover:border-slate-700'
                }`}
              >
                <input
                  type="checkbox"
                  checked={!!checkedItems[i]}
                  onChange={() => {}}
                  className="mt-0.5 rounded border-slate-700 text-emerald-500 focus:ring-0"
                />
                <span className={checkedItems[i] ? 'line-through text-slate-400' : ''}>{chk}</span>
              </label>
            ))}
          </div>
        </div>
      </div>

      {/* Recommended Corrective Actions */}
      <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-3 shadow-md">
        <h3 className="text-sm font-bold text-slate-200 flex items-center gap-2">
          <CheckCircle className="w-4 h-4 text-sky-400" />
          Recommended Corrective Actions & LOTO Safety Protocol
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
          {diagnosis.corrective_actions?.map((act, i) => (
            <div key={i} className="p-3.5 bg-slate-950 rounded-xl border border-slate-800 flex items-start space-x-2 text-slate-300">
              <span className="font-mono text-sky-400 font-bold">{i + 1}.</span>
              <span>{act}</span>
            </div>
          ))}
        </div>
      </div>

      {/* RAG Knowledge Base Sources */}
      <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-3 shadow-md">
        <h3 className="text-sm font-bold text-slate-200 flex items-center gap-2">
          <FileText className="w-4 h-4 text-violet-400" />
          Retrieved Technical Knowledge Sources (RAG Citations)
        </h3>
        <div className="flex flex-wrap gap-2 text-xs">
          {diagnosis.knowledge_sources?.map((src, i) => (
            <div key={i} className="px-3.5 py-1.5 rounded-xl bg-violet-950/30 border border-violet-800/50 text-violet-300 flex items-center gap-1.5">
              <FileText className="w-3.5 h-3.5" />
              <span>{src}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Uncertainty & Engineering Caveat Disclaimer */}
      <div className="p-4 rounded-2xl bg-slate-950 border border-slate-800 flex items-start space-x-3 text-xs text-slate-400">
        <Info className="w-5 h-5 text-sky-400 flex-shrink-0 mt-0.5" />
        <div>
          <span className="font-semibold text-slate-300 block mb-0.5">Engineering Uncertainty & Safety Advisory:</span>
          {diagnosis.uncertainty}
        </div>
      </div>
    </div>
  );
}

// -------------------------------------------------------------
// TAB 6: SIMULATOR CONTROLS
// -------------------------------------------------------------
function SimulatorTab({ simState, isInjecting, onInject, onReset, activeFault, telemetry }) {
  const faultModes = [
    {
      id: 'bearing_degradation',
      name: 'Bearing Degradation',
      desc: 'High friction: Vibration surges to 8.4 mm/s, temperature ramps to 89°C, current rises.',
      badge: 'Zone D Trip',
    },
    {
      id: 'motor_overheating',
      name: 'Motor Overheating',
      desc: 'Cooling blockage: Temperature spikes over 104°C while vibration remains normal.',
      badge: 'Thermal Alarm',
    },
    {
      id: 'motor_overload',
      name: 'Motor Overload',
      desc: 'Mechanical bind: Current surges to 15.8 A (>150% FLA) with sharp rotor slip speed drop.',
      badge: 'Overcurrent',
    },
    {
      id: 'excessive_vibration',
      name: 'Excessive Vibration',
      desc: 'Rotor unbalance / looseness: Vibration velocity spikes to 11.2 mm/s.',
      badge: 'ISO 10816 Alert',
    },
    {
      id: 'low_pressure',
      name: 'Low Lube Pressure',
      desc: 'Auxiliary cooling line pressure collapses below 2.0 bar.',
      badge: 'Lube Alarm',
    },
    {
      id: 'sensor_anomaly',
      name: 'Sensor Anomaly',
      desc: 'Open thermocouple fault: Temperature step-jumps instantly to 999°C.',
      badge: 'Sensor Error',
    },
  ];

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <div>
        <h2 className="text-lg font-bold text-slate-100">Industrial Machine Simulator Control Panel</h2>
        <p className="text-xs text-slate-400">
          Inject deterministic mechanical and electrical faults over MQTT into the live induction motor simulation.
        </p>
      </div>

      {/* Current State Card */}
      <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 flex items-center justify-between shadow-md">
        <div>
          <span className="text-xs text-slate-400 uppercase font-mono">Current Simulator Profile</span>
          <div className="text-xl font-bold text-slate-100 capitalize mt-0.5">
            {simState.replace('_', ' ')}
          </div>
        </div>
        <button
          onClick={onReset}
          disabled={isInjecting}
          className="flex items-center space-x-2 px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white font-bold rounded-xl text-xs shadow transition"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isInjecting ? 'animate-spin' : ''}`} />
          <span>Reset Machine to Normal</span>
        </button>
      </div>

      {/* Fault Injection Buttons Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {faultModes.map((fm) => {
          const isSelected = simState === fm.id;
          return (
            <div
              key={fm.id}
              className={`p-5 rounded-2xl border transition-all flex flex-col justify-between shadow-sm ${
                isSelected
                  ? 'bg-rose-950/30 border-rose-600 text-rose-100 shadow-md'
                  : 'bg-slate-900 border-slate-800 text-slate-200 hover:border-slate-700'
              }`}
            >
              <div>
                <div className="flex justify-between items-center mb-2">
                  <h3 className="font-bold text-sm text-slate-100">{fm.name}</h3>
                  <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-slate-800 text-slate-300 border border-slate-700">
                    {fm.badge}
                  </span>
                </div>
                <p className="text-xs text-slate-400 mb-4">{fm.desc}</p>
              </div>

              <button
                onClick={() => onInject(fm.id)}
                disabled={isInjecting}
                className={`w-full py-2.5 rounded-xl text-xs font-bold transition flex items-center justify-center space-x-1.5 ${
                  isSelected
                    ? 'bg-rose-600 text-white'
                    : 'bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700'
                }`}
              >
                <Flame className="w-3.5 h-3.5" />
                <span>{isSelected ? 'Active Fault Injected' : `Inject ${fm.name}`}</span>
              </button>
            </div>
          );
        })}
      </div>
    </div>
  );
}
