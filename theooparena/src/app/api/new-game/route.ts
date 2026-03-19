import { NextRequest, NextResponse } from "next/server";
import { createHero, HeroClass } from "../../../lib/models/Hero";
import { createEnemy, WAVE_COMPOSITIONS } from "../../../lib/models/Enemy";

function toHeroSnap(hero: ReturnType<typeof createHero>, wave: number) {
  const s = hero.toSnapshot() as Record<string, unknown>;
  return {
    name: s.name, class_name: s.heroClass, hero_class: s.heroClass,
    current_hp: s.currentHp, max_hp: s.maxHp, base_damage: s.damage,
    defense: s.defense, speed: s.speed, is_alive: s.isAlive,
    hp_ratio: 1, status_effects: [], mana: s.mana, max_mana: s.maxMana,
    mana_ratio: 1, level: s.level, experience: s.xp,
    focus_stacks: 0, wave_level: wave,
  };
}

function toEnemySnap(enemy: ReturnType<typeof createEnemy>, wave: number) {
  const s = enemy.toSnapshot() as Record<string, unknown>;
  return {
    name: s.name, class_name: s.enemyType, enemy_type: s.enemyType,
    current_hp: s.currentHp, max_hp: s.maxHp, base_damage: s.damage,
    defense: s.defense, speed: s.speed, is_alive: s.isAlive,
    hp_ratio: 1, status_effects: [], xp_reward: s.xpReward, wave_level: wave,
  };
}

export async function POST(req: NextRequest) {
  try {
    const { hero_class, hero_name } = await req.json() as { hero_class: HeroClass; hero_name: string };
    const hero    = createHero(hero_class, hero_name || "Hero");
    const enemies = WAVE_COMPOSITIONS[1].map(type => createEnemy(type, 1));

    return NextResponse.json({
      game_state: {
        hero:       toHeroSnap(hero, 1),
        enemies:    enemies.map(e => toEnemySnap(e, 1)),
        wave: 1, turn: 1, phase: "player_turn", score: 0, levelled_up: false,
        battle_log: [`Wave 1 begins! ${hero.name} faces ${enemies.map(e => e.name).join(" and ")}!`],
      },
      message: "Game started!",
    });
  } catch (e) {
    return NextResponse.json({ error: String(e) }, { status: 500 });
  }
}
