"use client";

import { useState } from "react";
import HeroSelector from "@/components/HeroSelector";
import BattleArena from "@/components/BattleArena";
import CodeTrace from "@/components/CodeTrace";
import ClassExplorer from "@/components/ClassExplorer";
import { useGameState } from "@/hooks/useGameState";

type SidePanel = "trace" | "explorer";

export default function Home() {
  const game = useGameState();
  const [sidePanel, setSidePanel] = useState<SidePanel>("trace");

  // ── Hero selection phase ──────────────────────────────────────────────────
  if (!game.gameState) {
    return (
      <HeroSelector
        onStart={game.startNewGame}
        isLoading={game.isLoading}
        error={game.error}
        onClearError={game.clearError}
      />
    );
  }

  // ── Main battle layout ────────────────────────────────────────────────────
  return (
    <div className="min-h-screen bg-gray-950 text-gray-100 flex flex-col">
      {/* ── Top bar ── */}
      <header className="border-b border-gray-800 bg-gray-900/80 backdrop-blur px-4 py-2 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className="text-amber-400 text-xl font-black tracking-tight">
            ⚔ CodeQuest
          </span>
          <span className="text-xs text-gray-500 hidden sm:block">
            OOP Arena — learn by fighting
          </span>
        </div>

        {/* Panel switcher (mobile / narrow) */}
        <div className="flex items-center gap-1 bg-gray-800 rounded-lg p-1">
          <button
            onClick={() => setSidePanel("trace")}
            className={`px-3 py-1 rounded-md text-xs font-semibold transition-colors ${
              sidePanel === "trace"
                ? "bg-amber-500 text-gray-950"
                : "text-gray-400 hover:text-gray-200"
            }`}
          >
            Code Trace
          </button>
          <button
            onClick={() => setSidePanel("explorer")}
            className={`px-3 py-1 rounded-md text-xs font-semibold transition-colors ${
              sidePanel === "explorer"
                ? "bg-violet-500 text-white"
                : "text-gray-400 hover:text-gray-200"
            }`}
          >
            Class Explorer
          </button>
        </div>

        <button
          onClick={game.resetGame}
          className="text-xs text-gray-500 hover:text-red-400 transition-colors px-2 py-1 rounded border border-gray-700 hover:border-red-700"
        >
          ↩ New Hero
        </button>
      </header>

      {/* ── Main content ── */}
      <main className="flex-1 flex overflow-hidden">
        {/* Left — battle arena (always visible) */}
        <section className="flex-1 min-w-0 overflow-y-auto p-4">
          <BattleArena
            gameState={game.gameState}
            lastActionResult={game.lastActionResult}
            isLoading={game.isLoading}
            error={game.error}
            onAction={game.performAction}
            onAdvanceWave={game.advanceWave}
            onReset={game.resetGame}
            onClearError={game.clearError}
          />
        </section>

        {/* Right — side panel (Code Trace OR Class Explorer) */}
        <aside className="w-[420px] min-w-[320px] max-w-[480px] border-l border-gray-800 overflow-y-auto hidden md:block">
          {sidePanel === "trace" ? (
            <CodeTrace
              playerTrace={game.activeTrace}
              enemyTrace={game.enemyTrace}
            />
          ) : (
            <ClassExplorer />
          )}
        </aside>
      </main>

      {/* ── Mobile bottom panel ── */}
      <section className="md:hidden border-t border-gray-800 max-h-72 overflow-y-auto">
        {sidePanel === "trace" ? (
          <CodeTrace
            playerTrace={game.activeTrace}
            enemyTrace={game.enemyTrace}
          />
        ) : (
          <ClassExplorer />
        )}
      </section>
    </div>
  );
}
