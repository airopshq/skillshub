"""Configuration management for SkillsHub CLI."""

from __future__ import annotations

import json
from pathlib import Path

CONFIG_DIR = Path.home() / ".skillshub"
CONFIG_FILE = CONFIG_DIR / "config.json"

DEFAULT_SYNC_TARGETS = [
    str(Path.home() / ".agents" / "skills"),
    str(Path.home() / ".claude" / "skills"),
]


def load_config() -> dict:
    if not CONFIG_FILE.exists():
        return {}
    return json.loads(CONFIG_FILE.read_text())


def save_config(config: dict) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(config, indent=2) + "\n")


def get_repo_path() -> Path:
    config = load_config()
    return Path(config.get("repo_path", str(CONFIG_DIR / "repo"))).expanduser()


def get_repo_url() -> str | None:
    return load_config().get("repo_url")


def get_sync_targets() -> list[str]:
    config = load_config()
    return config.get("sync_targets", DEFAULT_SYNC_TARGETS)


def get_skills_dir() -> Path:
    """Return the path to the skills/ directory inside the local repo clone."""
    return get_repo_path() / "skills"
