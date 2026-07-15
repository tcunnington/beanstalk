# The Layered Pragmatist: Python Software Design & Clean Code Guide

> **The Creed:** Optimize for low cognitive overhead. Code should build up complexity linearly, ensuring that the novel contribution of any single function remains minimal, highly readable, and easily testable.

---

## Part 1: Core Philosophy

* **Pragmatism Over Purity:** We do not write abstract code for hypothetical futures. Use the simplest tool that adequately solves today's problem.
* **Low Cognitive Overhead:** Code must be optimized for readability and maintainability. If a junior engineer cannot understand the flow of data within a few minutes, the abstraction is failing.
* **Multi-Paradigm Python:** Python is not Java. Mix procedural, functional, and object-oriented styles where they naturally fit. Favor functions and modules over classes unless state management or clear developer UX requires an object.

---

## Part 2: The Four-Tier Architecture (The Velocity of Change)

We organize behavior into four layers based on how frequently the underlying
concepts change. Each tier may import only from tiers below it.

```
+-------------------------------------------------------+
|                    TIER 4: SERVICES                   |
|  - Usually stable coordination & facades              |
|  - Orchestrates features; owns cross-cutting infra    |
+---------------------------+---------------------------+
                            |
                            v
+-------------------------------------------------------+
|                TIER 3: FEATURE SANDBOXES              |
|  - Constantly-changing, isolated mini-apps            |
|  - Build on core truths; never import each other      |
+---------------------------+---------------------------+
                            |
                            v
+-------------------------------------------------------+
|                   TIER 2: CORE DOMAIN                 |
|  - Slowly-changing, enterprise-wide concepts          |
|  - Native Types (@dataclass, Enum) & Pure Functions   |
+---------------------------+---------------------------+
                            |
                            v
+-------------------------------------------------------+
|                    TIER 1: UTILITIES                  |
|  - Never-changing low-level generic helpers           |
|  - No domain context; pure input/output behavior      |
+-------------------------------------------------------+
```

A useful mental model: were this a set of microservices instead of a modular
monolith, the **features** would be the services and the **services tier** would
be the pub/sub bus wiring them together. That is why features never call each
other directly — they meet at the coordination tier, never in a private back
channel.

### Tier 1: Utilities (`utils`)
* **Velocity:** *Never-changing.*
* **What it is:** Low-level, highly generic helper functions. They have no concept of our specific business domain (e.g., a date formatting helper, a custom dictionary merger). Pure third-party libraries (numpy, toolz, Shapely) are welcome here — the bar is *zero business context*, not zero dependencies.
* **Testing:** Easily and thoroughly unit-tested with pure inputs and outputs; zero mocking required.

### Tier 2: Core Domain (`core`)
* **Velocity:** *Slowly-changing.*
* **What it is:** The pure, stable foundation: enterprise-wide data shapes (using `@dataclass` or `Enum`) and the pure functions that manipulate them. Core holds the truths shared across *every* feature, and it never leaks feature-specific logic — if a concept only one capability cares about is creeping in, it belongs in that feature, not here.
* **The Rules:**
    * **Anemic Domain Models:** Keep business logic outside of data objects. Methods on data objects must be strictly limited to local transformations, derived properties, or formatting (e.g., `__str__`, `.to_json()`). Complex workflows belong in the pure functions of Core or in the Service layer.
    * **Immutability by Default:** Favor immutable data structures (`@dataclass(frozen=True)`) to prevent side effects. If a function mutates an incoming object, it must be the explicit, singular purpose of that function. Unintended mutations are PR-blocking smells.
    * **Scope:** Logic here is tightly restricted in scope. It defines *how* we manipulate core data. If a module in this layer starts importing from numerous other core modules without producing a singular, shared abstraction, it is likely leaking into a Feature or a Service.
* **Testing:** Tested by verifying business rules against core data structures, keeping external dependencies out.

### Tier 3: Feature Sandboxes (`features`)
* **Velocity:** *Constantly-changing.*
* **What it is:** Isolated mini-applications, one per product capability (a risk scorer, a recommendation engine). A feature builds on core truths and utilities but is otherwise a sandbox: the team that owns it is free to grow whatever internal structure it needs — its own helpers, its own sub-packages, its own third-party stack (sklearn, torch, an external SDK).
* **The Rules:**
    * **One Entry Point:** Each feature exposes its capability through a single `entrypoint.py`. Everything else in the feature is private; outside code imports the entrypoint and nothing deeper. The entrypoint speaks in Core vocabulary — it takes and returns core types (or primitives), so the coordination tier can wire features together without knowing their internals.
    * **No Cross-Feature Imports:** Features never import each other. Two capabilities that need to cooperate do so *through the service tier*, never by reaching into a sibling's internals. (Enforced: the `independence` contract.)
    * **Sandbox Freedom:** Inside the boundary, pragmatism rules. A feature may use frameworks and heavyweight libraries that Core and Utils forbid; it may lay out its own directory tree however its complexity demands.
* **Testing:** Each feature is tested in isolation through its entrypoint, with its own fixtures.

### Tier 4: Services
* **Velocity:** *Usually stable.*
* **What it is:** Coordination-oriented services: lightweight facades that manage high-level flow and orchestrate communication *between* features. Services handle the *when* and *why* of our business operations, own the cross-cutting infrastructure that coordination needs (databases, settings, queues), and may pass Core types straight through. A service is the broker, not a fifth feature — if real product logic accumulates here, it wants to move down into a feature or Core.
* **The Rules:**
    * **Explicit over Implicit State:** Avoid global or singleton states imported across modules. Pass dependencies explicitly through function arguments or constructors, even if it results in longer function signatures. Knowing exactly where state comes from is worth the verbosity.
    * **Composition Over DI Frameworks:** We strongly favor object and function composition over inheritance and dependency injection (DI) frameworks. Use standard Python composition (e.g., passing a repository into a service constructor via `__init__`) rather than introducing complex, magical DI libraries.
    * **Duck Typing over ABCs:** Prefer duck typing and Python `Protocols` over explicit Abstract Base Classes (`ABCs`) when formalizing interfaces. A service declares what it needs from a feature as a `Protocol` in Core terms; the feature's entrypoint conforms structurally.
* **Testing:** Tested by verifying coordination. This is where your integration testing or mocking of external boundaries primarily lives.

### Architectural Red Flags (What to Look For in PRs)
* **Cross-Feature Back Channels:** A feature importing another feature's internals. Route the collaboration through a service instead; the sandbox boundary is load-bearing.
* **Service-to-Service Chains:** If `ServiceA` calls `ServiceB` which calls `ServiceC`, stop. This is a sign that a core business abstraction is missing. We need to compress this complexity down into the *Core Domain* layer.
* **Fat Services:** A coordination service growing real product logic. It should stay a thin broker; push the logic down into a feature or Core.
* **Premature Design Patterns:** Do not introduce structural design patterns (Strategy, Factory, etc.) to "future-proof" code. Use them only when implementing library-level code or when a pattern natively maps to Python primitives (e.g., decorators, iterators).
* **Leaky Complexity:** Every layer should build on the last. If a high-level Service is performing low-level dictionary manipulations, that code needs to be pushed down into a utility or core operation.

---

## Part 3: Micro-Architecture & Clean Code Rules

*Much of this section is inspired by and loosely adapted from Robert C. Martin's* Clean Code**

### 1. Naming & Readability
* **Reveal Intent Over Snippets:** Names must tell the reader exactly why a variable or function exists (e.g., `days_since_last_backup` instead of `d`).
* **Name by Domain, Not Implementation:** Name variables and arguments after the business or application concept they represent, not their technical mechanism or data type.
    * *Bad:* `constructor_kwargs = {"timeout": 30}` or `user_list = []`
    * *Good:* `connection_policies = {"timeout": 30}` or `active_subscribers = []`
* **Case Conventions:** Use `snake_case` for functions and variables, and `CamelCase` nouns for classes.

### 2. Function Structure & Argument Rules
* **Max 100–120 Lines:** Keep functions highly focused. Even if AI can read massive blocks easily, human oversight still happens 5–10% of the time.
* **Do One Thing:** A function should handle exactly one logical operation. If a function reads a file, parses it, and saves it, split it into three.
* **The Pythonic Argument Rule:** Keep mandatory positional arguments to a minimum (ideally <= 2). If you need to pass a cluster of tightly coupled data, group them using a Python `@dataclass`.
* **The Python Exception:** It is entirely acceptable to use multiple optional keyword-only configuration arguments (e.g., `def parse_data(file_path, *, format="csv", delimiter=","):`).

### 3. Scope & Function Placement
* **The Stepdown Rule:** Organize source files like a newspaper article. High-level orchestrator functions belong at the top; low-level implementation details belong at the bottom.
* **Placement of Helpers:** If `function_a` calls a dedicated helper `_helper_b`, place `_helper_b` directly below `function_a` with a leading underscore to signal it is private to that module. 
* **Avoid Nesting:** This top-to-bottom layout is preferred over nesting helper functions inside parent functions, which makes unit testing isolated edge cases impossible. (Standard closures, decorators, or short lambdas are exempt from this).

### 4. Pythonic Design over OOP
* **Embrace None Intentionally:** It is perfectly idiomatic to use `None` as a default argument or an explicit "not found" state. Always pair this with clear Python type hinting (e.g., `user: User | None = None`).
* **Ditch Getters and Setters:** Access attributes directly (`user.email = "..."`). If you eventually need validation logic, seamlessly upgrade it using Python's native `@property` decorator without changing your public API.
* **Prefer Functions Over Classes:** You do not need to wrap everything in a class. If you are writing pure transformations with no internal state, write standalone Python functions.

### 5. Errors & Resilience
* **Exceptions for the Exceptional:** Reserve exceptions for genuinely unexpected failures, not routine business logic — and once you're in that territory, prefer trying the operation and catching the failure (EAFP) over defensive `if/else` checks (LBYL).
* **Catch Narrow, Never Swallow:** Never use a bare `except:` or catch a generic `Exception` — only catch specific errors you intend to handle (e.g., `ValueError`, `KeyError`). And never hide a failure behind an empty `except: pass`; a caught exception must be logged, handled, or re-raised, never silently discarded.
* **Chain Explicitly:** When wrapping a lower-level error, use `from` to preserve the underlying stack trace (e.g., `raise DomainError(...) from err`).

### 6. Documentation & Comments
* **Docstrings for Interface Context:** While code logic must remain self-explanatory, up-to-date documentation acts as a vital navigation map for teams and AI agents.
* **Keep it High-Level:** Every public module and complex function should feature a brief Google-style docstring explaining what it does and its return behavior. Don't duplicate native type hints in the text—keep the description concise so it never dwarfs the code itself.
* **Kill Dead Code:** Never check in commented-out blocks of code. Trust version control to handle history.

### 7. The Boy Scout Rule
* **Leave it Cleaner:** Every time you touch a file—whether you are a human submitting a PR or an AI agent fixing a bug—leave that file in a slightly cleaner state than you found it. Fix a stale docstring, break up a bloated loop, or tighten up an argument list before you commit.
