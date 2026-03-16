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


def get_skills_paths() -> list[str]:
    """Return the list of skills/ paths within the repo to scan.

    If empty or not set, auto-discovers all directories containing skills/*/SKILL.md.
    """
    config = load_config()
    return config.get("skills_paths", [])


def get_skills_dirs() -> list[Path]:
    """Return resolved paths to all skills directories to scan.

    If skills_paths is configured, uses those. Otherwise auto-discovers
    by scanning the repo for any directory pattern: */skills/*/SKILL.md
    """
    repo = get_repo_path()
    configured = get_skills_paths()

    if configured:
        return [repo / p for p in configured]

    # Auto-discover: scan for */skills/ directories containing skill subdirs
    # Also check repo root skills/ for backward compat
    found = []
    root_skills = repo / "skills"
    if root_skills.is_dir() and _has_skills(root_skills):
        found.append(root_skills)

    for child in sorted(repo.iterdir()):
        if child.is_dir() and not child.name.startswith("."):
            skills_subdir = child / "skills"
            if skills_subdir.is_dir() and _has_skills(skills_subdir):
                found.append(skills_subdir)

    return found if found else [root_skills]


def _has_skills(skills_dir: Path) -> bool:
    """Check if a directory contains at least one skill (subdir with SKILL.md)."""
    try:
        return any(
            (d / "SKILL.md").exists() for d in skills_dir.iterdir() if d.is_dir()
        )
    except OSError:
        return False
