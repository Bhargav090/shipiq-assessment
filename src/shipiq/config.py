import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    log_level: str
    api_key: str | None

    @staticmethod
    def from_env() -> "Settings":
        return Settings(
            log_level=os.getenv("SHIPIQ_LOG_LEVEL", "INFO").upper(),
            api_key=os.getenv("SHIPIQ_API_KEY") or None,
        )
