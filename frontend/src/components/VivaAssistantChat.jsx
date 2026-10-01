import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, Sparkles, FileText, HelpCircle, Terminal } from 'lucide-react';

export default function VivaAssistantChat({ telemetry, activeFault, diagnosis }) {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      text: "Hello! I am your **Knowledge-Driven IoT Reliability Assistant**. I have direct access to real-time machine telemetry, active deterministic fault triggers, and 7 indexed equipment engineering manuals. How can I assist with your fault diagnosis or viva examination defense today?",
      citations: ['Industrial Motor Maintenance Manual', 'ISO 10816-3 Standards'],
      is_fallback: false
    }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const quickPrompts = [
    "What does ISO 10816 Zone D vibration mean?",
    "Why does bearing degradation cause both high vibration and temperature?",
    "What is the difference between measured current and full load amps (FLA)?",
    "What safety precautions (LOTO) are required before inspecting the motor?"
  ];

  const handleSend = async (queryText) => {
    const textToSend = queryText || input;
    if (!textToSend.trim() || loading) return;

    const userMessage = { role: 'user', text: textToSend };
    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const response = await fetch('/api/assistant/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: textToSend,
          machine_id: 'MOTOR-001'
        })
      });

      if (!response.ok) throw new Error('Assistant API error');
      const data = await response.json();

      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          text: data.reply,
          citations: data.citations || [],
          is_fallback: data.is_fallback
        }
      ]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          text: "I experienced an error connecting to the backend assistant service. Please ensure the backend is running at http://localhost:8000.",
          citations: [],
          is_fallback: true
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-[650px] rounded-2xl bg-slate-900 border border-slate-800 shadow-xl overflow-hidden">
      {/* Header */}
      <div className="p-4 bg-slate-950/80 border-b border-slate-800 flex justify-between items-center">
        <div className="flex items-center space-x-3">
          <div className="p-2 rounded-xl bg-violet-600/20 text-violet-400 border border-violet-500/30">
            <Bot className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2">
              AI Reliability Assistant & Viva Tutor
              <span className="text-[10px] px-2 py-0.5 rounded font-mono bg-violet-950 text-violet-300 border border-violet-800">
                RAG + OLLAMA
              </span>
            </h3>
            <p className="text-[11px] text-slate-400">
              Interactive technical Q&A grounded in live telemetry and technical equipment manuals
            </p>
          </div>
        </div>

        <div className="text-xs text-slate-400 font-mono hidden md:block">
          Machine: MOTOR-001 • Telemetry: {telemetry ? `${telemetry.temperature}°C | ${telemetry.vibration} mm/s` : 'Nominal'}
        </div>
      </div>

      {/* Messages Stream */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 font-sans text-xs">
        {messages.map((msg, index) => {
          const isUser = msg.role === 'user';
          return (
            <div
              key={index}
              className={`flex items-start gap-3 ${isUser ? 'flex-row-reverse' : ''}`}
            >
              <div className={`p-2 rounded-lg flex-shrink-0 ${
                isUser ? 'bg-sky-600 text-white' : 'bg-slate-800 text-violet-400 border border-slate-700'
              }`}>
                {isUser ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
              </div>

              <div className={`max-w-2xl rounded-xl p-3.5 space-y-2 ${
                isUser
                  ? 'bg-sky-600/20 text-sky-100 border border-sky-500/30'
                  : 'bg-slate-950/90 text-slate-200 border border-slate-800'
              }`}>
                <div className="whitespace-pre-wrap leading-relaxed">
                  {msg.text}
                </div>

                {/* Citations & Fallback Badge for Assistant Responses */}
                {!isUser && (
                  <div className="pt-2 border-t border-slate-800/80 flex flex-wrap items-center gap-1.5 text-[10px]">
                    <span className="text-slate-500 font-mono">Sources:</span>
                    {msg.citations && msg.citations.length > 0 ? (
                      msg.citations.map((c, i) => (
                        <span key={i} className="px-2 py-0.5 rounded bg-violet-950/60 text-violet-300 border border-violet-800/60 flex items-center gap-1 font-mono">
                          <FileText className="w-2.5 h-2.5" />
                          {c}
                        </span>
                      ))
                    ) : (
                      <span className="text-slate-500">General Equipment Manuals</span>
                    )}

                    {msg.is_fallback && (
                      <span className="ml-auto px-1.5 py-0.5 rounded bg-amber-950 text-amber-300 border border-amber-800 text-[9px] font-mono">
                        Fallback Mode
                      </span>
                    )}
                  </div>
                )}
              </div>
            </div>
          );
        })}

        {loading && (
          <div className="flex items-start gap-3">
            <div className="p-2 rounded-lg bg-slate-800 text-violet-400 border border-slate-700">
              <Bot className="w-4 h-4 animate-pulse" />
            </div>
            <div className="bg-slate-950/90 border border-slate-800 p-3 rounded-xl flex items-center space-x-2 text-slate-400 text-xs font-mono">
              <span className="w-2 h-2 rounded-full bg-violet-400 animate-ping"></span>
              <span>Consulting RAG vector index & local Ollama...</span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Suggested Quick Prompt Pills */}
      <div className="px-4 py-2 bg-slate-950/40 border-t border-slate-800/60 flex items-center gap-2 overflow-x-auto text-[11px]">
        <span className="text-slate-500 flex items-center gap-1 flex-shrink-0 font-mono text-[10px]">
          <HelpCircle className="w-3 h-3 text-sky-400" /> Viva Prompts:
        </span>
        {quickPrompts.map((p, idx) => (
          <button
            key={idx}
            onClick={() => handleSend(p)}
            disabled={loading}
            className="flex-shrink-0 px-2.5 py-1 rounded-full bg-slate-800/80 hover:bg-slate-700 text-slate-300 border border-slate-700 transition"
          >
            {p}
          </button>
        ))}
      </div>

      {/* Input Box */}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          handleSend();
        }}
        className="p-3 bg-slate-950 border-t border-slate-800 flex items-center gap-2"
      >
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask a technical question about the motor, detected fault, or ISO 10816 standards..."
          disabled={loading}
          className="flex-1 bg-slate-900 border border-slate-800 rounded-xl px-4 py-2.5 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-sky-500 transition"
        />
        <button
          type="submit"
          disabled={loading || !input.trim()}
          className="px-4 py-2.5 bg-sky-600 hover:bg-sky-500 disabled:bg-slate-800 disabled:text-slate-500 text-white rounded-xl text-xs font-bold transition flex items-center gap-1.5 shadow"
        >
          <Send className="w-3.5 h-3.5" />
          <span>Send</span>
        </button>
      </form>
    </div>
  );
}
