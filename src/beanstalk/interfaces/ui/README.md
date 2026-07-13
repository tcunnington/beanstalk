# interfaces/ui — internal reviewer UI

Server-rendered (FastAPI + Jinja2) queue for human reviewers to resolve
NEEDS_REVIEW decisions. Runs on :8001 (`just ui`).

| Module | Provides |
|---|---|
| `forms.py` | `ReviewForm` — Pydantic validation of the approve/decline form |
| `routes.py` | queue page, application detail, `POST .../review` |
| `app.py` | `create_app()` factory (explicit composition, `uvicorn --factory`) |
| `templates/` | `base.html`, `queue.html`, `detail.html` |

**Boundary rules:** form input is validated through a Pydantic model before it
touches the service; invalid verdicts → 422, double-reviews → 409, unknown
ids → 404 (all via narrow `except ... raise ... from`).

**What must NOT be here:** business rules, JSON API endpoints (that's `api/`),
direct `beanstalk.model` imports (independence contract), imports from `api/`.

**Allowed imports:** `services`, `domain`, `utils`, fastapi/jinja2/pydantic.

**Testing:** `tests/integration/test_ui.py` — submit → queue → resolve flow.
