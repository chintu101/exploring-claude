"use client";

import type { CharacterSnapshot, PlayerAction } from "../types/game";
import { ENEMY_ICONS } from "../types/game";

// ── Resource bar ──────────────────────────────────────────────────────────────

function ResourceBar({
  current, max, colorClass, label, showText = true,
}: {
  current: number; max: number; colorClass: string; label: string; showText?: boolean;
}) {
  const pct = Math.max(0, Math.min(100, (current / max) * 100));
  return (
    <div className="w-full">
      {showText && (
        <div className="flex justify-between text-xs mb-1">
          <span className="text-gray-500 font-mono uppercase tracking-widest" style={{ fontSize: "10px" }}>{label}</span>
          <span className="text-gray-300 font-mono">{Math.ceil(current)}<span className="text-gray-600">/{max}</span></span>
        </div>
      )}
      <div className="w-full h-2 rounded-full overflow-hidden" style={{ background: "#1a1a2e" }}>
        <div
          className={`h-full rounded-full bar-fill ${colorClass}`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

// ── Hero card ─────────────────────────────────────────────────────────────────

function HeroCard({ hero }: { hero: CharacterSnapshot }) {
  const hpColor = hero.hp_ratio > 0.5 ? "bg-emerald-500" : hero.hp_ratio > 0.25 ? "bg-amber-500" : "bg-rose-500";
  const icon = hero.hero_class === "Warrior" ? "⚔️" : hero.hero_class === "Mage" ? "✨" : "🏹";

  return (
    <div
      className="relative rounded-2xl overflow-hidden p-4"
      style={{ background: "linear-gradient(135deg, #0f0f22 0%, #131326 100%)", border: "1px solid #1e1e3f" }}
    >
      {/* Subtle top glow */}
      <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-amber-500/30 to-transparent" />

      <div className="flex items-start gap-3 mb-4">
        <div
          className="w-14 h-14 rounded-xl flex items-center justify-center text-2xl shrink-0 animate-float"
          style={{ background: "rgba(245,158,11,0.08)", border: "1px solid rgba(245,158,11,0.2)" }}
        >
          {icon}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-baseline gap-2 mb-0.5">
            <span className="font-display font-bold text-white tracking-wide truncate">{hero.name}</span>
            <span
              className="text-xs font-mono shrink-0 px-1.5 py-0.5 rounded"
              style={{ background: "rgba(245,158,11,0.1)", color: "#f59e0b", border: "1px solid rgba(245,158,11,0.2)" }}
            >Lv {hero.level}</span>
          </div>
          <span className="text-gray-500 text-xs font-mono tracking-wider uppercase">{hero.hero_class}</span>
        </div>
      </div>

      <div className="space-y-2.5">
        <ResourceBar current={hero.current_hp} max={hero.max_hp} colorClass={hpColor} label="HP" />
        {hero.mana !== undefined && hero.max_mana !== undefined && (
          <ResourceBar current={hero.mana} max={hero.max_mana} colorClass="bg-violet-500" label="Mana" />
        )}
        {hero.experience !== undefined && (
          <ResourceBar
            current={(hero.experience ?? 0) % 100}
            max={100}
            colorClass="bg-fuchsia-600"
            label="XP"
          />
        )}
      </div>

      {/* Stats row */}
      <div className="mt-3 flex gap-3 text-xs font-mono">
        <span className="text-gray-600">ATK <span className="text-orange-400">{hero.base_damage}</span></span>
        <span className="text-gray-600">DEF <span className="text-sky-400">{hero.defense}</span></span>
        <span className="text-gray-600">SPD <span className="text-teal-400">{hero.speed}</span></span>
        {hero.focus_stacks !== undefined && hero.focus_stacks > 0 && (
          <span className="text-gray-600">Focus <span className="text-cyan-400">{"◈".repeat(hero.focus_stacks)}</span></span>
        )}
      </div>

      {/* Status effects */}
      {hero.status_effects.length > 0 && (
        <div className="mt-3 flex flex-wrap gap-1">
          {hero.status_effects.map((e) => (
            <span key={e} className="text-xs font-mono px-2 py-0.5 rounded-full" style={{ background: "rgba(239,68,68,0.1)", color: "#f87171", border: "1px solid rgba(239,68,68,0.2)" }}>
              {e}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

// ── Enemy card ────────────────────────────────────────────────────────────────

function EnemyCard({ enemy, index }: { enemy: CharacterSnapshot; index: number }) {
  const hpColor = enemy.hp_ratio > 0.5 ? "bg-rose-600" : enemy.hp_ratio > 0.25 ? "bg-orange-500" : "bg-yellow-500";
  const icon = ENEMY_ICONS[enemy.enemy_type as keyof typeof ENEMY_ICONS] ?? "👾";
  const isTarget = index === 0 && enemy.is_alive;

  return (
    <div
      className={`relative rounded-xl overflow-hidden p-3 transition-all duration-300 ${!enemy.is_alive ? "opacity-40 grayscale" : ""}`}
      style={{
        background: "linear-gradient(135deg, #0f0f1e 0%, #12121f 100%)",
        border: isTarget ? "1px solid rgba(239,68,68,0.5)" : "1px solid #1e1e35",
        boxShadow: isTarget ? "0 0 16px rgba(239,68,68,0.1)" : "none",
      }}
    >
      {isTarget && (
        <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-red-500/40 to-transparent" />
      )}

      <div className="flex items-center gap-2 mb-2">
        <span className="text-xl">{icon}</span>
        <div className="flex-1">
          <div className="flex items-center justify-between">
            <span className="text-gray-100 text-sm font-display font-semibold">{enemy.name}</span>
            {isTarget && (
              <span className="text-xs font-mono px-1.5 py-0.5 rounded animate-pulse-red" style={{ color: "#f87171", background: "rgba(239,68,68,0.1)", border: "1px solid rgba(239,68,68,0.25)" }}>
                TARGET
              </span>
            )}
            {!enemy.is_alive && (
              <span className="text-xs font-mono text-gray-600">SLAIN</span>
            )}
          </div>
          <span className="text-gray-600 text-xs font-mono">W{enemy.wave_level} · XP {enemy.xp_reward}</span>
        </div>
      </div>

      <ResourceBar current={enemy.current_hp} max={enemy.max_hp} colorClass={hpColor} label="HP" />

      {enemy.status_effects.length > 0 && (
        <div className="mt-2 flex flex-wrap gap-1">
          {enemy.status_effects.map((e) => (
            <span key={e} className="text-xs font-mono px-1.5 py-0.5 rounded-full" style={{ background: "rgba(251,146,60,0.1)", color: "#fb923c", border: "1px solid rgba(251,146,60,0.2)" }}>
              {e}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

// ── Action buttons ────────────────────────────────────────────────────────────

const SPECIAL_LABELS: Record<string, string> = {
  Warrior: "Whirlwind",
  Mage:    "Fireball",
  Archer:  "Rain of Arrows",
};
const SPECIAL_COSTS: Record<string, number> = { Warrior: 20, Mage: 40, Archer: 30 };
const SPECIAL_ICONS: Record<string, string> = { Warrior: "🌀", Mage: "🔥", Archer: "🏹" };

function ActionButtons({ heroClass, mana, onAction, disabled }: {
  heroClass: string; mana: number; onAction: (a: PlayerAction) => void; disabled: boolean;
}) {
  const cost = SPECIAL_COSTS[heroClass] ?? 30;
  const canSpecial = mana >= cost;

  return (
    <div className="grid grid-cols-3 gap-2 mt-2">
      {/* Attack */}
      <button
        onClick={() => onAction("basic_attack")}
        disabled={disabled}
        className="group relative py-3 px-2 rounded-xl text-sm font-display font-semibold transition-all duration-200 active:scale-95 disabled:opacity-30 disabled:cursor-not-allowed overflow-hidden"
        style={{ background: "linear-gradient(135deg, #292929, #1f1f1f)", border: "1px solid #3a3a3a" }}
      >
        <div className="absolute inset-0 bg-white/0 group-hover:bg-white/5 transition-colors rounded-xl" />
        <div className="relative">
          <div className="text-base mb-0.5">⚔️</div>
          <div className="text-gray-200 text-xs">Attack</div>
        </div>
      </button>

      {/* Special */}
      <button
        onClick={() => onAction("special_ability")}
        disabled={disabled || !canSpecial}
        title={!canSpecial ? `Need ${cost} mana` : ""}
        className="group relative py-3 px-2 rounded-xl text-xs font-display font-semibold transition-all duration-200 active:scale-95 disabled:opacity-30 disabled:cursor-not-allowed overflow-hidden"
        style={{
          background: canSpecial ? "linear-gradient(135deg, #3b1f6e, #2d1654)" : "linear-gradient(135deg, #1e1e2e, #181828)",
          border: `1px solid ${canSpecial ? "#5b21b6" : "#2a2a3e"}`,
          boxShadow: canSpecial ? "0 0 12px rgba(139,92,246,0.2)" : "none",
        }}
      >
        <div className="absolute inset-0 bg-white/0 group-hover:bg-white/5 transition-colors rounded-xl" />
        <div className="relative">
          <div className="text-base mb-0.5">{SPECIAL_ICONS[heroClass] ?? "✨"}</div>
          <div className="text-violet-200 text-xs leading-tight">{SPECIAL_LABELS[heroClass] ?? "Special"}</div>
          <div className="text-violet-400/70 text-xs mt-0.5 font-mono">{cost}mp</div>
        </div>
      </button>

      {/* Defend */}
      <button
        onClick={() => onAction("defend")}
        disabled={disabled}
        className="group relative py-3 px-2 rounded-xl text-sm font-display font-semibold transition-all duration-200 active:scale-95 disabled:opacity-30 disabled:cursor-not-allowed overflow-hidden"
        style={{ background: "linear-gradient(135deg, #0f2a2a, #0a1f1f)", border: "1px solid #134040" }}
      >
        <div className="absolute inset-0 bg-white/0 group-hover:bg-white/5 transition-colors rounded-xl" />
        <div className="relative">
          <div className="text-base mb-0.5">🛡️</div>
          <div className="text-teal-300 text-xs">Defend</div>
          <div className="text-teal-500/70 text-xs mt-0.5 font-mono">+10mp</div>
        </div>
      </button>
    </div>
  );
}

// ── Battle log ────────────────────────────────────────────────────────────────

function BattleLog({ log }: { log: string[] }) {
  const reversed = [...log].reverse();
  return (
    <div className="rounded-xl overflow-hidden" style={{ background: "#09090f", border: "1px solid #1a1a2e" }}>
      <div className="px-3 py-2 border-b" style={{ borderColor: "#1a1a2e" }}>
        <span className="text-xs font-mono tracking-widest uppercase" style={{ color: "#4a4a6a" }}>Battle Log</span>
      </div>
      <div className="p-3 h-36 overflow-y-auto space-y-1">
        {reversed.map((entry, i) => (
          <p
            key={i}
            className="text-xs font-mono leading-relaxed animate-fade-slide"
            style={{
              color: i === 0 ? "#e2e8f0" : i < 3 ? "#9198a1" : "#4a5568",
              animationDelay: `${i * 20}ms`,
            }}
          >
            <span style={{ color: "#3a3a5a" }}>›</span> {entry}
          </p>
        ))}
      </div>
    </div>
  );
}

// ── Main BattleArena ──────────────────────────────────────────────────────────

interface BattleArenaProps {
  hero: CharacterSnapshot;
  enemies: CharacterSnapshot[];
  wave: number;
  phase: string;
  battleLog: string[];
  isLoading: boolean;
  onAction: (action: PlayerAction) => void;
  onNextWave: () => void;
  onReset: () => void;
  score: number;
}

export function BattleArena({ hero, enemies, wave, phase, battleLog, isLoading, onAction, onNextWave, onReset, score }: BattleArenaProps) {
  const isPlayerTurn = phase === "player_turn" && !isLoading;

  return (
    <div className="flex flex-col gap-4 max-w-xl mx-auto">
      {/* Wave header */}
      <div className="flex items-center justify-between px-1">
        <div className="flex items-center gap-3">
          <span className="font-display font-bold text-amber-400 tracking-wider">Wave {wave}</span>
          <div className="flex gap-1.5">
            {Array.from({ length: 5 }).map((_, i) => (
              <div
                key={i}
                className="rounded-full transition-all duration-500"
                style={{
                  width: 8, height: 8,
                  background: i < wave ? "#f59e0b" : "#1e1e35",
                  boxShadow: i < wave ? "0 0 6px #f59e0b80" : "none",
                }}
              />
            ))}
          </div>
        </div>
        <div className="text-xs font-mono text-gray-600">
          XP <span className="text-amber-500">{score}</span>
        </div>
      </div>

      {/* Hero */}
      <HeroCard hero={hero} />

      {/* VS divider */}
      <div className="flex items-center gap-3">
        <div className="flex-1 h-px" style={{ background: "linear-gradient(to right, transparent, #2d1a3a)" }} />
        <span className="text-xs font-mono text-gray-700 tracking-widest px-2">VS</span>
        <div className="flex-1 h-px" style={{ background: "linear-gradient(to left, transparent, #1a2d3a)" }} />
      </div>

      {/* Enemies */}
      <div className="space-y-2">
        {enemies.map((enemy, i) => (
          <EnemyCard key={enemy.name + i} enemy={enemy} index={i} />
        ))}
      </div>

      {/* Actions */}
      {phase === "player_turn" && (
        <ActionButtons
          heroClass={hero.hero_class ?? "Warrior"}
          mana={hero.mana ?? 0}
          onAction={onAction}
          disabled={!isPlayerTurn}
        />
      )}

      {/* Loading */}
      {isLoading && (
        <div className="flex items-center justify-center gap-2 py-1">
          <div className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-bounce" style={{ animationDelay: "0ms" }} />
          <div className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-bounce" style={{ animationDelay: "150ms" }} />
          <div className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-bounce" style={{ animationDelay: "300ms" }} />
        </div>
      )}

      {/* Wave complete */}
      {phase === "wave_complete" && (
        <div className="text-center py-5 rounded-2xl" style={{ background: "linear-gradient(135deg, #0a1f0a, #0d1a0d)", border: "1px solid #1a3d1a" }}>
          <p className="font-display font-bold text-emerald-400 text-lg mb-1">✦ Wave {wave} Complete ✦</p>
          <p className="text-gray-500 text-sm mb-4 font-light">Your hero grows stronger.</p>
          <button
            onClick={onNextWave}
            disabled={isLoading}
            className="px-8 py-3 font-display font-bold tracking-widest uppercase text-sm rounded-xl transition-all active:scale-95 disabled:opacity-40"
            style={{ background: "linear-gradient(135deg, #166534, #14532d)", border: "1px solid #16a34a40", color: "#86efac" }}
          >
            Enter Wave {wave + 1} →
          </button>
        </div>
      )}

      {/* Victory */}
      {phase === "victory" && (
        <div className="text-center py-6 rounded-2xl" style={{ background: "linear-gradient(135deg, #1a1200, #140e00)", border: "1px solid #f59e0b30" }}>
          <div className="text-4xl mb-3 animate-float">🏆</div>
          <p className="font-display font-black text-2xl text-amber-400 tracking-wider mb-1">VICTORY</p>
          <p className="text-gray-500 text-sm mb-4">Final XP: <span className="text-amber-400 font-mono">{score}</span></p>
          <button onClick={onReset} className="px-8 py-3 font-display font-bold tracking-widest uppercase text-sm rounded-xl transition-all active:scale-95" style={{ background: "linear-gradient(135deg, #92400e, #78350f)", border: "1px solid #f59e0b40", color: "#fbbf24" }}>
            Play Again
          </button>
        </div>
      )}

      {/* Defeat */}
      {phase === "defeat" && (
        <div className="text-center py-6 rounded-2xl" style={{ background: "linear-gradient(135deg, #1a0505, #120303)", border: "1px solid #ef444430" }}>
          <div className="text-4xl mb-3">💀</div>
          <p className="font-display font-black text-2xl text-rose-500 tracking-wider mb-1">DEFEATED</p>
          <p className="text-gray-600 text-sm mb-4 font-light italic">The dungeon claims another soul.</p>
          <button onClick={onReset} className="px-8 py-3 font-display font-bold tracking-widest uppercase text-sm rounded-xl transition-all active:scale-95" style={{ background: "linear-gradient(135deg, #7f1d1d, #6b1a1a)", border: "1px solid #ef444430", color: "#fca5a5" }}>
            Try Again
          </button>
        </div>
      )}

      <BattleLog log={battleLog} />
    </div>
  );
}

export default BattleArena;
