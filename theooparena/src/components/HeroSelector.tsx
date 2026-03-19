"use client";

import { useState } from "react";
import type { HeroClass } from "../types/game";
import { HERO_META } from "../types/game";

interface HeroSelectorProps {
  onSelect: (heroClass: HeroClass, heroName: string) => void;
  isLoading: boolean;
}

const CLASS_THEMES: Record<HeroClass, { border: string; glow: string; accent: string; bg: string; icon_bg: string }> = {
  Warrior: {
    border: "border-amber-600/60 hover:border-amber-400",
    glow: "shadow-amber-500/20",
    accent: "text-amber-400",
    bg: "from-amber-950/30 to-transparent",
    icon_bg: "bg-amber-400/10 border-amber-500/30",
  },
  Mage: {
    border: "border-violet-600/60 hover:border-violet-400",
    glow: "shadow-violet-500/20",
    accent: "text-violet-400",
    bg: "from-violet-950/30 to-transparent",
    icon_bg: "bg-violet-400/10 border-violet-500/30",
  },
  Archer: {
    border: "border-teal-600/60 hover:border-teal-400",
    glow: "shadow-teal-500/20",
    accent: "text-teal-400",
    bg: "from-teal-950/30 to-transparent",
    icon_bg: "bg-teal-400/10 border-teal-500/30",
  },
};

const ACTIVE_THEMES: Record<HeroClass, { border: string; glow: string }> = {
  Warrior: { border: "border-amber-400", glow: "shadow-amber-400/40" },
  Mage:    { border: "border-violet-400", glow: "shadow-violet-400/40" },
  Archer:  { border: "border-teal-400",   glow: "shadow-teal-400/40" },
};

const STAT_COLORS: Record<string, string> = {
  hp:      "bg-rose-500",
  damage:  "bg-orange-500",
  defense: "bg-sky-500",
  mana:    "bg-violet-500",
  speed:   "bg-teal-500",
};

export function HeroSelector({ onSelect, isLoading }: HeroSelectorProps) {
  const [selected, setSelected] = useState<HeroClass | null>(null);
  const [heroName, setHeroName] = useState("");

  const handleStart = () => {
    if (!selected) return;
    onSelect(selected, heroName.trim() || "Hero");
  };

  return (
    <div
      className="min-h-screen flex flex-col items-center justify-center p-6 relative overflow-hidden"
      style={{ background: "radial-gradient(ellipse at 50% 0%, #1a0a2e 0%, #080810 60%)" }}
    >
      {/* Background runes */}
      <div className="absolute inset-0 pointer-events-none select-none overflow-hidden opacity-[0.04]">
        {["⚔", "✦", "◈", "⟡", "✦", "◈", "⚔", "⟡"].map((r, i) => (
          <span
            key={i}
            className="absolute font-display text-white"
            style={{
              fontSize: `${60 + (i % 3) * 30}px`,
              left: `${10 + i * 12}%`,
              top: `${5 + (i % 4) * 22}%`,
              transform: `rotate(${i * 17}deg)`,
            }}
          >{r}</span>
        ))}
      </div>

      {/* Title */}
      <div className="mb-12 text-center relative z-10">
        <p className="text-xs font-mono tracking-[0.4em] text-amber-500/60 uppercase mb-3">
          Object-Oriented Programming
        </p>
        <h1
          className="font-display font-black text-6xl md:text-7xl tracking-tight mb-2"
          style={{
            background: "linear-gradient(135deg, #fbbf24 0%, #f59e0b 40%, #d97706 70%, #fbbf24 100%)",
            backgroundSize: "200% auto",
            WebkitBackgroundClip: "text",
            WebkitTextFillColor: "transparent",
            textShadow: "none",
          }}
        >
          CodeQuest
        </h1>
        <p className="text-gray-400 text-lg font-light tracking-wide">
          The OOP Arena — <span className="text-amber-400/70 italic">learn by fighting</span>
        </p>
      </div>

      {/* Hero cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5 w-full max-w-4xl mb-10 relative z-10">
        {HERO_META.map((meta) => {
          const isActive = selected === meta.class;
          const theme = CLASS_THEMES[meta.class];
          const activeTheme = ACTIVE_THEMES[meta.class];

          return (
            <button
              key={meta.class}
              onClick={() => setSelected(meta.class)}
              className={`
                relative rounded-2xl border-2 p-6 text-left transition-all duration-300 overflow-hidden
                bg-[#0f0f1a]
                ${isActive
                  ? `${activeTheme.border} shadow-2xl ${activeTheme.glow}`
                  : `${theme.border} shadow-lg ${theme.glow}`
                }
              `}
            >
              {/* Card bg gradient */}
              <div
                className={`absolute inset-0 bg-gradient-to-b ${theme.bg} opacity-60 pointer-events-none`}
              />

              {/* Selected badge */}
              {isActive && (
                <span
                  className={`absolute top-3 right-3 text-xs font-mono font-bold px-2 py-1 rounded-md ${theme.accent} bg-white/5 border border-current/30`}
                >
                  ✓ CHOSEN
                </span>
              )}

              <div className="relative z-10">
                {/* Icon */}
                <div className={`w-14 h-14 rounded-xl border ${theme.icon_bg} flex items-center justify-center text-3xl mb-4 ${isActive ? "animate-float" : ""}`}>
                  {meta.icon}
                </div>

                {/* Name */}
                <div className="mb-1">
                  <span className={`font-display font-bold text-xl ${isActive ? theme.accent : "text-gray-100"} transition-colors`}>
                    {meta.class}
                  </span>
                </div>
                <p className="text-gray-500 text-xs tracking-widest uppercase font-mono mb-4">
                  {meta.tagline}
                </p>

                {/* Stat bars */}
                <div className="space-y-2 mb-5">
                  {(["hp", "damage", "defense", "mana", "speed"] as const).map((stat) => (
                    <div key={stat} className="flex items-center gap-2">
                      <span className="text-gray-600 text-xs w-14 capitalize font-mono">{stat}</span>
                      <div className="flex-1 bg-gray-800/80 rounded-full h-1.5 overflow-hidden">
                        <div
                          className={`h-full rounded-full bar-fill ${STAT_COLORS[stat]}`}
                          style={{ width: `${(meta.stats[stat] / 200) * 100}%` }}
                        />
                      </div>
                      <span className="text-gray-400 text-xs w-7 text-right font-mono">{meta.stats[stat]}</span>
                    </div>
                  ))}
                </div>

                {/* Abilities */}
                <div className="border-t border-white/5 pt-4 space-y-2">
                  <div className="flex gap-2">
                    <span className="text-xs font-mono text-cyan-500 shrink-0 mt-0.5">✦</span>
                    <p className="text-xs text-gray-300">{meta.special}</p>
                  </div>
                  <div className="flex gap-2">
                    <span className="text-xs font-mono text-purple-400 shrink-0 mt-0.5">◈</span>
                    <p className="text-xs text-gray-400">{meta.passive}</p>
                  </div>
                  <div className="mt-2 rounded-lg bg-white/3 border border-white/5 px-2 py-1.5">
                    <p className="text-xs text-gray-500 italic">{meta.oop_highlight}</p>
                  </div>
                </div>
              </div>
            </button>
          );
        })}
      </div>

      {/* Name + Start */}
      <div className="flex flex-col items-center gap-4 w-full max-w-sm relative z-10">
        <input
          type="text"
          placeholder="Name your hero…"
          maxLength={20}
          value={heroName}
          onChange={(e) => setHeroName(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleStart()}
          className="w-full px-4 py-3 rounded-xl bg-[#0f0f1a] border border-white/10 text-white placeholder-gray-600 focus:outline-none focus:border-amber-500/50 text-center font-display tracking-wider transition-colors"
        />
        <button
          onClick={handleStart}
          disabled={!selected || isLoading}
          className={`
            w-full py-4 rounded-xl font-display font-bold text-base tracking-widest uppercase transition-all duration-300
            ${selected && !isLoading
              ? "bg-gradient-to-r from-amber-600 to-amber-500 text-gray-950 hover:from-amber-500 hover:to-amber-400 shadow-lg shadow-amber-500/30 active:scale-95"
              : "bg-gray-800/60 text-gray-600 cursor-not-allowed border border-white/5"
            }
          `}
        >
          {isLoading ? "⏳ Entering dungeon…" : selected ? `Enter as ${selected} ⚔` : "Select a class"}
        </button>
      </div>

      <p className="mt-8 text-gray-700 text-sm text-center max-w-md relative z-10">
        Watch the <span className="text-cyan-500/80 font-mono text-xs">Code Trace</span> panel during battle — every action reveals the class hierarchy behind it.
      </p>
    </div>
  );
}

export default HeroSelector;
