"use client";

import { useState } from "react";
import HeroSelector from "../components/HeroSelector";
import BattleArena from "../components/BattleArena";
import CodeTracePanel from "../components/CodeTrace";
import ClassExplorer from "../components/ClassExplorer";
import { useGameState } from "../hooks/useGameState";

type SidePanel = "trace" | "explorer";

export default function Home() {
  const game = useGameState();
  const [sidePanel, setSidePanel] = useState<SidePanel>("trace");

  if (!game.gameState) {
    return <HeroSelector onSelect={game.startNewGame} isLoading={game.isLoading} />;
  }

  const { hero, enemies, wave, phase, battle_log } = game.gameState;

  return (
    <div className="min-h-screen flex flex-col" style={{ background: "#080810" }}>
      {/* Top bar */}
      <header
        className="shrink-0 flex items-center justify-between px-4 py-2.5"
        style={{ borderBottom: "1px solid #1a1a2e", background: "rgba(8,8,16,0.9)", backdropFilter: "blur(12px)" }}
      >
        <div className="flex items-center gap-3">
          <span className="font-display font-black text-lg tracking-wider" style={{ color: "#f59e0b" }}>⚔ CodeQuest</span>
          <span className="text-xs font-mono hidden sm:block" style={{ color: "#2a2a4a" }}>OOP Arena</span>
        </div>

        {/* Panel toggle */}
        <div className="flex items-center gap-1 rounded-lg p-1" style={{ background: "#0f0f1a", border: "1px solid #1a1a2e" }}>
          <button
            onClick={() => setSidePanel("trace")}
            className="px-3 py-1 rounded-md text-xs font-mono tracking-widest uppercase transition-all"
            style={sidePanel === "trace"
              ? { background: "rgba(245,158,11,0.15)", color: "#f59e0b", border: "1px solid rgba(245,158,11,0.3)" }
              : { color: "#3a3a5a", border: "1px solid transparent" }}
          >Trace</button>
          <button
            onClick={() => setSidePanel("explorer")}
            className="px-3 py-1 rounded-md text-xs font-mono tracking-widest uppercase transition-all"
            style={sidePanel === "explorer"
              ? { background: "rgba(139,92,246,0.15)", color: "#a78bfa", border: "1px solid rgba(139,92,246,0.3)" }
              : { color: "#3a3a5a", border: "1px solid transparent" }}
          >Classes</button>
        </div>

        <button
          onClick={game.resetGame}
          className="text-xs font-mono transition-colors px-2 py-1 rounded"
          style={{ color: "#3a3a5a", border: "1px solid #1a1a2e" }}
          onMouseEnter={e => (e.currentTarget.style.color = "#f87171")}
          onMouseLeave={e => (e.currentTarget.style.color = "#3a3a5a")}
        >↩ Quit</button>
      </header>

      {/* Main */}
      <main className="flex-1 flex overflow-hidden">
        {/* Battle */}
        <section className="flex-1 min-w-0 overflow-y-auto p-4 md:p-6">
          <BattleArena
            hero={hero}
            enemies={enemies}
            wave={wave}
            phase={phase}
            battleLog={battle_log}
            isLoading={game.isLoading}
            onAction={game.performAction}
            onNextWave={game.advanceWave}
            onReset={game.resetGame}
            score={hero.experience ?? 0}
          />
        </section>

        {/* Side panel (desktop) */}
        <aside className="w-[400px] shrink-0 hidden md:flex flex-col overflow-hidden" style={{ borderLeft: "1px solid #1a1a2e" }}>
          {sidePanel === "trace"
            ? <CodeTracePanel trace={game.activeTrace} enemyTrace={game.enemyTrace} />
            : <ClassExplorer />}
        </aside>
      </main>

      {/* Side panel (mobile) */}
      <section className="md:hidden max-h-64 overflow-hidden" style={{ borderTop: "1px solid #1a1a2e" }}>
        {sidePanel === "trace"
          ? <CodeTracePanel trace={game.activeTrace} enemyTrace={game.enemyTrace} />
          : <ClassExplorer />}
      </section>
    </div>
  );
}
