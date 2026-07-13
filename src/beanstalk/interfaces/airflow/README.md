# interfaces/airflow — stub

Beanstalk has no batch orchestration, so this is a placeholder showing where a
DAG interface *would* go and what shape it would take. It exists because larger
apps almost always grow one, and the pattern is worth pinning before it's needed.

A DAG file is an interface, exactly like `api/routes.py` is: a thin entry point
that declares *when and in what order* service methods run, and nothing else.

```python
# dags/nightly_rescore.py — what a real one would look like
from airflow.decorators import dag, task
from beanstalk.services.applications import build_application_service

@dag(schedule="@daily")
def nightly_rescore():
    @task
    def rescore_pending():
        service = build_application_service()
        for application in service.review_queue():
            ...  # call a service method per item; no business logic here

nightly_rescore()
```

Rules, same as every interface:

- imports `services` only — never a `features/` sandbox, never another interface
- no business logic in tasks; if a task grows an `if` about the business, that
  branch belongs in `core/` and the orchestration of it in `services/`
- scheduling/retry/alerting config is interface concern and belongs here

If this becomes real: add the `airflow` dependency in its own optional group,
keep DAG files importable without a scheduler running, and add
`beanstalk.interfaces.airflow` to the independence import contract.
