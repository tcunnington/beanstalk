# The Layered Pragmatist: Python Software Design & Clean Code Guide

> **The Creed:** Optimize for low cognitive overhead. Code should build up complexity linearly, ensuring that the novel contribution of any single function remains minimal, highly readable, and easily testable.

---

## Part 1: Core Philosophy

* **Pragmatism Over Purity:** We do not write abstract code for hypothetical futures. Use the simplest tool that adequately solves today's problem.
* **Low Cognitive Overhead:** Code must be optimized for readability and maintainability. If a junior engineer cannot understand the flow of data within a few minutes, the abstraction is failing.
* **Multi-Paradigm Python:** Python is not Java. Mix procedural, functional, and object-oriented styles where they naturally fit. Favor functions and modules over classes unless state management or clear developer UX requires an object.

---

## Part 2: The Three-Tier Architecture (The Velocity of Change)

We organize behavior into three distinct layers based on how frequently the underlying concepts change.

```
+-------------------------------------------------------+
|                    TIER 3: SERVICES                   |
|  - Constantly-changing high-level workflows          |
|  - Coordinates application flow & external infra     |
+---------------------------+---------------------------+
                            |
                            v
+-------------------------------------------------------+
|                 TIER 2: DOMAIN LOGIC                  |
|  - Slowly-changing core business concepts             |
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

### Tier 1: Utilities (`utils`)
* **Velocity:** *Never-changing.*
* **What it is:** Low-level, highly generic helper functions. They have no concept of our specific business domain (e.g., a date formatting helper, a custom dictionary merger).
* **Testing:** Easily and thoroughly unit-tested with pure inputs and outputs; zero mocking required.

### Tier 2: Domain Logic
* **Velocity:** *Slowly-changing.*
* **What it is:** This layer models our core business concepts and abstractions. It includes our data shapes (using `@dataclass` or `Enum`) and the pure functions that manipulate them. 
* **The Rules:**
    * **Anemic Domain Models:** Keep business logic outside of data objects. Methods on data objects must be strictly limited to local transformations, derived properties, or formatting (e.g., `__str__`, `.to_json()`). Complex workflows belong in the functions of the Domain Logic or Service layers.
    * **Immutability by Default:** Favor immutable data structures (`@dataclass(frozen=True)`) to prevent side effects. If a function mutates an incoming object, it must be the explicit, singular purpose of that function. Unintended mutations are PR-blocking smells.
    * **Scope:** Logic here is tightly restricted in scope. It defines *how* we manipulate domain data. If a module in this layer starts importing from numerous other domain modules without producing a singular, core abstraction, it is likely leaking into a Service.
* **Testing:** Tested by verifying business rules against domain data structures, keeping external dependencies out.

### Tier 3: Services
* **Velocity:** *Constantly-changing.*
* **What it is:** High-level orchestrators that capture complex workflows. Services handle the *when* and *why* of our business operations. They coordinate application flow, manage external infrastructure (DBs, APIs), and encapsulate state when necessary.
* **The Rules:**
    * **Explicit over Implicit State:** Avoid global or singleton states imported across modules. Pass dependencies explicitly through function arguments or constructors, even if it results in longer function signatures. Knowing exactly where state comes from is worth the verbosity.
    * **Composition Over DI Frameworks:** We strongly favor object and function composition over inheritance and dependency injection (DI) frameworks. Use standard Python composition (e.g., passing a repository into a service constructor via `__init__`) rather than introducing complex, magical DI libraries.
    * **Duck Typing over ABCs:** Prefer duck typing and Python `Protocols` over explicit Abstract Base Classes (`ABCs`) when formalizing interfaces.
* **Testing:** Tested by verifying coordination. This is where your integration testing or mocking of external boundaries primarily lives.

### Architectural Red Flags (What to Look For in PRs)
* **Service-to-Service Chains:** If `ServiceA` calls `ServiceB` which calls `ServiceC`, stop. This is a sign that a core business abstraction is missing. We need to compress this complexity down into the *Domain Logic* layer.
* **Premature Design Patterns:** Do not introduce structural design patterns (Strategy, Factory, etc.) to "future-proof" code. Use them only when implementing library-level code or when a pattern natively maps to Python primitives (e.g., decorators, iterators).
* **Leaky Complexity:** Every layer should build on the last. If a high-level Service is performing low-level dictionary manipulations, that code needs to be pushed down into a utility or domain operation.

---

## Part 3: Micro-Architecture & Clean Code Rules

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

### 5. Errors & Resilience (Pythonic Exception Patterns)
* **Exceptions are for the Unexpected:** Use exceptions exclusively to signal clear problems, breaking issues, or genuinely unexpected states. Do not use them as optional code paths or standard business logic flow control.
* **Embrace EAFP:** Favor trying an operation and catching the failure over writing long strings of defensive `if/else` checks (Easier to Ask Forgiveness than Permission).
* **Catch the Narrowest Exception:** Never use a bare `except:`. Avoid catching a generic `Exception` unless you are logging the traceback and instantly re-raising it. Only catch specific errors you explicitly intend to handle right there (e.g., `ValueError`, `KeyError`).
* **Never Swallow Silently:** Never hide a failure behind an empty `except: pass` block. It blinds both developers and AI tools to real logic errors.
* **Chain Explicitly:** When wrapping a lower-level error in a domain-specific custom exception, use the `from` keyword to preserve the underlying stack trace for debugging (e.g., `raise DomainError(...) from err`).

### 6. Documentation & Comments
* **Docstrings for Interface Context:** While code logic must remain self-explanatory, up-to-date documentation acts as a vital navigation map for teams and AI agents.
* **Keep it High-Level:** Every public module and complex function should feature a brief Google-style docstring explaining what it does and its return behavior. Don't duplicate native type hints in the text—keep the description concise so it never dwarfs the code itself.
* **Kill Dead Code:** Never check in commented-out blocks of code. Trust version control to handle history.

### 7. The Boy Scout Rule
* **Leave it Cleaner:** Every time you touch a file—whether you are a human submitting a PR or an AI agent fixing a bug—leave that file in a slightly cleaner state than you found it. Fix a stale docstring, break up a bloated loop, or tighten up an argument list before you commit.
