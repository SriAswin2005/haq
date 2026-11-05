"""Config loader. config.yaml is the single place for models, thresholds and keywords."""
import os
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent

try:  # .env is optional
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")
except Exception:  # pragma: no cover
    pass

_cache: dict = {}


def load_config(path: str | None = None, reload: bool = False) -> dict:
    p = Path(path) if path else ROOT / "config.yaml"
    key = str(p)
    if reload or key not in _cache:
        with open(p, encoding="utf-8") as f:
            cfg = yaml.safe_load(f) or {}
        _cache[key] = cfg
    cfg = _cache[key]
    return cfg


def is_mock() -> bool:
    if os.environ.get("AI_LAWYER_MOCK", "").strip() in ("1", "true", "yes"):
        return True
    return bool(load_config().get("mock", False))


def resolve(path_str: str) -> Path:
    p = Path(path_str)
    return p if p.is_absolute() else ROOT / p


def read_prompt(name: str) -> str:
    return (ROOT / "app" / "prompts" / name).read_text(encoding="utf-8")
