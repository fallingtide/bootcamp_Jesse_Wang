"""Configuration helpers for loading secrets and settings from a .env file."""

import os
from typing import Optional

from dotenv import load_dotenv


def load_env(dotenv_path: str = ".env") -> None:
    """Load environment variables from a ``.env`` file into ``os.environ``."""
    load_dotenv(dotenv_path=dotenv_path)


def get_key(name: str) -> Optional[str]:
    """Return the value of the environment variable ``name``, or ``None`` if unset."""
    return os.getenv(name)
