"""Runtime configuration, read from BEANSTALK_-prefixed environment variables."""

from decimal import Decimal
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

from beanstalk.model.predict import DEFAULT_ARTIFACT_PATH


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="BEANSTALK_")

    database_path: Path = Path("beanstalk.db")
    artifact_path: Path = DEFAULT_ARTIFACT_PATH
    annual_rate: Decimal = Decimal("0.12")
    approve_risk_below: float = 0.25
    decline_risk_at: float = 0.60
