import json
import threading
import time
import urllib.parse
import urllib.request
from typing import Callable, Dict, Optional

from tradingview_service.errors import AuthenticationError


class TradingViewAuthenticator:
    SIGN_IN_URL = "https://www.tradingview.com/accounts/signin/"

    def __init__(
        self,
        username: str,
        password: str,
        *,
        timeout_seconds: int,
        opener: Optional[Callable[..., object]] = None,
    ) -> None:
        self.username = username
        self.password = password
        self.timeout_seconds = timeout_seconds
        self._opener = opener or urllib.request.urlopen
        self._lock = threading.Lock()
        self._token: Optional[str] = None
        self._last_refresh_at: Optional[int] = None
        self._last_error: Optional[str] = None

    def get_token(self, *, force_refresh: bool = False) -> str:
        if not self.username or not self.password:
            return "unauthorized_user_token"

        with self._lock:
            if self._token and not force_refresh:
                return self._token

            payload = urllib.parse.urlencode(
                {
                    "username": self.username,
                    "password": self.password,
                    "remember": "on",
                }
            ).encode("utf-8")
            request = urllib.request.Request(
                self.SIGN_IN_URL,
                data=payload,
                headers={
                    "Referer": "https://www.tradingview.com",
                    "Content-Type": "application/x-www-form-urlencoded",
                },
            )

            try:
                with self._opener(request, timeout=self.timeout_seconds) as response:
                    data = json.loads(response.read().decode("utf-8"))
            except Exception as exc:
                self._last_error = exc.__class__.__name__
                raise AuthenticationError("failed to authenticate with TradingView") from exc

            token = data.get("user", {}).get("auth_token")
            if not token:
                self._last_error = data.get("error") or "missing_auth_token"
                raise AuthenticationError("TradingView login did not return an auth token")

            self._token = token
            self._last_refresh_at = int(time.time())
            self._last_error = None
            return token

    def health(self) -> Dict[str, Optional[str]]:
        if not self.username or not self.password:
            state = "anonymous"
        elif self._token:
            state = "ready"
        elif self._last_error:
            state = "error"
        else:
            state = "configured"

        return {
            "mode": "credentials" if self.username and self.password else "anonymous",
            "state": state,
            "last_refresh_at": self._last_refresh_at,
            "last_error": self._last_error,
        }

