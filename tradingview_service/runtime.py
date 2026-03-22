import os
from typing import MutableMapping, Optional

from tradingview_service.dotenv import load_dotenv


TRUTHY_VALUES = {"1", "true", "yes", "on"}


def configure_runtime_env(env: Optional[MutableMapping[str, str]] = None) -> None:
    runtime_env = env if env is not None else os.environ
    load_dotenv()

    if _use_tradingview_credentials(runtime_env):
        return

    runtime_env["TRADINGVIEW_USERNAME"] = ""
    runtime_env["TRADINGVIEW_PASSWORD"] = ""


def _use_tradingview_credentials(env: MutableMapping[str, str]) -> bool:
    value = env.get("TRADINGVIEW_USE_CREDENTIALS", "")
    return value.strip().lower() in TRUTHY_VALUES
