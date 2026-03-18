"use client";

import { useEffect, useState } from "react";
import type { CodeTrace, TraceStep } from "@/types/game";
import { CLASS_COLORS } from "@/types/game";

// ─── Inheritance chain visualizer ─────────────────────────────────────────────

function InheritanceChain({ chain }: { chain: string[] }) {
  return (
    <div className="flex items-center gap-1 flex-wrap">
      {chain.map((cls, i) => (
        <span key={cls} className="flex items-center gap-1">
          <span
            className="text-xs font-mono px-1.5 py-0.5 rounded"
            style={{
              backgroundColor: `${CLASS_COLORS[cls] ?? "#6b7280"}22`,
              color: CLASS_COLORS[cls] ?? "#9ca3af",
              border: `1px solid ${CLASS_COLORS[cls] ?? "#6b7280"}44`,
            }}
          >
            {cls}
          </span>
          {i < chain.length - 1 && (
            <span className="text-gray-600 text-xs">→</span>
          )}
        </span>
      ))}
    </div>
  );
}

// ─── Single trace step card ───────────────────────────────────────────────────

function TraceStepCard({
  step,
  index,
  isActive,
}: {
  step: TraceStep;
  index: number;
  isActive: boolean;
}) {
  const classColor = CLASS_COLORS[step.class_name] ?? "#6b7280";

  return (
    <div
      className={`rounded-xl border p-3 transition-all duration-300 ${
        isActive
          ? "border-cyan-500/60 bg-cyan-950/30 shadow-md shadow-cyan-500/10"
          : "border-gray-700 bg-gray-900/60"
      }`}
    >
      {/* Step number + class badge */}
      <div className="flex items-center gap-2 mb-2">
        <span className="text-xs text-gray-600 font-mono w-5">{index + 1}.</span>
        <span
          className="text-xs font-mono font-bold px-2 py-0.5 rounded"
          style={{
            color: classColor,
            backgroundColor: `${classColor}18`,
            border: `1px solid ${classColor}33`,
          }}
        >
          {step.class_name}
        </span>
        <span className="text-gray-400 text-xs font-mono">
          .{step.method_name}()
        </span>
        {step.concept && (
          <span className="ml-auto text-xs text-purple-400 border border-purple-800/50 px-1.5 py-0.5 rounded shrink-0">
            {step.concept}
          </span>
        )}
      </div>

      {/* Code line */}
      <pre className="text-xs font-mono text-green-300 bg-gray-950 rounded p-2 mb-2 overflow-x-auto whitespace-pre-wrap">
        {step.code_line}
      </pre>

      {/* Description */}
      <p className="text-xs text-gray-400 leading-relaxed mb-2">
        {step.description}
      </p>

      {/* Inheritance chain */}
      {step.inheritance_chain.length > 0 && (
        <div>
          <span className="text-xs text-gray-600 mr-1">Chain:</span>
          <InheritanceChain chain={step.inheritance_chain} />
        </div>
      )}
    </div>
  );
}

// ─── Main CodeTrace panel ─────────────────────────────────────────────────────

interface CodeTracePanelProps {
  trace: CodeTrace | null;
  enemyTrace: CodeTrace | null;
  title?: string;
}

export function CodeTracePanel({ trace, enemyTrace, title = "Code Trace" }: CodeTracePanelProps) {
  const [activeStep, setActiveStep] = useState<number>(-1);
  const [activeTrace, setActiveTraceLocal] = useState<"hero" | "enemy">("hero");

  // Animate steps sequentially whenever trace changes
  useEffect(() => {
    if (!trace) {
      setActiveStep(-1);
      return;
    }
    setActiveStep(-1);
    setActiveTraceLocal("hero");
    let i = 0;
    const interval = setInterval(() => {
      setActiveStep(i);
      i++;
      if (i >= trace.steps.length) clearInterval(interval);
    }, 600);
    return () => clearInterval(interval);
  }, [trace]);

  const currentTrace = activeTrace === "hero" ? trace : enemyTrace;

  if (!trace && !enemyTrace) {
    return (
      <div className="bg-gray-900 border border-gray-700 rounded-2xl p-6 flex flex-col items-center justify-center h-64">
        <div className="text-4xl mb-3 opacity-30">🔍</div>
        <p className="text-gray-500 text-sm text-center">
          Perform an action to see the OOP code trace here.
        </p>
        <p className="text-gray-600 text-xs text-center mt-1">
          Watch which class methods fire and why.
        </p>
      </div>
    );
  }

  return (
    <div className="bg-gray-900 border border-gray-700 rounded-2xl overflow-hidden">
      {/* Header */}
      <div className="px-4 py-3 border-b border-gray-700 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
          <span className="text-white font-semibold text-sm">{title}</span>
        </div>

        {/* Hero / Enemy toggle */}
        {enemyTrace && (
          <div className="flex rounded-lg overflow-hidden border border-gray-700 text-xs">
            <button
              onClick={() => setActiveTraceLocal("hero")}
              className={`px-2 py-1 transition-colors ${
                activeTrace === "hero" ? "bg-amber-500 text-gray-900 font-bold" : "text-gray-400 hover:text-white"
              }`}
            >
              Hero
            </button>
            <button
              onClick={() => setActiveTraceLocal("enemy")}
              className={`px-2 py-1 transition-colors ${
                activeTrace === "enemy" ? "bg-red-500 text-white font-bold" : "text-gray-400 hover:text-white"
              }`}
            >
              Enemy
            </button>
          </div>
        )}
      </div>

      {currentTrace && (
        <>
          {/* Summary */}
          <div className="px-4 py-2 bg-gray-800/50 border-b border-gray-700">
            <p className="text-xs text-cyan-300 leading-relaxed">{currentTrace.summary}</p>
          </div>

          {/* Steps */}
          <div className="p-3 space-y-2 max-h-[500px] overflow-y-auto">
            {currentTrace.steps.map((step, i) => (
              <TraceStepCard
                key={`${currentTrace.action_key}-${i}`}
                step={step}
                index={i}
                isActive={activeTrace === "hero" ? i === activeStep : true}
              />
            ))}
          </div>
        </>
      )}
    </div>
  );
}
