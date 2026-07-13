# features/ — tier 3: feature sandboxes

**Velocity: constantly-changing.** One subpackage per product capability. Each is an
isolated mini-application — the risk model Beanstalk sells, the equipment
recommender it upsells with — that builds on core truths but is otherwise free
to grow whatever it needs.

| Feature | Capability | Entrypoint exposes |
|---|---|---|
| [risk_scorer/](risk_scorer/README.md) | default-risk model (real: sklearn) | `load_scorer()` → scores an application in [0, 1] |
| [machine_recommender/](machine_recommender/README.md) | espresso-machine suggestion (stub) | `load_recommender()` → suggests an `EquipmentItem` |

**The two rules that make a sandbox a sandbox:**

1. **One entry point.** Everything a feature offers is reached through its
   `entrypoint.py`; the rest of the package is private. The entrypoint speaks
   **core vocabulary** — takes and returns core types (or primitives) — so
   services can wire features together without knowing their internals. (The
   coordination tier declares what it needs as a `Protocol` in core terms; the
   entrypoint conforms structurally — see `services/scoring.py`.)
2. **No cross-feature imports.** Features never import each other; two that must
   cooperate do so *through services*. Enforced by the `independence` contract.

**Sandbox freedom.** Inside the boundary, do what the problem needs: any
third-party stack (sklearn, torch, an external SDK — none of the tier-1/2 purity
rules apply here), any internal layout (own helpers, own sub-packages, even an
own private `utils`). The metaphor: if these were microservices, each feature
would be one service and the `services/` tier would be the message bus.

**Allowed imports:** `beanstalk.core`, `beanstalk.utils`, and anything the
sandbox needs. Never another feature; never `services` or `interfaces`.

**Testing:** each feature in isolation through its entrypoint (`tests/features/`).
