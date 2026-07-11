# api/ — partner-facing REST API (vertical app)

FastAPI app for equipment vendors and partners: submit financing applications,
fetch decisions. Runs on :8000 (`just api`).

| Module | Provides |
|---|---|
| `schemas.py` | Pydantic request/response models + `to_domain()`/`from_domain()` converters |
| `routes.py` | `POST /applications`, `GET /applications`, `GET /applications/{id}` |
| `app.py` | `create_app()` factory — explicit composition, run via `uvicorn --factory` |

**Boundary rules:** everything crossing HTTP is a Pydantic model (`schemas.py`);
conversion happens there so routes stay thin and the domain stays pydantic-free.
Unknown ids → 404 via EAFP (`except ApplicationNotFoundError ... raise ... from`).

**What must NOT be here:** business rules, direct `beanstalk.model` imports
(the independence contract fails the build — go through `services`), imports
from `ui/`.

**Allowed imports:** `services`, `domain`, `utils`, fastapi/pydantic.

**Testing:** `tests/integration/test_api.py` via TestClient with a stub scorer.
