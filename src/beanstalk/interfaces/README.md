# interfaces/ — delivery mechanisms

**Purpose:** every way the outside world reaches Beanstalk lives here: the
partner REST API, the reviewer UI, and (in a larger app) DAGs, CLIs, queue
workers, scheduled jobs. One subpackage per mechanism.

**Kind / velocity:** vertical apps. They change when a delivery channel
changes, independently of each other and of the business.

**What belongs here**
- Thin entry points: parse/validate input (Pydantic at the boundary), call a
  service, format the response. Routes, forms, templates, DAG definitions.
- Framework wiring (FastAPI app factories, router registration).

**What must NOT be here**
- Business logic — that's `core/`. If an endpoint grows an `if` about the
  business, push it down.
- Orchestration or persistence — that's `services/`.
- Imports of another interface, or of any `features/` sandbox directly.
  Interfaces and features relate many-to-many *through services* — the same
  service method backs the API, the UI, and tomorrow's DAG.

**Allowed imports:** `services`, `core`, `utils`. Enforced by the layers and
independence import contracts (see [src/beanstalk/README.md](../README.md)).

| Subpackage | Mechanism |
|---|---|
| [api/](api/README.md) | partner-facing REST API (FastAPI, :8000) |
| [ui/](ui/README.md) | internal reviewer queue (FastAPI + Jinja, :8001) |
| [airflow/](airflow/README.md) | stub — what a batch/orchestration interface would look like |
