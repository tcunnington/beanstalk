"""Manually exercise the partner API with example payloads, one function per endpoint.

Each example input is a plain dict, validated against the same Pydantic schema
the route expects — so the payload sent over HTTP is provably shaped like what
FastAPI will accept, without going through ApplicationService directly.
Requires the API running first (`just api`).

Usage:
    uv run python scripts/try_api.py submit_application
    uv run python scripts/try_api.py list_applications
    uv run python scripts/try_api.py get_application <application_id>
    uv run python scripts/try_api.py generate_random_application
    uv run python scripts/try_api.py delete_application <application_id>
"""

import json
import random

import fire
import httpx

from beanstalk.core.application import EquipmentCategory
from beanstalk.interfaces.api.schemas import ApplicationRequest
from beanstalk.services.decision_records import DecisionRecordStore
from beanstalk.services.settings import Settings

DEFAULT_BASE_URL = "http://localhost:8000"

_SILLY_ADJECTIVES = ["Sleepy", "Wobbly", "Feral", "Lucky", "Rowdy", "Foggy"]
_SILLY_ANIMALS = ["Wolf", "Sparrow", "Otter", "Marmot", "Yak", "Ferret"]

EXAMPLE_APPLICATION_REQUEST = {
    "cafe": {
        "name": "Little Wolf",
        "months_in_business": 24,
        "monthly_revenue": "38000",
        "seats": 22,
        "has_existing_financing": False,
    },
    "equipment": {
        "category": "espresso_machine",
        "description": "Slayer Steam LP, 2 group",
        "price": "18500",
    },
    "term_months": 48,
    "down_payment": "3700",
}


def submit_application(base_url: str = DEFAULT_BASE_URL) -> None:
    """POST /applications with EXAMPLE_APPLICATION_REQUEST, skipping a cafe-name dup."""
    cafe_name = EXAMPLE_APPLICATION_REQUEST["cafe"]["name"]
    if cafe_name in _existing_cafe_names(base_url):
        print(f"{cafe_name!r} already exists, skipping.")
        return
    payload = ApplicationRequest.model_validate(EXAMPLE_APPLICATION_REQUEST)
    response = httpx.post(f"{base_url}/applications", json=payload.model_dump(mode="json"))
    _print_response(response)


def generate_random_application(base_url: str = DEFAULT_BASE_URL) -> None:
    """POST /applications with a randomly generated payload; retries on a name collision."""
    existing_names = _existing_cafe_names(base_url)
    cafe_name = _random_cafe_name()
    while cafe_name in existing_names:
        cafe_name = _random_cafe_name()
    category = random.choice(list(EquipmentCategory))
    price = random.randint(2_000, 40_000)
    payload = {
        "cafe": {
            "name": cafe_name,
            "months_in_business": random.randint(1, 240),
            "monthly_revenue": str(random.randint(5_000, 80_000)),
            "seats": random.randint(4, 60),
            "has_existing_financing": random.choice([True, False]),
        },
        "equipment": {
            "category": category.value,
            "description": f"Random {category.value.replace('_', ' ')}",
            "price": str(price),
        },
        "term_months": random.choice([24, 36, 48, 60]),
        "down_payment": str(random.randint(0, price // 3)),
    }
    request = ApplicationRequest.model_validate(payload)
    response = httpx.post(f"{base_url}/applications", json=request.model_dump(mode="json"))
    _print_response(response)


def delete_application(application_id: str, database_path: str | None = None) -> None:
    """Delete a stored application directly — intentionally no API/UI route for this.

    Bypasses the running server and writes straight to the sqlite file, so it
    works even though the API deliberately doesn't expose deletion.
    """
    records = DecisionRecordStore(database_path or Settings().database_path)
    records.delete(application_id)
    records.close()
    print(f"Deleted {application_id}")


def list_applications(base_url: str = DEFAULT_BASE_URL) -> None:
    """GET /applications, with each item's application_id promoted to the top level."""
    response = httpx.get(f"{base_url}/applications")
    applications = [
        {"application_id": item["decision"]["application_id"], **item} for item in response.json()
    ]
    print(response.status_code)
    print(json.dumps(applications, indent=2))


def get_application(application_id: str, base_url: str = DEFAULT_BASE_URL) -> None:
    """GET /applications/{application_id}."""
    response = httpx.get(f"{base_url}/applications/{application_id}")
    _print_response(response)


def _existing_cafe_names(base_url: str) -> set[str]:
    response = httpx.get(f"{base_url}/applications")
    response.raise_for_status()
    return {application["cafe_name"] for application in response.json()}


def _random_cafe_name() -> str:
    return f"{random.choice(_SILLY_ADJECTIVES)} {random.choice(_SILLY_ANIMALS)}"


def _print_response(response: httpx.Response) -> None:
    print(response.status_code)
    print(json.dumps(response.json(), indent=2))


if __name__ == "__main__":
    fire.Fire()
