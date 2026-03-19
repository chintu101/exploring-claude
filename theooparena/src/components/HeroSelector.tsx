"use client";

import { useState } from "react";
import type { HeroClass } from "../types/game";
import { HERO_META } from "../types/game";

interface HeroSelectorProps {
  onSelect: (heroClass: HeroClass, heroName: string) => void;
  isLoading: boolean;
}

export function HeroSelector({ onSelect, isLoading }: HeroSelectorProps) {
  const [selected, setSelected] = useState<HeroClass | null>(null);
  const [heroName, setHeroName] = useState("");

  const handleStart = () => {
    if (!selected) return;
    onSelect(selected, heroName.trim() || "Hero");
  };

  return (
    <div className="min-h-screen flex flex-col items-center justify-center p-6 bg-gray-950">
      {/* Title */}
      <div className="mb-10 text-center">
        <h1 className="text-5xl font-bold text-amber-400 tracking-tight mb-2" style={{ fontFamily: "'Cinzel', serif" }}>
          CodeQuest
        </h1>
        <p className="text-gray-400 text-lg">The OOP Arena — learn code by playing</p>
      </div>

      {/* Hero cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 w-full max-w-4xl mb-8">
        {HERO_META.map((meta) => {
          const isActive = selected === meta.class;
          return (
            <button
              key={meta.class}
              onClick={() => setSelected(meta.class)}
              className={`
                relative rounded-2xl border-2 p-6 text-left transition-all duration-200
                ${isActive
                  ? "border-amber-400 bg-gray-800 shadow-lg shadow-amber-400/20"
                  : "border-gray-700 bg-gray-900 hover:border-gray-500 hover:bg-gray-800"
                }
              `}
            >
              {isActive && (
                <span className="absolute top-3 right-3 text-xs font-bold text-amber-400 bg-amber-400/10 px-2 py-1 rounded">
                  Selected
                </span>
              )}

              {/* Icon + Name */}
              <div className="flex items-center gap-3 mb-4">
                <span className="text-4xl">{meta.icon}</span>
                <div>
                  <div className="text-white font-bold text-lg">{meta.class}</div>
                  <div className="text-gray-400 text-sm">{meta.tagline}</div>
                </div>
              </div>

              {/* Stats */}
              <div className="space-y-1.5 mb-4">
                {(["hp", "damage", "defense", "mana", "speed"] as const).map((stat) => (
                  <div key={stat} className="flex items-center gap-2">
                    <span className="text-gray-500 text-xs w-14 capitalize">{stat}</span>
                    <div className="flex-1 bg-gray-700 rounded-full h-1.5">
                      <div
                        className="h-1.5 rounded-full bg-amber-400 transition-all"
                        style={{ width: `${(meta.stats[stat] / 200) * 100}%` }}
                      />
                    </div>
                    <span className="text-gray-300 text-xs w-8 text-right">{meta.stats[stat]}</span>
                  </div>
                ))}
              </div>

              {/* Special + OOP note */}
              <div className="border-t border-gray-700 pt-3 space-y-2">
                <p className="text-xs text-cyan-400">
                  <span className="font-semibold">Special:</span> {meta.special}
                </p>
                <p className="text-xs text-purple-400">
                  <span className="font-semibold">Passive:</span> {meta.passive}
                </p>
                <p className="text-xs text-gray-500 italic">
                  OOP: {meta.oop_highlight}
                </p>
              </div>
            </button>
          );
        })}
      </div>

      {/* Name input + Start */}
      <div className="flex flex-col items-center gap-4 w-full max-w-sm">
        <input
          type="text"
          placeholder="Enter your hero's name…"
          maxLength={20}
          value={heroName}
          onChange={(e) => setHeroName(e.target.value)}
          className="w-full px-4 py-3 rounded-xl bg-gray-800 border border-gray-600 text-white placeholder-gray-500 focus:outline-none focus:border-amber-400 text-center"
        />
        <button
          onClick={handleStart}
          disabled={!selected || isLoading}
          className={`
            w-full py-3.5 rounded-xl font-bold text-lg tracking-wide transition-all duration-200
            ${selected
              ? "bg-amber-400 text-gray-900 hover:bg-amber-300 active:scale-95"
              : "bg-gray-700 text-gray-500 cursor-not-allowed"
            }
          `}
        >
          {isLoading ? "Entering dungeon…" : selected ? `Enter as ${selected}` : "Select a class"}
        </button>
      </div>

      {/* Subtitle note */}
      <p className="mt-8 text-gray-600 text-sm text-center max-w-md">
        Watch the <span className="text-cyan-400">Code Trace</span> panel as you fight — every action shows you which class method runs and why.
      </p>
    </div>
  );
}

export default HeroSelector;
