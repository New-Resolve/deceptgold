import json
import os
from functools import lru_cache
from typing import Any, Optional


@lru_cache(maxsize=1)
def _load_generated_module_secrets() -> dict:
    try:
        from deceptgold import _secrets_generated

        data = getattr(_secrets_generated, "SECRETS", None)
        if isinstance(data, dict):
            return data
        return {}
    except Exception:
        return {}


@lru_cache(maxsize=1)
def _load_packaged_secrets() -> dict:
    try:
        from importlib.resources import files

        secrets_path = files("deceptgold.resources").joinpath("secrets.json")
        if not secrets_path.is_file():
            return {}
        data = secrets_path.read_text(encoding="utf-8")
        if not data.strip():
            return {}
        return json.loads(data)
    except Exception:
        return {}


def get_secret(name: str, default: Optional[Any] = None, required: bool = False) -> Any:
    env_name = f"DECEPTGOLD_{name}".upper()

    generated = _load_generated_module_secrets()
    if name in generated and generated[name] not in (None, ""):
        return generated[name]

    if env_name in os.environ:
        value = os.environ.get(env_name)
        if value is not None and value != "":
            return value

    packaged = _load_packaged_secrets()
    if name in packaged and packaged[name] not in (None, ""):
        return packaged[name]

    if required:
        print("ERROR: Missing required secrets module: deceptgold._secrets_generated. "
              "Run: poetry run bootstrap-secrets")
        raise RuntimeError(
            f"Missing required secret '{name}'. Provide '{env_name}' environment variable "
            f"or package a deceptgold/resources/secrets.json with this key."
        )

    return default
