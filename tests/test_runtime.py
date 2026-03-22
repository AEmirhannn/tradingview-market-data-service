import unittest
from unittest.mock import patch

from tradingview_service.runtime import configure_runtime_env


class RuntimeTests(unittest.TestCase):
    @patch("tradingview_service.runtime.load_dotenv", autospec=True)
    def test_configure_runtime_env_forces_anonymous_mode_by_default(self, _load_dotenv):
        env = {
            "TRADINGVIEW_USERNAME": "user@example.com",
            "TRADINGVIEW_PASSWORD": "secret",
        }

        configure_runtime_env(env)

        self.assertEqual(env["TRADINGVIEW_USERNAME"], "")
        self.assertEqual(env["TRADINGVIEW_PASSWORD"], "")

    @patch("tradingview_service.runtime.load_dotenv", autospec=True)
    def test_configure_runtime_env_preserves_credentials_when_opted_in(self, _load_dotenv):
        env = {
            "TRADINGVIEW_USE_CREDENTIALS": "1",
            "TRADINGVIEW_USERNAME": "user@example.com",
            "TRADINGVIEW_PASSWORD": "secret",
        }

        configure_runtime_env(env)

        self.assertEqual(env["TRADINGVIEW_USERNAME"], "user@example.com")
        self.assertEqual(env["TRADINGVIEW_PASSWORD"], "secret")


if __name__ == "__main__":
    unittest.main()
