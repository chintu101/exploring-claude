"""
CodeQuest — OOP Class Hierarchy
================================
This module is the educational heart of CodeQuest. Every class here demonstrates
a core OOP concept:

  Entity (ABC)               ← Abstract base class, root of all game objects
    └── Character (ABC)      ← Inherits Entity; adds combat stats (encapsulation)
          ├── Hero (ABC)     ← Inherits Character; adds mana, skills, levelling
          │     ├── Warrior  ← Concrete; overrides calculate_base_damage (polymorphism)
          │     ├── Mage     ← Concrete; overrides basic_attack AND calculate_base_damage
          │     └── Archer   ← Concrete; overrides calculate_base_damage (crit system)
          └── Enemy (ABC)    ← Inherits Character; adds AI decision logic
                ├── Goblin   ← Concrete; frenzy multi-hit special
                ├── Troll    ← Concrete; overrides decide_action (regeneration)
                ├── Dragon   ← Concrete; limited fire breath charges
                └── Lich     ← Concrete; soul drain life-steal mechanic

OOP Concepts Demonstrated:
  - Abstraction     : Entity and Character are abstract (cannot be instantiated)
  - Encapsulation   : All attributes are private (_name, _hp); exposed via @property
  - Inheritance     : Every class extends its parent, calling super().__init__()
  - Polymorphism    : calculate_base_damage() and special_ability() behave differently
                       per subclass but share the same interface
  - Method Override : Warrior/Mage/Archer/Troll all override parent methods
  - super()         : All subclasses use super().__init__() to chain constructors
"""

from __future__ import annotations

import random
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


# ═══════════════════════════════════════════════════════════════════════════════
# LAYER 0 — ActionResult (value object, no inheritance needed)
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class ActionResult:
    """Immutable value object returned by every game action.

    Attributes:
        action   : Machine-readable action key (e.g. "whirlwind_strike")
        source   : Name of the acting entity
        target   : Name of the target entity
        value    : Numeric outcome (damage dealt, HP healed, etc.)
        message  : Human-readable description for the battle log
        is_crit  : Whether the action was a critical hit
        extra    : Arbitrary extra data (status effects applied, charges remaining…)
    """
    action: str
    source: str
    target: str
    value: int
    message: str
    is_crit: bool = False
    extra: dict = field(default_factory=dict)


# ═══════════════════════════════════════════════════════════════════════════════
# LAYER 1 — Entity (Abstract Base Class — root of the entire hierarchy)
# ═══════════════════════════════════════════════════════════════════════════════

class Entity(ABC):
    """Root abstract class for every object that exists in the game world.

    OOP Concepts:
        - Abstract (ABC): cannot be instantiated directly; only subclasses can
        - Encapsulation: _name and _entity_id are private; read via @property
        - Interface contract: every subclass MUST implement get_stats() and to_dict()

    Attributes:
        _name      : Display name shown in UI and battle log
        _entity_id : Unique identifier string for serialisation
        _alive     : Whether this entity is still active
    """

    CLASS_NAME: str = "Entity"      # Class-level attribute; overridden by subclasses

    def __init__(self, name: str, entity_id: str) -> None:
        self._name: str = name
        self._entity_id: str = entity_id
        self._alive: bool = True

    # ── Read-only properties (encapsulation: external code cannot mutate directly) ──

    @property
    def name(self) -> str:
        return self._name

    @property
    def entity_id(self) -> str:
        return self._entity_id

    @property
    def is_alive(self) -> bool:
        return self._alive

    # ── Abstract interface — subclasses must implement these ──

    @abstractmethod
    def get_stats(self) -> dict:
        """Return a dict of current stats. Used by the frontend to render UI."""
        pass

    @abstractmethod
    def to_dict(self) -> dict:
        """Full serialisation to JSON-safe dict for API responses."""
        pass

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self._name!r}, alive={self._alive})"


# ═══════════════════════════════════════════════════════════════════════════════
# LAYER 2 — Character (extends Entity; adds combat stats and mechanics)
# ═══════════════════════════════════════════════════════════════════════════════

class Character(Entity, ABC):
    """Abstract character with combat capabilities.

    Inherits from Entity (which provides name, id, alive flag) and adds:
        - Health points (current/max)
        - Base damage and defense stats
        - Speed (determines turn order)
        - Status effects list
        - take_damage() and heal() methods (shared by all characters)

    OOP Concepts:
        - Inheritance: super().__init__(name, entity_id) chains to Entity
        - Encapsulation: all stats are private (_current_hp, etc.)
        - Concrete methods: take_damage and heal are implemented here so every
          subclass gets them for free (code reuse via inheritance)

    Attributes:
        _max_hp         : Maximum hit points
        _current_hp     : Current hit points (decreases as damage is taken)
        _base_damage    : Raw damage output before modifiers
        _defense        : Flat damage reduction applied to incoming hits
        _speed          : Initiative value; higher = acts first
        _status_effects : Active debuffs/buffs (e.g. "bleeding", "burning")
    """

    CLASS_NAME: str = "Character"

    def __init__(
        self,
        name: str,
        entity_id: str,
        max_hp: int,
        base_damage: int,
        defense: int,
        speed: int,
    ) -> None:
        super().__init__(name, entity_id)   # ← super() chains to Entity.__init__
        self._max_hp: int = max_hp
        self._current_hp: int = max_hp
        self._base_damage: int = base_damage
        self._defense: int = defense
        self._speed: int = speed
        self._status_effects: list[str] = []

    # ── Properties ──

    @property
    def max_hp(self) -> int:
        return self._max_hp

    @property
    def current_hp(self) -> int:
        return self._current_hp

    @property
    def base_damage(self) -> int:
        return self._base_damage

    @property
    def defense(self) -> int:
        return self._defense

    @property
    def speed(self) -> int:
        return self._speed

    @property
    def hp_ratio(self) -> float:
        """Fraction of HP remaining (0.0 – 1.0)."""
        return self._current_hp / self._max_hp if self._max_hp > 0 else 0.0

    @property
    def status_effects(self) -> list[str]:
        return list(self._status_effects)   # return a copy; don't expose the list

    # ── Shared combat methods (inherited by Hero and Enemy for free) ──

    def take_damage(self, raw_damage: int) -> int:
        """Apply incoming damage after subtracting defense.

        Returns:
            actual_damage: the HP amount actually lost (always >= 1)
        """
        actual_damage = max(1, raw_damage - self._defense)
        self._current_hp = max(0, self._current_hp - actual_damage)
        if self._current_hp == 0:
            self._alive = False
        return actual_damage

    def heal(self, amount: int) -> int:
        """Restore HP, capped at max_hp.

        Returns:
            healed: how many HP were actually restored
        """
        before = self._current_hp
        self._current_hp = min(self._max_hp, self._current_hp + amount)
        return self._current_hp - before

    def calculate_base_damage(self) -> int:
        """Base damage roll with ±2 variance.

        This method is overridden by subclasses (Warrior, Mage, Archer) to
        add class-specific modifiers — demonstrating POLYMORPHISM.
        """
        variance = random.randint(-2, 2)
        return max(1, self._base_damage + variance)

    def add_status_effect(self, effect: str) -> None:
        if effect not in self._status_effects:
            self._status_effects.append(effect)

    def remove_status_effect(self, effect: str) -> None:
        if effect in self._status_effects:
            self._status_effects.remove(effect)

    def tick_status_effects(self) -> list[str]:
        """Process end-of-turn status effects (bleeding, burning, etc.).

        Returns:
            messages: list of status tick messages for the battle log
        """
        messages = []
        if "bleeding" in self._status_effects:
            bleed_dmg = 5
            self._current_hp = max(0, self._current_hp - bleed_dmg)
            if self._current_hp == 0:
                self._alive = False
            messages.append(f"{self._name} bleeds for {bleed_dmg} damage!")
        if "burning" in self._status_effects:
            burn_dmg = 8
            self._current_hp = max(0, self._current_hp - burn_dmg)
            if self._current_hp == 0:
                self._alive = False
            messages.append(f"{self._name} burns for {burn_dmg} damage!")
        return messages

    def get_stats(self) -> dict:
        """Implements the abstract method from Entity."""
        return {
            "name": self._name,
            "class_name": self.CLASS_NAME,
            "current_hp": self._current_hp,
            "max_hp": self._max_hp,
            "base_damage": self._base_damage,
            "defense": self._defense,
            "speed": self._speed,
            "is_alive": self._alive,
            "hp_ratio": self.hp_ratio,
            "status_effects": self._status_effects,
        }


# ═══════════════════════════════════════════════════════════════════════════════
# LAYER 3a — Hero (extends Character; the player-controlled characters)
# ═══════════════════════════════════════════════════════════════════════════════

class Hero(Character, ABC):
    """Abstract base class for all player heroes.

    Extends Character with:
        - Mana resource (fuel for special abilities)
        - Level and experience system
        - Inventory slot for equipped weapon
        - Abstract special_ability() that every hero must implement

    OOP Concepts:
        - Inheritance chain: Hero → Character → Entity (3 levels deep)
        - Abstract method: special_ability() forces each subclass to define
          its own unique ability (polymorphism)
        - Protected method: _level_up() is prefixed _ (convention: internal use)

    Attributes:
        _hero_class  : String label of the hero's class ("Warrior", "Mage", etc.)
        _mana        : Current mana
        _max_mana    : Maximum mana
        _level       : Current level (starts at 1)
        _experience  : Total XP accumulated
    """

    CLASS_NAME: str = "Hero"

    def __init__(
        self,
        name: str,
        hero_class: str,
        max_hp: int,
        base_damage: int,
        defense: int,
        speed: int,
        max_mana: int = 100,
    ) -> None:
        # super() calls Character.__init__, which calls Entity.__init__
        super().__init__(
            name=name,
            entity_id=f"hero_{name.lower().replace(' ', '_')}",
            max_hp=max_hp,
            base_damage=base_damage,
            defense=defense,
            speed=speed,
        )
        self._hero_class: str = hero_class
        self._mana: int = max_mana
        self._max_mana: int = max_mana
        self._level: int = 1
        self._experience: int = 0

    # ── Properties ──

    @property
    def hero_class(self) -> str:
        return self._hero_class

    @property
    def mana(self) -> int:
        return self._mana

    @property
    def max_mana(self) -> int:
        return self._max_mana

    @property
    def level(self) -> int:
        return self._level

    @property
    def experience(self) -> int:
        return self._experience

    @property
    def mana_ratio(self) -> float:
        return self._mana / self._max_mana if self._max_mana > 0 else 0.0

    # ── Abstract method — each subclass MUST implement this ──

    @abstractmethod
    def special_ability(self, target: "Enemy") -> ActionResult:
        """Hero's unique special move. Must be implemented by each subclass."""
        pass

    # ── Concrete methods shared by all Heroes ──

    def basic_attack(self, target: "Enemy") -> ActionResult:
        """Standard physical attack. Can be overridden by subclasses (Mage does)."""
        damage = self.calculate_base_damage()
        actual = target.take_damage(damage)
        return ActionResult(
            action="basic_attack",
            source=self._name,
            target=target.name,
            value=actual,
            message=f"{self._name} attacks {target.name} for {actual} damage!",
        )

    def defend(self) -> ActionResult:
        """Temporarily increase defense. Universal hero action."""
        bonus = 5
        self._defense += bonus
        self._mana = min(self._max_mana, self._mana + 10)   # defending restores mana
        return ActionResult(
            action="defend",
            source=self._name,
            target=self._name,
            value=bonus,
            message=f"{self._name} takes a defensive stance (+{bonus} defense, +10 mana).",
            extra={"defense_bonus": bonus, "mana_restored": 10},
        )

    def reset_defense(self) -> None:
        """Called at the start of each round to remove defend bonus."""
        pass   # stateless in this implementation; defense is base stat

    def gain_experience(self, amount: int) -> bool:
        """Add XP. Returns True if the hero levelled up."""
        self._experience += amount
        threshold = self._level * 100
        if self._experience >= threshold:
            self._level_up()
            return True
        return False

    def _level_up(self) -> None:
        """Protected helper: called automatically when XP threshold is reached."""
        self._level += 1
        old_hp = self._max_hp
        self._max_hp += 15
        self._current_hp = min(self._current_hp + 15, self._max_hp)
        self._base_damage += 2
        self._mana = self._max_mana   # refill mana on level up

    def restore_mana(self, amount: int) -> int:
        """Restore mana up to the maximum. Returns how much was actually restored."""
        before = self._mana
        self._mana = min(self._max_mana, self._mana + amount)
        return self._mana - before

    def to_dict(self) -> dict:
        base = self.get_stats()
        base.update({
            "hero_class": self._hero_class,
            "mana": self._mana,
            "max_mana": self._max_mana,
            "mana_ratio": self.mana_ratio,
            "level": self._level,
            "experience": self._experience,
            "xp_to_next": self._level * 100,
        })
        return base


# ──────────────────────────────────────────────────────────────────────────────
# CONCRETE HERO — Warrior
# ──────────────────────────────────────────────────────────────────────────────

class Warrior(Hero):
    """The Warrior: a tanky brawler who gets stronger as HP drops.

    Key OOP Demonstrations:
        - Overrides calculate_base_damage() → Berserker rage bonus (polymorphism)
        - Has its own private attribute: _rage_charges (new state in subclass)
        - Calls super().__init__ to forward params up the hierarchy chain

    Stats: High HP (150), High Damage (20), High Defense (8), Low Mana (50)
    Special: Whirlwind Strike — 150% damage, costs 20 mana
    Passive: Berserker — deals +0..+10 extra damage scaled by missing HP
    """

    CLASS_NAME: str = "Warrior"

    def __init__(self, name: str) -> None:
        super().__init__(
            name=name,
            hero_class="Warrior",
            max_hp=150,
            base_damage=20,
            defense=8,
            speed=6,
            max_mana=50,
        )
        self._rage_charges: int = 0   # new attribute that only Warrior has

    # ── Override: Berserker rage makes Warrior hit harder at low HP ──

    def calculate_base_damage(self) -> int:
        """OVERRIDES Character.calculate_base_damage().

        Adds rage bonus: the lower Warrior's HP, the more damage it deals.
        Also consumes rage charges (built up by Whirlwind Strike).
        """
        base = super().calculate_base_damage()    # ← calls Character.calculate_base_damage()
        rage_bonus = int((1.0 - self.hp_ratio) * 10)   # 0 when full HP, up to 10 when near death
        charge_bonus = self._rage_charges * 3
        self._rage_charges = 0   # rage charges consumed on attack
        return base + rage_bonus + charge_bonus

    def special_ability(self, target: "Enemy") -> ActionResult:
        """Whirlwind Strike: powerful swing that builds rage and costs 20 mana."""
        if self._mana < 20:
            return ActionResult(
                action="special_failed",
                source=self._name,
                target=target.name,
                value=0,
                message=f"{self._name} needs 20 mana for Whirlwind Strike! (has {self._mana})",
            )
        damage = int(self.calculate_base_damage() * 1.5)
        actual = target.take_damage(damage)
        self._mana -= 20
        self._rage_charges += 1
        return ActionResult(
            action="whirlwind_strike",
            source=self._name,
            target=target.name,
            value=actual,
            is_crit=damage > self._base_damage * 2,
            message=f"⚔️ {self._name} unleashes Whirlwind Strike for {actual} damage! Rage builds!",
            extra={"rage_charges": self._rage_charges},
        )

    def to_dict(self) -> dict:
        d = super().to_dict()
        d["rage_charges"] = self._rage_charges
        return d


# ──────────────────────────────────────────────────────────────────────────────
# CONCRETE HERO — Mage
# ──────────────────────────────────────────────────────────────────────────────

class Mage(Hero):
    """The Mage: a glass-cannon spell caster whose magic bypasses armor.

    Key OOP Demonstrations:
        - Overrides basic_attack() — the most dramatic override; Mage's auto-attack
          is a Magic Bolt that ignores defense entirely (polymorphism)
        - Overrides calculate_base_damage() → scales with mana percentage
        - Introduces _spell_power — a new attribute unique to Mage

    Stats: Low HP (80), Medium Damage (12), Low Defense (3), High Mana (200)
    Special: Fireball — 200% spell power, ignores armor, costs 40 mana
    Passive: Mana Flow — damage scales with current mana percentage
    """

    CLASS_NAME: str = "Mage"

    def __init__(self, name: str) -> None:
        super().__init__(
            name=name,
            hero_class="Mage",
            max_hp=80,
            base_damage=12,
            defense=3,
            speed=8,
            max_mana=200,
        )
        self._spell_power: int = 25   # attribute unique to Mage subclass

    @property
    def spell_power(self) -> int:
        return self._spell_power

    # ── Override: mana scales damage ──

    def calculate_base_damage(self) -> int:
        """OVERRIDES Character.calculate_base_damage().

        Mage deals bonus damage proportional to mana ratio.
        This demonstrates polymorphism: same method name, different behaviour.
        """
        base = super().calculate_base_damage()
        mana_bonus = int(self.mana_ratio * 8)
        return base + mana_bonus

    # ── Override: Mage's basic attack is magic, not physical ──

    def basic_attack(self, target: "Enemy") -> ActionResult:
        """OVERRIDES Hero.basic_attack().

        Magic Bolt: deals spell_power-based damage that IGNORES the target's
        defense stat. Costs 5 mana per cast.
        """
        if self._mana < 5:
            # Fallback to feeble physical attack when dry on mana
            return super().basic_attack(target)
        damage = self.calculate_base_damage() + self._spell_power // 2
        # Magic ignores defense: bypass take_damage() and apply directly
        actual = max(1, damage)
        target._current_hp = max(0, target._current_hp - actual)
        if target._current_hp == 0:
            target._alive = False
        self._mana -= 5
        return ActionResult(
            action="magic_bolt",
            source=self._name,
            target=target.name,
            value=actual,
            message=f"✨ {self._name} casts Magic Bolt for {actual} damage (armor ignored)!",
        )

    def special_ability(self, target: "Enemy") -> ActionResult:
        """Fireball: devastating spell that scorches and may apply burning."""
        if self._mana < 40:
            return ActionResult(
                action="special_failed",
                source=self._name,
                target=target.name,
                value=0,
                message=f"{self._name} needs 40 mana for Fireball! (has {self._mana})",
            )
        damage = int(self._spell_power * 2 + self.calculate_base_damage())
        actual = max(1, damage)
        target._current_hp = max(0, target._current_hp - actual)
        if target._current_hp == 0:
            target._alive = False
        self._mana -= 40
        # 40% chance to apply burning status
        applied_burn = random.random() < 0.4
        if applied_burn:
            target.add_status_effect("burning")
        return ActionResult(
            action="fireball",
            source=self._name,
            target=target.name,
            value=actual,
            is_crit=applied_burn,
            message=(
                f"🔥 {self._name} hurls a Fireball! {target.name} takes {actual} damage"
                + (" and catches fire!" if applied_burn else "!")
            ),
            extra={"burning_applied": applied_burn},
        )

    def to_dict(self) -> dict:
        d = super().to_dict()
        d["spell_power"] = self._spell_power
        return d


# ──────────────────────────────────────────────────────────────────────────────
# CONCRETE HERO — Archer
# ──────────────────────────────────────────────────────────────────────────────

class Archer(Hero):
    """The Archer: balanced fighter with the highest speed and critical hits.

    Key OOP Demonstrations:
        - Overrides calculate_base_damage() with a critical hit system
        - Introduces _crit_chance and _focus_stacks — new subclass state
        - Shows how a subclass can maintain internal counters that influence
          inherited method behaviour

    Stats: Medium HP (100), Medium Damage (15), Medium Defense (5), Fast Speed (12)
    Special: Rain of Arrows — guaranteed multi-crit, applies bleeding
    Passive: Focus — each non-crit attack builds focus stacks, raising crit chance
    """

    CLASS_NAME: str = "Archer"

    def __init__(self, name: str) -> None:
        super().__init__(
            name=name,
            hero_class="Archer",
            max_hp=100,
            base_damage=15,
            defense=5,
            speed=12,
            max_mana=80,
        )
        self._base_crit_chance: float = 0.20   # 20% base crit chance
        self._focus_stacks: int = 0            # each non-crit adds a stack

    @property
    def crit_chance(self) -> float:
        """Effective crit chance including focus stacks."""
        return min(0.90, self._base_crit_chance + self._focus_stacks * 0.05)

    def calculate_base_damage(self) -> int:
        """OVERRIDES Character.calculate_base_damage().

        Archer can critically strike. A crit doubles damage and resets focus.
        Non-crits build focus stacks (each adds +5% crit chance, up to 90%).
        """
        base = super().calculate_base_damage()
        is_crit = random.random() < self.crit_chance
        if is_crit:
            self._focus_stacks = 0   # reset on crit
            return base * 2
        self._focus_stacks += 1
        return base

    def special_ability(self, target: "Enemy") -> ActionResult:
        """Rain of Arrows: 3 guaranteed-crit arrows that inflict bleeding."""
        if self._mana < 30:
            return ActionResult(
                action="special_failed",
                source=self._name,
                target=target.name,
                value=0,
                message=f"{self._name} needs 30 mana for Rain of Arrows! (has {self._mana})",
            )
        # Each arrow is a guaranteed crit (base * 2)
        arrow_damage = self._base_damage * 2 + 10
        actual = target.take_damage(arrow_damage)
        self._mana -= 30
        self._focus_stacks = 0
        target.add_status_effect("bleeding")
        return ActionResult(
            action="rain_of_arrows",
            source=self._name,
            target=target.name,
            value=actual,
            is_crit=True,
            message=(
                f"🏹 {self._name} rains arrows! {target.name} takes {actual} damage and is bleeding!"
            ),
            extra={"bleeding_applied": True},
        )

    def to_dict(self) -> dict:
        d = super().to_dict()
        d["crit_chance"] = round(self.crit_chance, 2)
        d["focus_stacks"] = self._focus_stacks
        return d


# ═══════════════════════════════════════════════════════════════════════════════
# LAYER 3b — Enemy (extends Character; AI-controlled opponents)
# ═══════════════════════════════════════════════════════════════════════════════

class Enemy(Character, ABC):
    """Abstract base class for all enemies.

    Extends Character with:
        - enemy_type label for UI rendering
        - xp_reward for player progression
        - Wave scaling (enemies become stronger each wave)
        - decide_action() AI method (can be overridden — see Troll)
        - Abstract special_attack() that each enemy must implement

    OOP Concepts:
        - Abstract: Enemy cannot be instantiated; only Goblin/Troll/Dragon/Lich can
        - Inheritance: Enemy → Character → Entity (same 3-level chain as Hero)
        - Polymorphism: decide_action() calls special_attack() via dynamic dispatch
        - Method override: Troll overrides decide_action() to add regeneration

    Attributes:
        _enemy_type  : Display type string ("Goblin", "Dragon", etc.)
        _xp_reward   : XP given to hero when this enemy is defeated
        _wave_level  : Current dungeon wave (used to scale stats)
    """

    CLASS_NAME: str = "Enemy"

    def __init__(
        self,
        name: str,
        enemy_type: str,
        max_hp: int,
        base_damage: int,
        defense: int,
        speed: int,
        xp_reward: int,
        wave_level: int = 1,
    ) -> None:
        super().__init__(
            name=name,
            entity_id=f"enemy_{enemy_type.lower()}_{random.randint(1000, 9999)}",
            max_hp=max_hp,
            base_damage=base_damage,
            defense=defense,
            speed=speed,
        )
        self._enemy_type: str = enemy_type
        self._xp_reward: int = xp_reward
        self._wave_level: int = wave_level
        self._apply_wave_scaling(wave_level)

    def _apply_wave_scaling(self, wave: int) -> None:
        """Enemies grow stronger with each wave (30% increase per wave)."""
        if wave <= 1:
            return
        multiplier = 1.0 + (wave - 1) * 0.3
        self._max_hp = int(self._max_hp * multiplier)
        self._current_hp = self._max_hp
        self._base_damage = int(self._base_damage * multiplier)
        self._xp_reward = int(self._xp_reward * multiplier)

    @property
    def enemy_type(self) -> str:
        return self._enemy_type

    @property
    def xp_reward(self) -> int:
        return self._xp_reward

    @abstractmethod
    def special_attack(self, target: Hero) -> ActionResult:
        """Each enemy has a unique special attack. Must be implemented."""
        pass

    def decide_action(self, target: Hero) -> ActionResult:
        """AI decision engine.

        Default strategy: use special attack when HP is below 30% or 20% random chance.
        Overridden by Troll which regenerates before acting.
        """
        if self.hp_ratio < 0.3 or random.random() < 0.20:
            return self.special_attack(target)
        return self._basic_enemy_attack(target)

    def _basic_enemy_attack(self, target: Hero) -> ActionResult:
        """Standard melee attack. Uses the inherited take_damage pipeline."""
        damage = self.calculate_base_damage()
        actual = target.take_damage(damage)
        return ActionResult(
            action="enemy_basic_attack",
            source=self._name,
            target=target.name,
            value=actual,
            message=f"{self._name} attacks {target.name} for {actual} damage!",
        )

    def to_dict(self) -> dict:
        base = self.get_stats()
        base.update({
            "enemy_type": self._enemy_type,
            "xp_reward": self._xp_reward,
            "wave_level": self._wave_level,
        })
        return base


# ──────────────────────────────────────────────────────────────────────────────
# CONCRETE ENEMY — Goblin
# ──────────────────────────────────────────────────────────────────────────────

class Goblin(Enemy):
    """Goblin: Fast, weak, attacks multiple times with Frenzy.

    OOP Demo: Implements abstract special_attack() with a multi-hit mechanic.
    """

    CLASS_NAME: str = "Goblin"

    def __init__(self, wave_level: int = 1) -> None:
        super().__init__(
            name="Goblin",
            enemy_type="Goblin",
            max_hp=40,
            base_damage=8,
            defense=1,
            speed=10,
            xp_reward=25,
            wave_level=wave_level,
        )

    def special_attack(self, target: Hero) -> ActionResult:
        """Frenzy: 3 rapid strikes for reduced damage each."""
        total_damage = 0
        for _ in range(3):
            hit = max(1, self._base_damage // 3)
            actual = target.take_damage(hit)
            total_damage += actual
        return ActionResult(
            action="goblin_frenzy",
            source=self._name,
            target=target.name,
            value=total_damage,
            message=f"👺 Goblin Frenzy! 3 rapid strikes deal {total_damage} total damage to {target.name}!",
        )


# ──────────────────────────────────────────────────────────────────────────────
# CONCRETE ENEMY — Troll
# ──────────────────────────────────────────────────────────────────────────────

class Troll(Enemy):
    """Troll: Slow but regenerates HP every turn.

    Key OOP Demo: OVERRIDES decide_action() to add regeneration logic before
    delegating to the parent's decide_action() via super().
    """

    CLASS_NAME: str = "Troll"

    def __init__(self, wave_level: int = 1) -> None:
        super().__init__(
            name="Troll",
            enemy_type="Troll",
            max_hp=120,
            base_damage=14,
            defense=5,
            speed=4,
            xp_reward=60,
            wave_level=wave_level,
        )
        self._regen_per_turn: int = 5

    def decide_action(self, target: Hero) -> ActionResult:
        """OVERRIDES Enemy.decide_action().

        Troll regenerates HP before attacking each turn.
        After healing, delegates to parent's decide_action() via super().
        """
        healed = self.heal(self._regen_per_turn)
        result = super().decide_action(target)   # ← super() calls Enemy.decide_action()
        if healed > 0:
            result.extra["troll_regen"] = healed
            result.message = f"[Troll regens {healed} HP] " + result.message
        return result

    def special_attack(self, target: Hero) -> ActionResult:
        """Ground Slam: ignores armor completely."""
        damage = self._base_damage + 8
        actual = max(1, damage)   # bypass take_damage; ignore defense
        target._current_hp = max(0, target._current_hp - actual)
        if target._current_hp == 0:
            target._alive = False
        return ActionResult(
            action="ground_slam",
            source=self._name,
            target=target.name,
            value=actual,
            message=f"🪨 Troll Ground Slam! {target.name} takes {actual} crushing damage (armor ignored)!",
        )


# ──────────────────────────────────────────────────────────────────────────────
# CONCRETE ENEMY — Dragon
# ──────────────────────────────────────────────────────────────────────────────

class Dragon(Enemy):
    """Dragon: Boss-tier with powerful Fire Breath (limited uses)."""

    CLASS_NAME: str = "Dragon"

    def __init__(self, wave_level: int = 1) -> None:
        super().__init__(
            name="Dragon",
            enemy_type="Dragon",
            max_hp=200,
            base_damage=22,
            defense=10,
            speed=7,
            xp_reward=150,
            wave_level=wave_level,
        )
        self._fire_charges: int = 3   # can only fire-breathe 3 times

    def special_attack(self, target: Hero) -> ActionResult:
        """Fire Breath: 2x damage, limited to 3 uses."""
        if self._fire_charges <= 0:
            return self._basic_enemy_attack(target)
        damage = self._base_damage * 2
        actual = target.take_damage(damage)
        self._fire_charges -= 1
        applied_burn = random.random() < 0.5
        if applied_burn:
            target.add_status_effect("burning")
        return ActionResult(
            action="fire_breath",
            source=self._name,
            target=target.name,
            value=actual,
            is_crit=damage > 35,
            message=(
                f"🐲 Dragon Fire Breath! {target.name} scorched for {actual} damage"
                + (" and is burning!" if applied_burn else "!")
            ),
            extra={"fire_charges_remaining": self._fire_charges, "burning_applied": applied_burn},
        )

    def to_dict(self) -> dict:
        d = super().to_dict()
        d["fire_charges"] = self._fire_charges
        return d


# ──────────────────────────────────────────────────────────────────────────────
# CONCRETE ENEMY — Lich
# ──────────────────────────────────────────────────────────────────────────────

class Lich(Enemy):
    """Lich: Undead boss with Soul Drain (life-steal)."""

    CLASS_NAME: str = "Lich"

    def __init__(self, wave_level: int = 1) -> None:
        super().__init__(
            name="Lich",
            enemy_type="Lich",
            max_hp=160,
            base_damage=18,
            defense=6,
            speed=9,
            xp_reward=175,
            wave_level=wave_level,
        )

    def special_attack(self, target: Hero) -> ActionResult:
        """Soul Drain: deals damage AND heals Lich for the same amount."""
        drain_amount = 20
        actual = target.take_damage(drain_amount)
        healed = self.heal(actual)   # Lich heals for what it drained
        return ActionResult(
            action="soul_drain",
            source=self._name,
            target=target.name,
            value=actual,
            message=(
                f"💀 Lich Soul Drain! Drains {actual} HP from {target.name} "
                f"(Lich heals {healed} HP)!"
            ),
            extra={"lich_healed": healed},
        )


# ═══════════════════════════════════════════════════════════════════════════════
# FACTORY FUNCTIONS — Create entities by string type name
# ═══════════════════════════════════════════════════════════════════════════════

HERO_REGISTRY: dict[str, type[Hero]] = {
    "Warrior": Warrior,
    "Mage": Mage,
    "Archer": Archer,
}

ENEMY_REGISTRY: dict[str, type[Enemy]] = {
    "Goblin": Goblin,
    "Troll": Troll,
    "Dragon": Dragon,
    "Lich": Lich,
}


def create_hero(hero_class: str, name: str) -> Hero:
    """Factory function: create a Hero by class name string.

    This demonstrates the Factory pattern — callers don't need to know which
    concrete class they're getting; they just ask for "Warrior" by name.

    Raises:
        ValueError: if hero_class is not in the registry
    """
    if hero_class not in HERO_REGISTRY:
        raise ValueError(
            f"Unknown hero class '{hero_class}'. "
            f"Available: {list(HERO_REGISTRY.keys())}"
        )
    return HERO_REGISTRY[hero_class](name)


def create_enemy(enemy_type: str, wave_level: int = 1) -> Enemy:
    """Factory function: create an Enemy by type string.

    Raises:
        ValueError: if enemy_type is not in the registry
    """
    if enemy_type not in ENEMY_REGISTRY:
        raise ValueError(
            f"Unknown enemy type '{enemy_type}'. "
            f"Available: {list(ENEMY_REGISTRY.keys())}"
        )
    return ENEMY_REGISTRY[enemy_type](wave_level)


def get_class_hierarchy() -> dict:
    """Return the full OOP hierarchy as a nested dict (for ClassExplorer UI)."""
    return {
        "name": "Entity",
        "class_name": "Entity",
        "type": "abstract",
        "description": "Root of all game objects. Provides name, id, is_alive.",
        "children": [
            {
                "name": "Character",
                "class_name": "Character",
                "type": "abstract",
                "description": "Adds HP, damage, defense, speed. Shared combat logic.",
                "children": [
                    {
                        "name": "Hero",
                        "class_name": "Hero",
                        "type": "abstract",
                        "description": "Adds mana, level, XP. Abstract special_ability().",
                        "children": [
                            {
                                "name": "Warrior",
                                "class_name": "Warrior",
                                "type": "concrete",
                                "description": "Berserker — deals more damage at low HP.",
                            },
                            {
                                "name": "Mage",
                                "class_name": "Mage",
                                "type": "concrete",
                                "description": "Spell caster — magic bypasses armor.",
                            },
                            {
                                "name": "Archer",
                                "class_name": "Archer",
                                "type": "concrete",
                                "description": "Critical hitter — focus stacks raise crit.",
                            },
                        ],
                    },
                    {
                        "name": "Enemy",
                        "class_name": "Enemy",
                        "type": "abstract",
                        "description": "AI combatants. Scaled by wave level.",
                        "children": [
                            {
                                "name": "Goblin",
                                "class_name": "Goblin",
                                "type": "concrete",
                                "description": "Fast. Frenzy: 3 rapid hits.",
                            },
                            {
                                "name": "Troll",
                                "class_name": "Troll",
                                "type": "concrete",
                                "description": "Regenerates HP each turn.",
                            },
                            {
                                "name": "Dragon",
                                "class_name": "Dragon",
                                "type": "concrete",
                                "description": "Boss. Fire Breath (3 uses).",
                            },
                            {
                                "name": "Lich",
                                "class_name": "Lich",
                                "type": "concrete",
                                "description": "Boss. Soul Drain (life-steal).",
                            },
                        ],
                    },
                ],
            }
        ],
    }
