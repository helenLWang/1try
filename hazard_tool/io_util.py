"""Workspace JSON checkpoints for the human-in-the-loop pipeline."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
WORKSPACE = ROOT / "workspace"


def load_dotenv() -> None:
    env_path = ROOT / ".env"
    if not env_path.exists():
        return
    try:
        from dotenv import load_dotenv as _load
    except ImportError:
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key, value = key.strip(), value.strip().strip('"').strip("'")
            if key and key not in __import__("os").environ:
                __import__("os").environ[key] = value
        return
    _load(env_path)


def ensure_workspace() -> Path:
    WORKSPACE.mkdir(parents=True, exist_ok=True)
    return WORKSPACE


def read_json(name: str) -> Any:
    path = WORKSPACE / name
    if not path.exists():
        raise FileNotFoundError(
            f"Missing {path}. Run the previous pipeline step, or copy an example from workspace/."
        )
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(name: str, payload: Any) -> Path:
    ensure_workspace()
    path = WORKSPACE / name
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def require_approved(name: str) -> Any:
    payload = read_json(name)
    if isinstance(payload, dict) and not payload.get("approved", False):
        raise SystemExit(
            f"{WORKSPACE / name} is not approved yet.\n"
            f"1. Open the file, edit/delete/add items.\n"
            f"2. Set \"approved\": true (or run: python -m hazard_tool approve {name}).\n"
            f"3. Re-run the next step."
        )
    return payload
