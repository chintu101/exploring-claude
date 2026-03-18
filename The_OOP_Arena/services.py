"""
CodeQuest — Code Trace Service
================================
The most educational component of CodeQuest.

For every game action (basic_attack, whirlwind_strike, fireball, etc.), this
service generates a list of TraceStep objects that the frontend animates
sequentially in the CodeTrace panel.

Each TraceStep shows:
  - Which class the method belongs to
  - The key line of code
  - A plain-English description of what's happening
  - The full inheritance chain from Entity to the concrete class
  - Which OOP concept is being demonstrated

This makes the invisible (class dispatch, method overriding, super() calls)
visible and educational.
"""

from __future__ import annotations

from api.schemas import CodeTrace, TraceStep


# ═══════════════════════════════════════════════════════════════════════════════
# Trace library — one trace definition per action key
# ═══════════════════════════════════════════════════════════════════════════════

# Each entry maps an action key → list of TraceStep dicts (converted below)
_TRACE_LIBRARY: dict[str, dict] = {

    # ── Hero: Basic attack (default Hero implementation) ──
    "basic_attack": {
        "summary": "Hero.basic_attack() calls Character.calculate_base_damage() and Enemy.take_damage() — inheritance in action.",
        "steps": [
            {
                "class_name": "Hero",
                "method_name": "basic_attack",
                "code_line": "def basic_attack(self, target: Enemy) -> ActionResult:",
                "description": "Hero.basic_attack() is called. This is the base implementation defined in the Hero class.",
                "inheritance_chain": ["Entity", "Character", "Hero"],
                "concept": "Inheritance",
            },
            {
                "class_name": "Character",
                "method_name": "calculate_base_damage",
                "code_line": "variance = random.randint(-2, 2)\nreturn max(1, self._base_damage + variance)",
                "description": "Hero calls self.calculate_base_damage() — which resolves to the Character implementation (unless overridden by the subclass).",
                "inheritance_chain": ["Entity", "Character"],
                "concept": "Method resolution",
            },
            {
                "class_name": "Character",
                "method_name": "take_damage",
                "code_line": "actual_damage = max(1, raw_damage - self._defense)\nself._current_hp = max(0, self._current_hp - actual_damage)",
                "description": "target.take_damage() is called on the Enemy. Defense reduces the hit. This method lives in Character — shared by all combatants.",
                "inheritance_chain": ["Entity", "Character"],
                "concept": "Code reuse via inheritance",
            },
        ],
    },

    # ── Mage: Magic bolt (overrides basic_attack) ──
    "magic_bolt": {
        "summary": "Mage.basic_attack() OVERRIDES Hero.basic_attack() — same method name, completely different behaviour (Polymorphism).",
        "steps": [
            {
                "class_name": "Mage",
                "method_name": "basic_attack",
                "code_line": "def basic_attack(self, target: Enemy) -> ActionResult:  # OVERRIDES Hero",
                "description": "Mage.basic_attack() overrides Hero.basic_attack(). Python's method resolution order (MRO) picks the Mage version because it's more specific.",
                "inheritance_chain": ["Entity", "Character", "Hero", "Mage"],
                "concept": "Polymorphism (method override)",
            },
            {
                "class_name": "Mage",
                "method_name": "calculate_base_damage",
                "code_line": "mana_bonus = int(self.mana_ratio * 8)\nreturn base + mana_bonus",
                "description": "Mage also overrides calculate_base_damage() — adds mana-scaling damage. The more mana Mage has, the harder it hits.",
                "inheritance_chain": ["Entity", "Character", "Hero", "Mage"],
                "concept": "Polymorphism",
            },
            {
                "class_name": "Mage",
                "method_name": "basic_attack",
                "code_line": "actual = max(1, damage)  # bypass take_damage(); magic ignores armor",
                "description": "Crucially, Mage bypasses take_damage() entirely. Magic damage is applied directly to _current_hp, skipping the defense reduction in Character.take_damage().",
                "inheritance_chain": ["Entity", "Character", "Hero", "Mage"],
                "concept": "Selective override",
            },
        ],
    },

    # ── Warrior: Whirlwind Strike ──
    "whirlwind_strike": {
        "summary": "Warrior.special_ability() overrides Hero's abstract method. Warrior.calculate_base_damage() shows Berserker rage (low HP → more damage).",
        "steps": [
            {
                "class_name": "Warrior",
                "method_name": "special_ability",
                "code_line": "def special_ability(self, target: Enemy) -> ActionResult:",
                "description": "Warrior.special_ability() is called. This IMPLEMENTS the abstract method declared in Hero. Without this, Warrior couldn't be instantiated.",
                "inheritance_chain": ["Entity", "Character", "Hero", "Warrior"],
                "concept": "Abstract method implementation",
            },
            {
                "class_name": "Warrior",
                "method_name": "calculate_base_damage",
                "code_line": "rage_bonus = int((1.0 - self.hp_ratio) * 10)\nreturn base + rage_bonus + charge_bonus",
                "description": "Warrior.calculate_base_damage() is called. It first calls super().calculate_base_damage() to get the base roll, then adds Berserker rage (scales with missing HP).",
                "inheritance_chain": ["Entity", "Character", "Hero", "Warrior"],
                "concept": "Polymorphism + super()",
            },
            {
                "class_name": "Character",
                "method_name": "calculate_base_damage",
                "code_line": "variance = random.randint(-2, 2)\nreturn max(1, self._base_damage + variance)",
                "description": "super().calculate_base_damage() runs Character's version first, then Warrior adds its bonus on top — stacking via super().",
                "inheritance_chain": ["Entity", "Character"],
                "concept": "super() call chaining",
            },
        ],
    },

    # ── Mage: Fireball ──
    "fireball": {
        "summary": "Mage.special_ability() implements Hero's abstract method with a high-power spell that may apply burning status.",
        "steps": [
            {
                "class_name": "Mage",
                "method_name": "special_ability",
                "code_line": "def special_ability(self, target: Enemy) -> ActionResult:",
                "description": "Mage.special_ability() implements the abstract Hero.special_ability(). Every hero subclass must provide this — it's the OOP contract.",
                "inheritance_chain": ["Entity", "Character", "Hero", "Mage"],
                "concept": "Abstract method contract",
            },
            {
                "class_name": "Mage",
                "method_name": "special_ability",
                "code_line": "damage = int(self._spell_power * 2 + self.calculate_base_damage())",
                "description": "Damage uses self._spell_power, a private attribute unique to Mage. This is encapsulation — spell_power is hidden from outside code, only Mage's own methods use it.",
                "inheritance_chain": ["Entity", "Character", "Hero", "Mage"],
                "concept": "Encapsulation",
            },
            {
                "class_name": "Character",
                "method_name": "add_status_effect",
                "code_line": "if effect not in self._status_effects:\n    self._status_effects.append(effect)",
                "description": "target.add_status_effect('burning') is called. This method lives in Character — any character (hero or enemy) can have status effects. Inheritance gives Mage access to this shared method.",
                "inheritance_chain": ["Entity", "Character"],
                "concept": "Inherited shared method",
            },
        ],
    },

    # ── Archer: Rain of Arrows ──
    "rain_of_arrows": {
        "summary": "Archer.special_ability() shows encapsulated state (_focus_stacks, _crit_chance) and polymorphic calculate_base_damage().",
        "steps": [
            {
                "class_name": "Archer",
                "method_name": "special_ability",
                "code_line": "def special_ability(self, target: Enemy) -> ActionResult:",
                "description": "Archer.special_ability() is called — implements Hero's abstract method. Rain of Arrows applies bleeding alongside heavy damage.",
                "inheritance_chain": ["Entity", "Character", "Hero", "Archer"],
                "concept": "Abstract method implementation",
            },
            {
                "class_name": "Archer",
                "method_name": "crit_chance (property)",
                "code_line": "@property\ndef crit_chance(self):\n    return min(0.90, self._base_crit_chance + self._focus_stacks * 0.05)",
                "description": "crit_chance is a @property — it's computed from private attributes each time it's accessed. This is encapsulation: internal _focus_stacks are hidden but their effect is exposed cleanly.",
                "inheritance_chain": ["Entity", "Character", "Hero", "Archer"],
                "concept": "Encapsulation via @property",
            },
            {
                "class_name": "Character",
                "method_name": "add_status_effect",
                "code_line": "target.add_status_effect('bleeding')",
                "description": "The bleeding status is applied via the shared Character method. Archer uses an inherited method — it didn't have to write this logic itself.",
                "inheritance_chain": ["Entity", "Character"],
                "concept": "Code reuse via inheritance",
            },
        ],
    },

    # ── Archer: Basic attack with crit ──
    "basic_attack_crit": {
        "summary": "Archer.calculate_base_damage() overrides Character's version — same call site, different behaviour (Polymorphism).",
        "steps": [
            {
                "class_name": "Archer",
                "method_name": "calculate_base_damage",
                "code_line": "is_crit = random.random() < self.crit_chance\nif is_crit:\n    return base * 2",
                "description": "CRITICAL HIT! Archer.calculate_base_damage() overrides Character's version. When a crit fires, damage doubles and focus_stacks resets to 0.",
                "inheritance_chain": ["Entity", "Character", "Hero", "Archer"],
                "concept": "Polymorphism",
            },
        ],
    },

    # ── Defend ──
    "defend": {
        "summary": "Hero.defend() is defined once in Hero and inherited by Warrior, Mage, and Archer without any override needed.",
        "steps": [
            {
                "class_name": "Hero",
                "method_name": "defend",
                "code_line": "self._defense += bonus\nself._mana = min(self._max_mana, self._mana + 10)",
                "description": "Hero.defend() is called. This method is defined once in Hero and inherited by ALL hero subclasses — none need to override it. This is a core benefit of inheritance: write once, use many times.",
                "inheritance_chain": ["Entity", "Character", "Hero"],
                "concept": "Inheritance (write once, use many)",
            },
        ],
    },

    # ── Special failed ──
    "special_failed": {
        "summary": "The special_ability() method checked mana first — a guard clause using encapsulated state.",
        "steps": [
            {
                "class_name": "Hero",
                "method_name": "special_ability",
                "code_line": "if self._mana < cost:\n    return ActionResult(action='special_failed', ...)",
                "description": "Not enough mana! The method reads self._mana — a private attribute — to decide whether to proceed. Encapsulation ensures only the Hero's own code modifies mana.",
                "inheritance_chain": ["Entity", "Character", "Hero"],
                "concept": "Encapsulation (guard clause)",
            },
        ],
    },

    # ── Enemy: Goblin Frenzy ──
    "goblin_frenzy": {
        "summary": "Goblin.special_attack() implements Enemy's abstract method with a multi-hit loop.",
        "steps": [
            {
                "class_name": "Goblin",
                "method_name": "special_attack",
                "code_line": "def special_attack(self, target: Hero) -> ActionResult:",
                "description": "Goblin.special_attack() implements Enemy's abstract method. Each concrete enemy has a unique implementation — this is polymorphism across the enemy hierarchy.",
                "inheritance_chain": ["Entity", "Character", "Enemy", "Goblin"],
                "concept": "Polymorphism (concrete implementation)",
            },
            {
                "class_name": "Character",
                "method_name": "take_damage",
                "code_line": "actual_damage = max(1, raw_damage - self._defense)",
                "description": "target.take_damage() is called 3 times. take_damage() is defined in Character and inherited by Hero — Goblin calls it on the Hero target without knowing which Hero subclass it is.",
                "inheritance_chain": ["Entity", "Character"],
                "concept": "Polymorphism (calling inherited methods on unknown subtype)",
            },
        ],
    },

    # ── Enemy: Ground Slam ──
    "ground_slam": {
        "summary": "Troll overrides decide_action() to regenerate first, then calls super().decide_action() — demonstrating super() in an enemy subclass.",
        "steps": [
            {
                "class_name": "Troll",
                "method_name": "decide_action",
                "code_line": "def decide_action(self, target: Hero) -> ActionResult:  # OVERRIDES Enemy",
                "description": "Troll.decide_action() OVERRIDES Enemy.decide_action(). This is the only enemy that overrides the AI method — it adds regeneration before calling the parent logic.",
                "inheritance_chain": ["Entity", "Character", "Enemy", "Troll"],
                "concept": "Method override in subclass",
            },
            {
                "class_name": "Character",
                "method_name": "heal",
                "code_line": "self._current_hp = min(self._max_hp, self._current_hp + amount)",
                "description": "self.heal() is called first — Troll regenerates HP. heal() is defined in Character and inherited by Troll for free.",
                "inheritance_chain": ["Entity", "Character"],
                "concept": "Inherited method (code reuse)",
            },
            {
                "class_name": "Enemy",
                "method_name": "decide_action",
                "code_line": "result = super().decide_action(target)  # delegates to Enemy",
                "description": "After regenerating, Troll calls super().decide_action() — delegating to Enemy's AI logic. super() lets Troll extend, not replace, the parent behaviour.",
                "inheritance_chain": ["Entity", "Character", "Enemy"],
                "concept": "super() delegation",
            },
            {
                "class_name": "Troll",
                "method_name": "special_attack",
                "code_line": "actual = max(1, damage)  # bypass take_damage(); Ground Slam ignores armor",
                "description": "Troll.special_attack() applies damage directly, bypassing take_damage() to ignore defense — similar to Mage's magic bolt.",
                "inheritance_chain": ["Entity", "Character", "Enemy", "Troll"],
                "concept": "Selective method bypass",
            },
        ],
    },

    # ── Enemy: Fire Breath ──
    "fire_breath": {
        "summary": "Dragon.special_attack() uses _fire_charges — private state unique to the Dragon subclass (encapsulation).",
        "steps": [
            {
                "class_name": "Dragon",
                "method_name": "special_attack",
                "code_line": "if self._fire_charges <= 0:\n    return self._basic_enemy_attack(target)",
                "description": "Dragon checks its private _fire_charges attribute — unique to Dragon subclass. When depleted, it falls back to the parent's _basic_enemy_attack(). Encapsulation hides the charge state.",
                "inheritance_chain": ["Entity", "Character", "Enemy", "Dragon"],
                "concept": "Encapsulation (subclass private state)",
            },
            {
                "class_name": "Character",
                "method_name": "take_damage",
                "code_line": "actual_damage = max(1, raw_damage - self._defense)",
                "description": "target.take_damage() runs through Character's shared logic. Dragon calls it on the Hero without knowing if it's a Warrior, Mage, or Archer.",
                "inheritance_chain": ["Entity", "Character"],
                "concept": "Polymorphism (duck typing)",
            },
        ],
    },

    # ── Enemy: Soul Drain ──
    "soul_drain": {
        "summary": "Lich.soul_drain() calls both take_damage() (on target) and heal() (on self) — both inherited from Character.",
        "steps": [
            {
                "class_name": "Lich",
                "method_name": "special_attack",
                "code_line": "actual = target.take_damage(drain_amount)\nhealed = self.heal(actual)",
                "description": "Soul Drain calls two inherited Character methods: take_damage() on the target and heal() on self. Neither is overridden — Lich uses them as-is from Character.",
                "inheritance_chain": ["Entity", "Character", "Enemy", "Lich"],
                "concept": "Inherited shared methods",
            },
            {
                "class_name": "Character",
                "method_name": "heal",
                "code_line": "self._current_hp = min(self._max_hp, self._current_hp + amount)",
                "description": "The heal() call is on self (the Lich). This is the same method as when a hero heals — both Hero and Enemy inherit from Character, so they share the same heal() logic.",
                "inheritance_chain": ["Entity", "Character"],
                "concept": "Shared base class method",
            },
        ],
    },

    # ── Enemy basic attack ──
    "enemy_basic_attack": {
        "summary": "Enemy._basic_enemy_attack() is defined once in Enemy and used by all enemy types when they don't use a special.",
        "steps": [
            {
                "class_name": "Enemy",
                "method_name": "_basic_enemy_attack",
                "code_line": "damage = self.calculate_base_damage()\nactual = target.take_damage(damage)",
                "description": "Enemy._basic_enemy_attack() is a protected method defined once in Enemy, inherited by Goblin/Troll/Dragon/Lich. None need to override it — inheritance eliminates duplication.",
                "inheritance_chain": ["Entity", "Character", "Enemy"],
                "concept": "Inheritance (DRY principle)",
            },
        ],
    },

    # ── Status effect tick ──
    "status_tick": {
        "summary": "Character.tick_status_effects() demonstrates a shared method that works identically for heroes and enemies.",
        "steps": [
            {
                "class_name": "Character",
                "method_name": "tick_status_effects",
                "code_line": "if 'bleeding' in self._status_effects:\n    self._current_hp -= bleed_dmg",
                "description": "tick_status_effects() runs on both heroes and enemies. It's defined once in Character — a perfect example of reuse via inheritance. All combatants share this logic.",
                "inheritance_chain": ["Entity", "Character"],
                "concept": "Code reuse (defined once, runs everywhere)",
            },
        ],
    },
}


class TraceService:
    """Generates educational code traces for game actions.

    Attributes:
        None — all logic is stateless (no instance state needed)
    """

    @staticmethod
    def get_trace(action_key: str, hero_class: str = "") -> CodeTrace:
        """Return the CodeTrace for a given action.

        For basic_attack, the trace may vary between hero classes:
        Mage's basic attack overrides Hero's, so it gets the 'magic_bolt' trace.

        Args:
            action_key : The action identifier (e.g. "whirlwind_strike")
            hero_class : The hero's class name (used to route basic_attack)

        Returns:
            CodeTrace object with steps and summary
        """
        # Mage's basic attack is a magic bolt (different trace)
        resolved_key = action_key
        if action_key == "basic_attack" and hero_class == "Mage":
            resolved_key = "magic_bolt"

        trace_data = _TRACE_LIBRARY.get(resolved_key, _TRACE_LIBRARY.get("basic_attack"))
        if not trace_data:
            trace_data = {
                "summary": "Action processed through the OOP hierarchy.",
                "steps": [],
            }

        steps = [TraceStep(**step) for step in trace_data["steps"]]
        return CodeTrace(
            steps=steps,
            action_key=resolved_key,
            summary=trace_data["summary"],
        )

    @staticmethod
    def get_enemy_trace(action_key: str) -> CodeTrace:
        """Return the CodeTrace for an enemy action."""
        trace_data = _TRACE_LIBRARY.get(action_key, _TRACE_LIBRARY.get("enemy_basic_attack"))
        if not trace_data:
            trace_data = {
                "summary": "Enemy action processed through the OOP hierarchy.",
                "steps": [],
            }
        steps = [TraceStep(**step) for step in trace_data["steps"]]
        return CodeTrace(
            steps=steps,
            action_key=action_key,
            summary=trace_data["summary"],
        )

    @staticmethod
    def list_concepts() -> list[dict]:
        """Return all OOP concepts demonstrated in CodeQuest."""
        return [
            {
                "name": "Abstraction",
                "description": "Entity and Character are abstract — they define the interface but can't be instantiated directly.",
                "example": "class Entity(ABC): @abstractmethod def get_stats(self) -> dict: pass",
            },
            {
                "name": "Encapsulation",
                "description": "All attributes are private (_name, _current_hp). External code uses @property accessors.",
                "example": "@property\ndef current_hp(self) -> int:\n    return self._current_hp",
            },
            {
                "name": "Inheritance",
                "description": "Warrior → Hero → Character → Entity. Each class builds on its parent with super().__init__().",
                "example": "class Warrior(Hero):\n    def __init__(self, name):\n        super().__init__(name, 'Warrior', ...)",
            },
            {
                "name": "Polymorphism",
                "description": "calculate_base_damage() behaves differently in Warrior, Mage, and Archer — same method name, different behaviour.",
                "example": "# Warrior adds rage bonus; Mage adds mana scaling; Archer adds crits",
            },
            {
                "name": "Method Override",
                "description": "Mage overrides basic_attack(), Troll overrides decide_action(). Subclasses can replace or extend parent methods.",
                "example": "class Mage(Hero):\n    def basic_attack(self, target):\n        # completely different from Hero.basic_attack()",
            },
            {
                "name": "super()",
                "description": "Warrior calls super().calculate_base_damage() to chain to Character's version before adding its own bonus.",
                "example": "def calculate_base_damage(self):\n    base = super().calculate_base_damage()  # ← chain\n    return base + rage_bonus",
            },
            {
                "name": "Abstract Methods",
                "description": "Hero declares special_ability() as abstract. Every hero subclass MUST implement it, or Python raises TypeError.",
                "example": "@abstractmethod\ndef special_ability(self, target: Enemy) -> ActionResult:\n    pass",
            },
            {
                "name": "Factory Pattern",
                "description": "create_hero('Warrior', 'Arthur') creates the right subclass without the caller knowing the concrete type.",
                "example": "def create_hero(hero_class: str, name: str) -> Hero:\n    return HERO_REGISTRY[hero_class](name)",
            },
        ]
