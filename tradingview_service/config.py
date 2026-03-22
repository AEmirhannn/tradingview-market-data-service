import os
from dataclasses import dataclass

from tradingview_service.dotenv import load_dotenv


@dataclass(frozen=True)
class AppConfig:
    host: str = "0.0.0.0"
    port: int = 6969
    tradingview_username: str = ""
    tradingview_password: str = ""
    request_timeout_seconds: int = 20
    cache_ttl_seconds: int = 15
    default_limit: int = 500
    max_limit: int = 5000
    log_level: str = "INFO"

    @classmethod
    def from_env(cls) -> "AppConfig":
        load_dotenv()
        return cls(
            host=os.getenv("HOST", "0.0.0.0"),
            port=int(os.getenv("PORT", "6969")),
            tradingview_username=os.getenv("TRADINGVIEW_USERNAME", ""),
            tradingview_password=os.getenv("TRADINGVIEW_PASSWORD", ""),
            request_timeout_seconds=int(os.getenv("REQUEST_TIMEOUT_SECONDS", "20")),
            cache_ttl_seconds=int(os.getenv("CACHE_TTL_SECONDS", "15")),
            default_limit=int(os.getenv("DEFAULT_LIMIT", "500")),
            max_limit=int(os.getenv("MAX_LIMIT", "5000")),
            log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
        )

