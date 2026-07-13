"""Runtime configuration, read from BEANSTALK_-prefixed environment variables."""

from decimal import Decimal
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="BEANSTALK_")

    database_path: Path = Path("beanstalk.db")
    # None -> the risk_scorer feature loads its own default artifact. Services
    # doesn't know where the feature keeps it; that's the feature's business.
    artifact_path: Path | None = None
    annual_rate: Decimal = Decimal("0.12")
    approve_risk_below: float = 0.25
    decline_risk_at: float = 0.60
