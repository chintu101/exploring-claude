import { NextRequest, NextResponse } from "next/server";
import { createHero, HeroClass, Hero, Warrior, Mage, Archer } from "@/lib/models/Hero";
import { createEnemy, Enemy, EnemyType, Goblin, Troll, Dragon, Lich } from "@/lib/models/Enemy";
import { Character } from "@/lib/models/Character";
import { TraceService } from "@/lib/services/TraceService";

// ── Rehydrate hero from snapshot ──────────────────────────────────────────────
function rehydrateHero(snap: Record<string, unknown>): Hero {
  const hero = createHero(snap.heroClass as HeroClass, snap.name as string);
  // Restore state
  (hero as unknown as Record<string, unknown>)["_currentHp"] = snap.currentHp;
  (hero as unknown as Record<string, unknown>)["_mana"] = snap.mana;
  (hero as unknown as Record<string, unknown>)["_xp"] = snap.xp ?? 0;
  (hero as unknown as Record<string, unknown>)["_level"] = snap.level ?? 1;
  (hero as unknown as Record<string, unknown>)["_statusEffects"] = snap.statusEffects ?? [];
  if (snap.heroClass === "Archer") {
    (hero as unknown as Record<string, unknown>)["_focusStacks"] = (snap as Record<string, unknown>).focusStacks ?? 0;
  }
  return hero;
}

// ── Rehydrate enemy from snapshot ─────────────────────────────────────────────
function rehydrateEnemy(snap: Record<string, unknown>): Enemy {
  const enemy = createEnemy(snap.enemyType as EnemyType, 1);
  (enemy as unknown as Record<string, unknown>)["_maxHp"] = snap.maxHp;
  (enemy as unknown as Record<string, unknown>)["_currentHp"] = snap.currentHp;
  (enemy as unknown as Record<string, unknown>)["_damage"] = snap.damage;
  (enemy as unknown as Record<string, unknown>)["_defense"] = snap.defense;
  (enemy as unknown as Record<string, unknown>)["_statusEffects"] = snap.statusEffects ?? [];
  if (snap.enemyType === "Dragon") {
    (enemy as unknown as Record<string, unknown>)["_breathCharges"] = (snap as Record<string, unknown>).breathCharges ?? 3;
  }
  return enemy;
}

export async function POST(req: NextRequest) {
  try {
    const { gameState, action, targetIndex = 0 } = await req.json();

    const hero = rehydrateHero(gameState.hero);
    const enemies: Enemy[] = gameState.enemies.map(rehydrateEnemy);
    const log: string[] = [...(gameState.battleLog ?? [])];
    const aliveEnemies = enemies.filter(e => e.isAlive);

    if (aliveEnemies.length === 0) {
      return NextResponse.json({ gameState: { ...gameState, phase: "wave_complete" }, playerTrace: null, enemyTrace: null });
    }

    const target = aliveEnemies[Math.min(targetIndex, aliveEnemies.length - 1)];

    // ── Player action ──────────────────────────────────────────────────────
    let playerResult;
    if (action === "basic_attack") {
      playerResult = hero.basicAttack(target);
    } else if (action === "special_ability") {
      playerResult = hero.specialAbility(target);
    } else {
      playerResult = hero.defend();
    }
    log.push(playerResult.logEntry);

    // Status ticks on enemies after player acts
    for (const e of aliveEnemies) {
      const ticks = e.tickStatusEffects();
      log.push(...ticks);
    }

    const playerTrace = TraceService.getTrace(playerResult.actionKey);

    // ── Check if all enemies dead ──────────────────────────────────────────
    const stillAlive = enemies.filter(e => e.isAlive);
    if (stillAlive.length === 0) {
      const xpGain = gameState.enemies.reduce((s: number, e: Record<string, unknown>) => s + ((e.xpReward as number) ?? 0), 0);
      hero.gainXp(xpGain);
      log.push(`All enemies defeated! ${hero.name} gains ${xpGain} XP!`);

      return NextResponse.json({
        gameState: {
          hero: hero.toSnapshot(),
          enemies: enemies.map(e => e.toSnapshot()),
          wave: gameState.wave,
          phase: "wave_complete",
          battleLog: log.slice(-20),
          turn: gameState.turn + 1,
        },
        playerTrace,
        enemyTrace: null,
        actionResult: playerResult,
      });
    }

    // ── Enemy counter-attack ───────────────────────────────────────────────
    const attacker = stillAlive[0];
    const enemyResult = attacker.decideAction(hero);
    log.push(enemyResult.logEntry);
    const enemyTrace = TraceService.getTrace(enemyResult.actionKey);

    // Hero status ticks
    const heroTicks = hero.tickStatusEffects();
    log.push(...heroTicks);

    // ── Check win / lose ───────────────────────────────────────────────────
    let phase = "player_turn";
    if (!hero.isAlive) {
      phase = "defeat";
      log.push(`${hero.name} has fallen...`);
    } else if (enemies.filter(e => e.isAlive).length === 0) {
      phase = "wave_complete";
      const xpGain = gameState.enemies.reduce((s: number, e: Record<string, unknown>) => s + ((e.xpReward as number) ?? 0), 0);
      hero.gainXp(xpGain);
      log.push(`Wave ${gameState.wave} complete! +${xpGain} XP`);
    }

    if (phase === "wave_complete" && gameState.wave >= 5) phase = "victory";

    return NextResponse.json({
      gameState: {
        hero: hero.toSnapshot(),
        enemies: enemies.map(e => e.toSnapshot()),
        wave: gameState.wave,
        phase,
        battleLog: log.slice(-20),
        turn: gameState.turn + 1,
      },
      playerTrace,
      enemyTrace,
      actionResult: playerResult,
    });
  } catch (e) {
    return NextResponse.json({ error: String(e) }, { status: 500 });
  }
}
