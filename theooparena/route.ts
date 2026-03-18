import { NextRequest, NextResponse } from "next/server";
import { createHero, HeroClass } from "@/lib/models/Hero";
import { createEnemy, WAVE_COMPOSITIONS } from "@/lib/models/Enemy";

export async function POST(req: NextRequest) {
  try {
    const { heroClass, heroName } = await req.json() as { heroClass: HeroClass; heroName: string };

    const hero = createHero(heroClass, heroName || "Hero");
    const enemies = WAVE_COMPOSITIONS[1].map(type => createEnemy(type, 1));

    return NextResponse.json({
      gameState: {
        hero: hero.toSnapshot(),
        enemies: enemies.map(e => e.toSnapshot()),
        wave: 1,
        phase: "player_turn",
        battleLog: [`Wave 1 begins! ${hero.name} the ${heroClass} faces ${enemies.map(e => e.name).join(" and ")}!`],
        turn: 1,
      },
    });
  } catch (e) {
    return NextResponse.json({ error: String(e) }, { status: 500 });
  }
}
