"use client";

import { useEffect, useState } from "react";
import type { CodeTrace, TraceStep } from "../types/game";
import { CLASS_COLORS } from "../types/game";

function InheritanceChain({ chain }: { chain: string[] }) {
  return (
    <div className="flex items-center gap-1 flex-wrap">
      {chain.map((cls, i) => {
        const color = CLASS_COLORS[cls] ?? "#6b7280";
        return (
          <span key={cls} className="flex items-center gap-1">
            <span
              className="text-xs font-mono px-1.5 py-0.5 rounded"
              style={{ color, background: `${color}14`, border: `1px solid ${color}30` }}
            >{cls}</span>
            {i < chain.length - 1 && <span className="text-gray-700 text-xs">→</span>}
          </span>
        );
      })}
    </div>
  );
}

const CONCEPT_STYLES: Record<string, { bg: string; text: string; border: string }> = {
  "Polymorphism":    { bg: "rgba(139,92,246,0.1)",  text: "#a78bfa", border: "rgba(139,92,246,0.25)" },
  "Inheritance":     { bg: "rgba(16,185,129,0.1)",  text: "#6ee7b7", border: "rgba(16,185,129,0.25)" },
  "Encapsulation":   { bg: "rgba(245,158,11,0.1)",  text: "#fcd34d", border: "rgba(245,158,11,0.25)" },
  "Abstraction":     { bg: "rgba(239,68,68,0.1)",   text: "#fca5a5", border: "rgba(239,68,68,0.25)" },
  "Method Override": { bg: "rgba(14,165,233,0.1)",  text: "#7dd3fc", border: "rgba(14,165,233,0.25)" },
  "super()":         { bg: "rgba(251,146,60,0.1)",  text: "#fdba74", border: "rgba(251,146,60,0.25)" },
};

function TraceStepCard({ step, index, visible }: { step: TraceStep; index: number; visible: boolean }) {
  const color = CLASS_COLORS[step.class_name] ?? "#6b7280";
  const concept = CONCEPT_STYLES[step.concept] ?? { bg: "rgba(107,114,128,0.1)", text: "#9ca3af", border: "rgba(107,114,128,0.2)" };

  if (!visible) return null;

  return (
    <div
      className="rounded-xl overflow-hidden animate-fade-slide"
      style={{
        background: "#0b0b18",
        border: `1px solid ${color}25`,
        animationDelay: `${index * 80}ms`,
      }}
    >
      {/* Step header */}
      <div
        className="flex items-center justify-between px-3 py-2"
        style={{ background: `${color}0c`, borderBottom: `1px solid ${color}20` }}
      >
        <div className="flex items-center gap-2">
          <span
            className="text-xs font-mono font-bold px-2 py-0.5 rounded"
            style={{ color, background: `${color}18`, border: `1px solid ${color}30` }}
          >{step.class_name}</span>
          <span className="text-gray-400 text-xs font-mono">{step.method_name}</span>
        </div>
        <span
          className="text-xs font-mono px-1.5 py-0.5 rounded shrink-0"
          style={{ background: concept.bg, color: concept.text, border: `1px solid ${concept.border}` }}
        >{step.concept}</span>
      </div>

      <div className="p-3 space-y-2">
        {/* Code line */}
        <pre
          className="text-xs font-mono p-2.5 rounded-lg overflow-x-auto leading-relaxed"
          style={{ background: "#060610", color: "#a0e878", border: "1px solid #1a2a1a" }}
        >{step.code_line}</pre>

        {/* Description */}
        <p className="text-xs text-gray-400 leading-relaxed">{step.description}</p>

        {/* Chain */}
        {step.inheritance_chain && step.inheritance_chain.length > 1 && (
          <div>
            <p className="text-xs font-mono mb-1.5" style={{ color: "#3a3a5a" }}>CHAIN</p>
            <InheritanceChain chain={step.inheritance_chain} />
          </div>
        )}
      </div>
    </div>
  );
}

interface CodeTracePanelProps {
  trace: CodeTrace | null;
  enemyTrace: CodeTrace | null;
  title?: string;
}

export function CodeTracePanel({ trace, enemyTrace }: CodeTracePanelProps) {
  const [visibleCount, setVisibleCount] = useState(0);
  const [activeTab, setActiveTab] = useState<"player" | "enemy">("player");

  const activeTrace = activeTab === "player" ? trace : enemyTrace;

  useEffect(() => {
    setVisibleCount(0);
    if (!activeTrace?.steps.length) return;
    const interval = setInterval(() => {
      setVisibleCount(c => {
        if (c >= (activeTrace.steps.length)) { clearInterval(interval); return c; }
        return c + 1;
      });
    }, 500);
    return () => clearInterval(interval);
  }, [activeTrace]);

  useEffect(() => { setActiveTab("player"); }, [trace]);

  return (
    <div className="flex flex-col h-full" style={{ background: "#08080f" }}>
      {/* Header */}
      <div className="px-4 py-3 shrink-0" style={{ borderBottom: "1px solid #1a1a2e" }}>
        <div className="flex items-center justify-between mb-2">
          <span className="font-mono text-xs tracking-widest uppercase" style={{ color: "#4a4a7a" }}>Code Trace</span>
          {(trace || enemyTrace) && (
            <div className="flex gap-1">
              {trace && (
                <button
                  onClick={() => setActiveTab("player")}
                  className="text-xs font-mono px-2 py-1 rounded transition-colors"
                  style={{
                    background: activeTab === "player" ? "rgba(245,158,11,0.15)" : "transparent",
                    color: activeTab === "player" ? "#f59e0b" : "#4a4a6a",
                    border: `1px solid ${activeTab === "player" ? "rgba(245,158,11,0.3)" : "transparent"}`,
                  }}
                >Hero</button>
              )}
              {enemyTrace && (
                <button
                  onClick={() => setActiveTab("enemy")}
                  className="text-xs font-mono px-2 py-1 rounded transition-colors"
                  style={{
                    background: activeTab === "enemy" ? "rgba(239,68,68,0.15)" : "transparent",
                    color: activeTab === "enemy" ? "#f87171" : "#4a4a6a",
                    border: `1px solid ${activeTab === "enemy" ? "rgba(239,68,68,0.3)" : "transparent"}`,
                  }}
                >Enemy</button>
              )}
            </div>
          )}
        </div>

        {activeTrace && (
          <div>
            <p className="text-sm font-display font-semibold text-gray-200">{activeTrace.action_key?.replace(/_/g, " ").replace(/\b\w/g, l => l.toUpperCase())}</p>
            <p className="text-xs text-gray-600 mt-0.5 leading-relaxed">{activeTrace.summary}</p>
          </div>
        )}
      </div>

      {/* Steps */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {!trace && !enemyTrace && (
          <div className="flex flex-col items-center justify-center h-full text-center px-6 py-12">
            <div className="text-4xl mb-4 opacity-20">⟡</div>
            <p className="font-mono text-xs tracking-widest uppercase mb-2" style={{ color: "#2a2a4a" }}>Awaiting action</p>
            <p className="text-gray-700 text-sm leading-relaxed">
              Attack, cast a spell, or defend. Each action reveals the class methods and inheritance chain behind it.
            </p>
          </div>
        )}

        {activeTrace?.steps.map((step, i) => (
          <TraceStepCard key={i} step={step} index={i} visible={i < visibleCount} />
        ))}
      </div>
    </div>
  );
}

export default CodeTracePanel;
