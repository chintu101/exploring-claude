import { NextRequest, NextResponse } from "next/server";
import { createEnemy, WAVE_COMPOSITIONS, EnemyType } from "@/lib/models/Enemy";
import { createHero, HeroClass } from "@/lib/models/Hero";

export async function POST(req: NextRequest) {
  try {
    const { gameState } = await req.json();
    const nextWave = gameState.wave + 1;

    if (nextWave > 5) {
      return NextResponse.json({ gameState: { ...gameState, phase: "victory" } });
    }

    const hero = (() => {
      const h = createHero(gameState.hero.heroClass as HeroClass, gameState.hero.name as string);
      (h as unknown as Record<string, unknown>)["_currentHp"] = gameState.hero.currentHp;
      (h as unknown as Record<string, unknown>)["_mana"] = gameState.hero.mana;
      (h as unknown as Record<string, unknown>)["_xp"] = gameState.hero.xp ?? 0;
      (h as unknown as Record<string, unknown>)["_level"] = gameState.hero.level ?? 1;
      (h as unknown as Record<string, unknown>)["_statusEffects"] = [];
      h.restoreMana(30); // bonus mana between waves
      return h;
    })();

    const composition = WAVE_COMPOSITIONS[nextWave] ?? ["Dragon", "Lich"] as EnemyType[];
    const enemies = composition.map(type => createEnemy(type as EnemyType, nextWave));

    return NextResponse.json({
      gameState: {
        hero: hero.toSnapshot(),
        enemies: enemies.map(e => e.toSnapshot()),
        wave: nextWave,
        phase: "player_turn",
        battleLog: [`Wave ${nextWave} begins! ${enemies.map(e => e.name).join(" and ")} appear!`],
        turn: gameState.turn,
      },
    });
  } catch (e) {
    return NextResponse.json({ error: String(e) }, { status: 500 });
  }
}
