import { NextRequest, NextResponse } from "next/server";
import { createHero, HeroClass } from "../../../lib/models/Hero";
import { createEnemy, WAVE_COMPOSITIONS, EnemyType } from "../../../lib/models/Enemy";

export async function POST(req: NextRequest) {
  try {
    const { game_state } = await req.json();
    const nextWave = (game_state.wave ?? 1) + 1;

    if (nextWave > 5) {
      return NextResponse.json({ game_state: { ...game_state, phase: "victory" } });
    }

    const heroSnap = game_state.hero;
    const hero = createHero(
      (heroSnap.hero_class ?? heroSnap.heroClass) as HeroClass,
      heroSnap.name as string
    );
    const h = hero as unknown as Record<string, unknown>;
    h["_currentHp"]     = heroSnap.current_hp ?? heroSnap.currentHp;
    h["_mana"]          = heroSnap.mana ?? heroSnap.max_mana ?? 0;
    h["_xp"]            = heroSnap.experience ?? heroSnap.xp ?? 0;
    h["_level"]         = heroSnap.level ?? 1;
    h["_statusEffects"] = [];
    hero.restoreMana(30);

    const composition = WAVE_COMPOSITIONS[nextWave] ?? ["Dragon", "Lich"];
    const enemies = composition.map((type: EnemyType) => createEnemy(type, nextWave));

    const toEnemySnap = (enemy: ReturnType<typeof createEnemy>) => {
      const s = enemy.toSnapshot() as Record<string, unknown>;
      return {
        name: s.name, class_name: s.enemyType, enemy_type: s.enemyType,
        current_hp: s.currentHp, max_hp: s.maxHp, base_damage: s.damage,
        defense: s.defense, speed: s.speed, is_alive: s.isAlive,
        hp_ratio: 1, status_effects: [], xp_reward: s.xpReward, wave_level: nextWave,
      };
    };

    const hs = hero.toSnapshot() as Record<string, unknown>;
    return NextResponse.json({
      game_state: {
        hero: {
          name: hs.name, class_name: hs.heroClass, hero_class: hs.heroClass,
          current_hp: hs.currentHp, max_hp: hs.maxHp, base_damage: hs.damage,
          defense: hs.defense, speed: hs.speed, is_alive: hs.isAlive,
          hp_ratio: (hs.currentHp as number) / (hs.maxHp as number),
          status_effects: [], mana: hs.mana, max_mana: hs.maxMana,
          mana_ratio: (hs.mana as number) / (hs.maxMana as number),
          level: hs.level, experience: hs.xp, focus_stacks: 0, wave_level: nextWave,
        },
        enemies: enemies.map(toEnemySnap),
        wave: nextWave, turn: game_state.turn ?? 1,
        phase: "player_turn", score: game_state.score ?? 0,
        levelled_up: false,
        battle_log: [`Wave ${nextWave} begins! ${enemies.map(e => e.name).join(" and ")} appear!`],
      },
    });
  } catch (e) {
    return NextResponse.json({ error: String(e) }, { status: 500 });
  }
}
