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
    return (
      <HeroSelector
        onSelect={game.startNewGame}
        isLoading={game.isLoading}
      />
    );
  }

  const { hero, enemies, wave, phase, battle_log } = game.gameState;

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100 flex flex-col">
      <header className="border-b border-gray-800 bg-gray-900/80 backdrop-blur px-4 py-2 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className="text-amber-400 text-xl font-black tracking-tight">⚔ CodeQuest</span>
          <span className="text-xs text-gray-500 hidden sm:block">OOP Arena</span>
        </div>
        <div className="flex items-center gap-1 bg-gray-800 rounded-lg p-1">
          <button
            onClick={() => setSidePanel("trace")}
            className={`px-3 py-1 rounded-md text-xs font-semibold transition-colors ${
              sidePanel === "trace" ? "bg-amber-500 text-gray-950" : "text-gray-400 hover:text-gray-200"
            }`}
          >Code Trace</button>
          <button
            onClick={() => setSidePanel("explorer")}
            className={`px-3 py-1 rounded-md text-xs font-semibold transition-colors ${
              sidePanel === "explorer" ? "bg-violet-500 text-white" : "text-gray-400 hover:text-gray-200"
            }`}
          >Class Explorer</button>
        </div>
        <button
          onClick={game.resetGame}
          className="text-xs text-gray-500 hover:text-red-400 transition-colors px-2 py-1 rounded border border-gray-700 hover:border-red-700"
        >↩ New Hero</button>
      </header>

      <main className="flex-1 flex overflow-hidden">
        <section className="flex-1 min-w-0 overflow-y-auto p-4">
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
        <aside className="w-[420px] min-w-[320px] max-w-[480px] border-l border-gray-800 overflow-y-auto hidden md:block">
          {sidePanel === "trace"
            ? <CodeTracePanel trace={game.activeTrace} enemyTrace={game.enemyTrace} />
            : <ClassExplorer />}
        </aside>
      </main>

      <section className="md:hidden border-t border-gray-800 max-h-72 overflow-y-auto">
        {sidePanel === "trace"
          ? <CodeTracePanel trace={game.activeTrace} enemyTrace={game.enemyTrace} />
          : <ClassExplorer />}
      </section>
    </div>
  );
}
