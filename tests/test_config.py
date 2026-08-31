import importlib
import os
import sys
import types
import unittest


class ConfigTests(unittest.TestCase):
    def test_uses_configured_service_endpoints(self):
        previous = {
            key: os.environ.get(key)
            for key in (
                "GITHUB_TOKEN",
                "INFERENCE_TOKEN",
                "GITHUB_API_URL",
                "INFERENCE_URL",
            )
        }
        dotenv_module = sys.modules.get("dotenv")
        try:
            sys.modules["dotenv"] = types.SimpleNamespace(load_dotenv=lambda: None)
            os.environ.update(
                {
                    "GITHUB_TOKEN": "test-github-token",
                    "INFERENCE_TOKEN": "test-inference-token",
                    "GITHUB_API_URL": "https://github.example.test/api/v3",
                    "INFERENCE_URL": "https://inference.example.test/v1/chat/completions",
                }
            )

            config = importlib.import_module("app.core.config")
            config = importlib.reload(config)

            self.assertEqual(config.GITHUB_API, os.environ["GITHUB_API_URL"])
            self.assertEqual(config.INFERENCE_URL, os.environ["INFERENCE_URL"])
        finally:
            if dotenv_module is None:
                sys.modules.pop("dotenv", None)
            else:
                sys.modules["dotenv"] = dotenv_module
            for key, value in previous.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value


if __name__ == "__main__":
    unittest.main()
