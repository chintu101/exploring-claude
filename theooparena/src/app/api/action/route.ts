import { NextRequest, NextResponse } from "next/server";
import { createHero, HeroClass } from "../../../lib/models/Hero";
import { createEnemy, EnemyType } from "../../../lib/models/Enemy";
import { Character } from "../../../lib/models/Character";
import { TraceService } from "../../../lib/services/TraceService";

function rehydrateHero(snap: Record<string, unknown>) {
  const hero = createHero(snap.hero_class as HeroClass ?? snap.heroClass as HeroClass, snap.name as string);
  const h = hero as unknown as Record<string, unknown>;
  h["_currentHp"]      = snap.current_hp ?? snap.currentHp ?? snap.max_hp ?? snap.maxHp;
  h["_mana"]           = snap.mana ?? snap.max_mana ?? snap.maxMana ?? 0;
  h["_xp"]             = snap.experience ?? snap.xp ?? 0;
  h["_level"]          = snap.level ?? 1;
  h["_statusEffects"]  = snap.status_effects ?? snap.statusEffects ?? [];
  if ((snap.hero_class ?? snap.heroClass) === "Archer") {
    h["_focusStacks"]  = snap.focus_stacks ?? snap.focusStacks ?? 0;
  }
  return hero;
}

function rehydrateEnemy(snap: Record<string, unknown>) {
  const type = (snap.enemy_type ?? snap.enemyType) as EnemyType;
  const enemy = createEnemy(type, 1);
  const e = enemy as unknown as Record<string, unknown>;
  e["_maxHp"]         = snap.max_hp ?? snap.maxHp;
  e["_currentHp"]     = snap.current_hp ?? snap.currentHp;
  e["_damage"]        = snap.base_damage ?? snap.damage;
  e["_defense"]       = snap.defense;
  e["_statusEffects"] = snap.status_effects ?? snap.statusEffects ?? [];
  if (type === "Dragon") {
    e["_breathCharges"] = snap.fire_charges ?? snap.breathCharges ?? 3;
  }
  return enemy;
}

function heroToSnapshot(hero: ReturnType<typeof createHero>, wave: number) {
  const s = hero.toSnapshot() as Record<string, unknown>;
  return {
    name:          s.name,
    class_name:    s.heroClass,
    hero_class:    s.heroClass,
    current_hp:    s.currentHp,
    max_hp:        s.maxHp,
    base_damage:   s.damage,
    defense:       s.defense,
    speed:         s.speed,
    is_alive:      s.isAlive,
    hp_ratio:      (s.currentHp as number) / (s.maxHp as number),
    status_effects: s.statusEffects,
    mana:          s.mana,
    max_mana:      s.maxMana,
    mana_ratio:    (s.mana as number) / (s.maxMana as number),
    level:         s.level,
    experience:    s.xp,
    focus_stacks:  s.focusStacks ?? 0,
    wave_level:    wave,
  };
}

function enemyToSnapshot(enemy: ReturnType<typeof createEnemy>, wave: number) {
  const s = enemy.toSnapshot() as Record<string, unknown>;
  return {
    name:          s.name,
    class_name:    s.enemyType,
    enemy_type:    s.enemyType,
    current_hp:    s.currentHp,
    max_hp:        s.maxHp,
    base_damage:   s.damage,
    defense:       s.defense,
    speed:         s.speed,
    is_alive:      s.isAlive,
    hp_ratio:      (s.currentHp as number) / (s.maxHp as number),
    status_effects: s.statusEffects,
    xp_reward:     s.xpReward,
    wave_level:    wave,
  };
}

function traceToApiShape(trace: ReturnType<typeof TraceService.getTrace>) {
  return {
    action_key: trace.actionKey,
    summary:    trace.summary,
    steps: trace.steps.map(step => ({
      class_name:        step.className,
      method_name:       step.methodName,
      code_line:         step.codeLine,
      description:       step.description,
      inheritance_chain: step.inheritanceChain,
      concept:           step.concept,
    })),
  };
}

export async function POST(req: NextRequest) {
  try {
    const { game_state, action } = await req.json();

    const hero    = rehydrateHero(game_state.hero);
    const enemies = (game_state.enemies as Record<string, unknown>[]).map(rehydrateEnemy);
    const log: string[] = [...(game_state.battle_log ?? [])];
    const alive   = enemies.filter(e => e.isAlive);
    const wave    = game_state.wave ?? 1;

    if (alive.length === 0) {
      return NextResponse.json({
        game_state:        { ...game_state, phase: "wave_complete" },
        code_trace:        null,
        enemy_code_trace:  null,
        action_result:     null,
        enemy_action_result: null,
        levelled_up:       false,
        status_messages:   [],
      });
    }

    const target = alive[0];

    // ── Player action ──────────────────────────────────────────────────────
    let playerResult;
    if (action === "basic_attack")     playerResult = hero.basicAttack(target as unknown as Character);
    else if (action === "special_ability") playerResult = hero.specialAbility(target as unknown as Character);
    else                                playerResult = hero.defend();
    log.push(playerResult.logEntry);

    // Status ticks on enemies
    for (const e of alive) log.push(...e.tickStatusEffects());

    const code_trace = traceToApiShape(TraceService.getTrace(playerResult.actionKey));

    // ── Check all dead ─────────────────────────────────────────────────────
    const stillAlive = enemies.filter(e => e.isAlive);
    if (stillAlive.length === 0) {
      const xpGain = (game_state.enemies as Record<string,unknown>[])
        .reduce((s: number, e) => s + ((e.xp_reward ?? e.xpReward ?? 0) as number), 0);
      hero.gainXp(xpGain);
      log.push(`All enemies defeated! +${xpGain} XP`);
      return NextResponse.json({
        game_state: {
          hero:       heroToSnapshot(hero, wave),
          enemies:    enemies.map(e => enemyToSnapshot(e, wave)),
          wave, turn: (game_state.turn ?? 0) + 1,
          phase: wave >= 5 ? "victory" : "wave_complete",
          battle_log: log.slice(-20), score: game_state.score ?? 0,
          levelled_up: false,
        },
        code_trace,
        enemy_code_trace:    null,
        action_result:       { action, source: hero.name, target: target.name, value: playerResult.damageDealt, message: playerResult.logEntry, is_crit: playerResult.critical, extra: {} },
        enemy_action_result: null,
        levelled_up:         false,
        status_messages:     [],
      });
    }

    // ── Enemy counter ──────────────────────────────────────────────────────
    const attacker       = stillAlive[0];
    const enemyResult    = attacker.decideAction(hero as unknown as Parameters<typeof attacker.decideAction>[0]);
    log.push(enemyResult.logEntry);
    const enemy_code_trace = traceToApiShape(TraceService.getTrace(enemyResult.actionKey));
    log.push(...hero.tickStatusEffects());

    let phase = "player_turn";
    if (!hero.isAlive) { phase = "defeat"; log.push(`${hero.name} has fallen...`); }
    else if (enemies.filter(e => e.isAlive).length === 0) {
      phase = wave >= 5 ? "victory" : "wave_complete";
      const xpGain = (game_state.enemies as Record<string,unknown>[])
        .reduce((s: number, e) => s + ((e.xp_reward ?? e.xpReward ?? 0) as number), 0);
      hero.gainXp(xpGain);
      log.push(`Wave ${wave} complete! +${xpGain} XP`);
    }

    return NextResponse.json({
      game_state: {
        hero:       heroToSnapshot(hero, wave),
        enemies:    enemies.map(e => enemyToSnapshot(e, wave)),
        wave, turn: (game_state.turn ?? 0) + 1,
        phase, battle_log: log.slice(-20), score: game_state.score ?? 0,
        levelled_up: false,
      },
      code_trace,
      enemy_code_trace,
      action_result:       { action, source: hero.name, target: target.name, value: playerResult.damageDealt, message: playerResult.logEntry, is_crit: playerResult.critical, extra: {} },
      enemy_action_result: { action: enemyResult.actionKey, source: attacker.name, target: hero.name, value: enemyResult.damageDealt, message: enemyResult.logEntry, is_crit: enemyResult.critical, extra: {} },
      levelled_up: false,
      status_messages: [],
    });
  } catch (e) {
    console.error(e);
    return NextResponse.json({ error: String(e) }, { status: 500 });
  }
}
