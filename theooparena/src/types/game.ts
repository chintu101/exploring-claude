// CodeQuest — TypeScript type definitions
// All types mirror the Pydantic schemas in api/schemas.py

export type HeroClass = "Warrior" | "Mage" | "Archer";
export type EnemyType = "Goblin" | "Troll" | "Dragon" | "Lich";
export type GamePhase =
  | "hero_select"
  | "player_turn"
  | "enemy_turn"
  | "wave_complete"
  | "victory"
  | "defeat";

export type PlayerAction = "basic_attack" | "special_ability" | "defend";

// ─── Character snapshot ───────────────────────────────────────────────────────

export interface CharacterSnapshot {
  name: string;
  class_name: string;
  current_hp: number;
  max_hp: number;
  base_damage: number;
  defense: number;
  speed: number;
  is_alive: boolean;
  hp_ratio: number;
  status_effects: string[];

  // Hero-only
  hero_class?: HeroClass;
  mana?: number;
  max_mana?: number;
  mana_ratio?: number;
  level?: number;
  experience?: number;
  xp_to_next?: number;
  rage_charges?: number;
  spell_power?: number;
  crit_chance?: number;
  focus_stacks?: number;

  // Enemy-only
  enemy_type?: EnemyType;
  xp_reward?: number;
  wave_level?: number;
  fire_charges?: number;
}

// ─── Game state ───────────────────────────────────────────────────────────────

export interface GameState {
  hero: CharacterSnapshot;
  enemies: CharacterSnapshot[];
  wave: number;
  turn: number;
  phase: GamePhase;
  battle_log: string[];
  score: number;
  levelled_up: boolean;
}

// ─── Code trace ───────────────────────────────────────────────────────────────

export interface TraceStep {
  class_name: string;
  method_name: string;
  code_line: string;
  description: string;
  inheritance_chain: string[];
  concept: string;
}

export interface CodeTrace {
  steps: TraceStep[];
  action_key: string;
  summary: string;
}

// ─── API responses ────────────────────────────────────────────────────────────

export interface ActionResult {
  action: string;
  source: string;
  target: string;
  value: number;
  message: string;
  is_crit: boolean;
  extra: Record<string, unknown>;
}

export interface ActionResponse {
  game_state: GameState;
  action_result: ActionResult;
  code_trace: CodeTrace;
  enemy_action_result: ActionResult | null;
  enemy_code_trace: CodeTrace | null;
  levelled_up: boolean;
  status_messages: string[];
}

export interface NewGameResponse {
  game_state: GameState;
  message: string;
}

// ─── Class hierarchy (ClassExplorer) ─────────────────────────────────────────

export interface ClassNode {
  name: string;
  class_name: string;
  type: "abstract" | "concrete";
  description: string;
  children?: ClassNode[];
}

export interface OopConcept {
  name: string;
  description: string;
  example: string;
}

export interface ClassHierarchyResponse {
  hierarchy: ClassNode;
  concepts: OopConcept[];
}

// ─── Hero selection metadata ──────────────────────────────────────────────────

export interface HeroMeta {
  class: HeroClass;
  icon: string;
  tagline: string;
  stats: {
    hp: number;
    damage: number;
    defense: number;
    mana: number;
    speed: number;
  };
  special: string;
  passive: string;
  oop_highlight: string;
}

export const HERO_META: HeroMeta[] = [
  {
    class: "Warrior",
    icon: "⚔️",
    tagline: "The Berserker",
    stats: { hp: 150, damage: 20, defense: 8, mana: 50, speed: 6 },
    special: "Whirlwind Strike — 150% damage, builds rage",
    passive: "Berserker — more damage at low HP",
    oop_highlight: "Overrides calculate_base_damage() with rage scaling",
  },
  {
    class: "Mage",
    icon: "✨",
    tagline: "The Arcanist",
    stats: { hp: 80, damage: 12, defense: 3, mana: 200, speed: 8 },
    special: "Fireball — 200% spell power, may burn",
    passive: "Mana Flow — damage scales with mana %",
    oop_highlight: "Overrides basic_attack() — magic bypasses armor",
  },
  {
    class: "Archer",
    icon: "🏹",
    tagline: "The Sharpshooter",
    stats: { hp: 100, damage: 15, defense: 5, mana: 80, speed: 12 },
    special: "Rain of Arrows — guaranteed crit, bleeds",
    passive: "Focus — each non-crit raises crit chance 5%",
    oop_highlight: "Overrides calculate_base_damage() with crit system",
  },
];

export const ENEMY_ICONS: Record<EnemyType, string> = {
  Goblin: "👺",
  Troll: "🪨",
  Dragon: "🐲",
  Lich: "💀",
};

export const CLASS_COLORS: Record<string, string> = {
  Entity: "#6b7280",
  Character: "#0f766e",
  Hero: "#7c3aed",
  Enemy: "#dc2626",
  Warrior: "#b45309",
  Mage: "#7c3aed",
  Archer: "#065f46",
  Goblin: "#991b1b",
  Troll: "#854d0e",
  Dragon: "#dc2626",
  Lich: "#4c1d95",
};
