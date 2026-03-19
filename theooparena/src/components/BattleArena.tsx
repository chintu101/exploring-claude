"use client";

import type { CharacterSnapshot, PlayerAction } from "../types/game";
import { ENEMY_ICONS } from "../types/game";

// ─── HP / Mana bar ────────────────────────────────────────────────────────────

function ResourceBar({
  current,
  max,
  color,
  label,
}: {
  current: number;
  max: number;
  color: string;
  label: string;
}) {
  const pct = Math.max(0, Math.min(100, (current / max) * 100));
  return (
    <div className="w-full">
      <div className="flex justify-between text-xs text-gray-400 mb-0.5">
        <span>{label}</span>
        <span>
          {current}/{max}
        </span>
      </div>
      <div className="w-full h-2 bg-gray-700 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-500 ${color}`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

// ─── Hero card ────────────────────────────────────────────────────────────────

function HeroCard({ hero }: { hero: CharacterSnapshot }) {
  const hpColor =
    hero.hp_ratio > 0.5
      ? "bg-green-500"
      : hero.hp_ratio > 0.25
      ? "bg-yellow-500"
      : "bg-red-500";

  return (
    <div className="bg-gray-900 border border-gray-700 rounded-2xl p-4">
      <div className="flex items-center gap-3 mb-4">
        <div className="w-12 h-12 rounded-full bg-amber-400/20 border border-amber-400/40 flex items-center justify-center text-2xl">
          {hero.hero_class === "Warrior" ? "⚔️" : hero.hero_class === "Mage" ? "✨" : "🏹"}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-baseline gap-2">
            <span className="text-white font-bold truncate">{hero.name}</span>
            <span className="text-xs text-amber-400 shrink-0">Lv {hero.level}</span>
          </div>
          <span className="text-gray-400 text-xs">{hero.hero_class}</span>
        </div>
      </div>

      <div className="space-y-2">
        <ResourceBar current={hero.current_hp} max={hero.max_hp} color={hpColor} label="HP" />
        {hero.mana !== undefined && hero.max_mana !== undefined && (
          <ResourceBar current={hero.mana} max={hero.max_mana} color="bg-blue-500" label="Mana" />
        )}

        {/* XP bar */}
        {hero.experience !== undefined && hero.xp_to_next !== undefined && (
          <ResourceBar
            current={hero.experience % (hero.xp_to_next || 100)}
            max={hero.xp_to_next}
            color="bg-purple-500"
            label="XP"
          />
        )}
      </div>

      {/* Status effects */}
      {hero.status_effects.length > 0 && (
        <div className="mt-3 flex flex-wrap gap-1">
          {hero.status_effects.map((e) => (
            <span key={e} className="text-xs px-2 py-0.5 rounded-full bg-red-900/50 text-red-400 border border-red-800">
              {e}
            </span>
          ))}
        </div>
      )}

      {/* Class-specific stats */}
      <div className="mt-3 grid grid-cols-2 gap-1 text-xs text-gray-500">
        <span>ATK: <span className="text-gray-300">{hero.base_damage}</span></span>
        <span>DEF: <span className="text-gray-300">{hero.defense}</span></span>
        <span>SPD: <span className="text-gray-300">{hero.speed}</span></span>
        {hero.rage_charges !== undefined && (
          <span>Rage: <span className="text-amber-400">{hero.rage_charges}⚡</span></span>
        )}
        {hero.crit_chance !== undefined && (
          <span>Crit: <span className="text-cyan-400">{Math.round(hero.crit_chance * 100)}%</span></span>
        )}
        {hero.spell_power !== undefined && (
          <span>SP: <span className="text-purple-400">{hero.spell_power}</span></span>
        )}
      </div>
    </div>
  );
}

// ─── Enemy card ───────────────────────────────────────────────────────────────

function EnemyCard({ enemy, index }: { enemy: CharacterSnapshot; index: number }) {
  const hpColor =
    enemy.hp_ratio > 0.5
      ? "bg-red-600"
      : enemy.hp_ratio > 0.25
      ? "bg-orange-500"
      : "bg-yellow-500";

  const icon = ENEMY_ICONS[enemy.enemy_type as keyof typeof ENEMY_ICONS] ?? "👾";

  return (
    <div
      className={`bg-gray-900 border rounded-xl p-3 transition-all ${
        index === 0 ? "border-red-500/60" : "border-gray-700"
      }`}
    >
      <div className="flex items-center gap-2 mb-2">
        <span className="text-2xl">{icon}</span>
        <div>
          <div className="text-white text-sm font-semibold">{enemy.name}</div>
          <div className="text-gray-500 text-xs">Wave {enemy.wave_level}</div>
        </div>
        {index === 0 && (
          <span className="ml-auto text-xs text-red-400 border border-red-400/30 px-1.5 py-0.5 rounded">
            TARGET
          </span>
        )}
      </div>
      <ResourceBar current={enemy.current_hp} max={enemy.max_hp} color={hpColor} label="HP" />
      {enemy.status_effects.length > 0 && (
        <div className="mt-2 flex flex-wrap gap-1">
          {enemy.status_effects.map((e) => (
            <span key={e} className="text-xs px-1.5 py-0.5 rounded-full bg-orange-900/50 text-orange-400 border border-orange-800">
              {e}
            </span>
          ))}
        </div>
      )}
      <div className="mt-2 grid grid-cols-3 gap-1 text-xs text-gray-500">
        <span>ATK: <span className="text-gray-300">{enemy.base_damage}</span></span>
        <span>DEF: <span className="text-gray-300">{enemy.defense}</span></span>
        <span>XP: <span className="text-yellow-400">{enemy.xp_reward}</span></span>
      </div>
    </div>
  );
}

// ─── Action buttons ───────────────────────────────────────────────────────────

interface ActionButtonsProps {
  heroClass: string;
  mana: number;
  onAction: (action: PlayerAction) => void;
  disabled: boolean;
}

function ActionButtons({ heroClass, mana, onAction, disabled }: ActionButtonsProps) {
  const specialCost = heroClass === "Warrior" ? 20 : heroClass === "Mage" ? 40 : 30;
  const canSpecial = mana >= specialCost;

  const specialLabel: Record<string, string> = {
    Warrior: "Whirlwind Strike",
    Mage: "Fireball",
    Archer: "Rain of Arrows",
  };

  return (
    <div className="grid grid-cols-3 gap-3 mt-4">
      <button
        onClick={() => onAction("basic_attack")}
        disabled={disabled}
        className="py-3 rounded-xl bg-gray-700 hover:bg-gray-600 disabled:opacity-40 disabled:cursor-not-allowed text-white font-semibold text-sm transition-all active:scale-95"
      >
        ⚔️ Attack
      </button>

      <button
        onClick={() => onAction("special_ability")}
        disabled={disabled || !canSpecial}
        title={!canSpecial ? `Need ${specialCost} mana` : ""}
        className="py-3 rounded-xl bg-purple-800 hover:bg-purple-700 disabled:opacity-40 disabled:cursor-not-allowed text-white font-semibold text-xs transition-all active:scale-95"
      >
        ✨ {specialLabel[heroClass] ?? "Special"}
        <div className="text-purple-300 text-xs mt-0.5">{specialCost} mana</div>
      </button>

      <button
        onClick={() => onAction("defend")}
        disabled={disabled}
        className="py-3 rounded-xl bg-teal-800 hover:bg-teal-700 disabled:opacity-40 disabled:cursor-not-allowed text-white font-semibold text-sm transition-all active:scale-95"
      >
        🛡️ Defend
      </button>
    </div>
  );
}

// ─── Battle log ───────────────────────────────────────────────────────────────

function BattleLog({ log }: { log: string[] }) {
  return (
    <div className="bg-gray-900 border border-gray-700 rounded-xl p-3 h-40 overflow-y-auto">
      <div className="text-xs text-gray-500 mb-2 font-mono">BATTLE LOG</div>
      <div className="space-y-1">
        {[...log].reverse().map((entry, i) => (
          <p
            key={i}
            className={`text-xs font-mono ${
              i === 0 ? "text-white" : i < 3 ? "text-gray-300" : "text-gray-500"
            }`}
          >
            {entry}
          </p>
        ))}
      </div>
    </div>
  );
}

// ─── Main BattleArena ─────────────────────────────────────────────────────────

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

export function BattleArena({
  hero,
  enemies,
  wave,
  phase,
  battleLog,
  isLoading,
  onAction,
  onNextWave,
  onReset,
  score,
}: BattleArenaProps) {
  const isPlayerTurn = phase === "player_turn" && !isLoading;

  return (
    <div className="flex flex-col gap-4">
      {/* Wave + score header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className="text-amber-400 font-bold text-lg">Wave {wave}/5</span>
          <div className="flex gap-1">
            {Array.from({ length: 5 }).map((_, i) => (
              <div
                key={i}
                className={`w-3 h-3 rounded-full ${i < wave ? "bg-amber-400" : "bg-gray-700"}`}
              />
            ))}
          </div>
        </div>
        <div className="text-gray-400 text-sm">
          Score: <span className="text-amber-400 font-bold">{score.toLocaleString()}</span>
        </div>
      </div>

      {/* Characters */}
      <HeroCard hero={hero} />

      <div className="text-center text-gray-600 text-xs">⚔️ VS ⚔️</div>

      <div className="space-y-2">
        {enemies.map((enemy, i) => (
          <EnemyCard key={enemy.name + i} enemy={enemy} index={i} />
        ))}
      </div>

      {/* Actions / Phase messages */}
      {phase === "player_turn" && (
        <ActionButtons
          heroClass={hero.hero_class ?? "Warrior"}
          mana={hero.mana ?? 0}
          onAction={onAction}
          disabled={!isPlayerTurn}
        />
      )}

      {phase === "wave_complete" && (
        <div className="text-center py-4">
          <p className="text-green-400 font-bold mb-3">✅ Wave {wave} Complete!</p>
          <button
            onClick={onNextWave}
            disabled={isLoading}
            className="px-6 py-3 bg-green-600 hover:bg-green-500 text-white font-bold rounded-xl transition-all active:scale-95 disabled:opacity-50"
          >
            Enter Wave {wave + 1} →
          </button>
        </div>
      )}

      {phase === "victory" && (
        <div className="text-center py-4 bg-amber-400/10 border border-amber-400/30 rounded-xl">
          <p className="text-amber-400 font-bold text-xl mb-1">🏆 VICTORY!</p>
          <p className="text-gray-300 text-sm mb-3">Score: {score.toLocaleString()}</p>
          <button onClick={onReset} className="px-6 py-2 bg-amber-400 text-gray-900 font-bold rounded-xl hover:bg-amber-300 transition-all">
            Play Again
          </button>
        </div>
      )}

      {phase === "defeat" && (
        <div className="text-center py-4 bg-red-900/20 border border-red-700/30 rounded-xl">
          <p className="text-red-400 font-bold text-xl mb-1">💀 Defeated</p>
          <p className="text-gray-400 text-sm mb-3">Score: {score.toLocaleString()}</p>
          <button onClick={onReset} className="px-6 py-2 bg-red-700 text-white font-bold rounded-xl hover:bg-red-600 transition-all">
            Try Again
          </button>
        </div>
      )}

      {isLoading && (
        <div className="text-center py-2">
          <span className="text-amber-400 animate-pulse text-sm">Processing…</span>
        </div>
      )}

      {/* Battle log */}
      <BattleLog log={battleLog} />
    </div>
  );
}

export default BattleArena;
