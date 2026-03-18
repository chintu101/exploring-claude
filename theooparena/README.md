# ⚔ CodeQuest — The OOP Arena

An interactive browser RPG that teaches Object-Oriented Programming by letting you fight monsters. Every attack triggers a live **Code Trace** panel showing exactly which class fired, which method was called, and how the inheritance chain resolved.

## Quick Start

```bash
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000). No Python, no separate server, no subprocess issues.

## Stack

- **Next.js 14** (App Router) — frontend + API routes, one process
- **TypeScript** — all OOP classes written in TS, same concepts as Python
- **Tailwind CSS** — styling
- **Vercel** — deploy with `vercel --prod`

## OOP Concepts Demonstrated

| Concept | Where |
|---------|-------|
| Abstraction | `Entity`, `Character`, `Hero`, `Enemy` are abstract classes |
| Encapsulation | All `_private` attributes, exposed via getters |
| Inheritance | `Warrior → Hero → Character → Entity` (3-level chain) |
| Polymorphism | `calculateBaseDamage()` differs per hero subclass |
| Method Override | `Mage.basicAttack()` fully replaces the parent |
| `super()` | `Warrior.calculateBaseDamage()` calls `super()` then adds rage |
| Abstract Methods | `specialAbility()` forces every hero to implement it |
| Factory Pattern | `createHero('Warrior', 'Arthur')` |

## Project Structure

```
src/
  lib/
    models/
      Entity.ts       ← Abstract root class
      Character.ts    ← Combat stats, status effects
      Hero.ts         ← Warrior, Mage, Archer
      Enemy.ts        ← Goblin, Troll, Dragon, Lich
    services/
      TraceService.ts ← Maps actions → educational traces
  app/
    api/              ← Next.js API routes (no separate server)
      new-game/
      action/
      next-wave/
      class-hierarchy/
      concepts/
    page.tsx          ← Root layout
  components/
    HeroSelector.tsx
    BattleArena.tsx
    CodeTrace.tsx
    ClassExplorer.tsx
  hooks/
    useGameState.ts
```
