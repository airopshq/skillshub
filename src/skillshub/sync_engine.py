"""Sync skills from the local repo clone to agent skill directories."""

from __future__ import annotations

import shutil
from pathlib import Path

from .config import get_skills_dir, get_sync_targets


def sync_skills(
    targets: list[str] | None = None,
    skills_dir: Path | None = None,
) -> dict:
    """Sync skills from repo to agent directories.

    Returns a summary: { synced: [...], removed: [...], unchanged: [...] }
    """
    src = skills_dir or get_skills_dir()
    target_dirs = [Path(t).expanduser() for t in (targets or get_sync_targets())]

    if not src.exists():
        return {
            "synced": [],
            "removed": [],
            "unchanged": [],
            "error": "Skills directory not found in repo",
        }

    # Get list of skills in the repo
    repo_skills = {
        d.name for d in src.iterdir() if d.is_dir() and (d / "SKILL.md").exists()
    }

    summary: dict[str, list[str]] = {"synced": [], "removed": [], "unchanged": []}

    for target in target_dirs:
        target.mkdir(parents=True, exist_ok=True)

        # Get list of skills currently in target
        existing_skills = {
            d.name for d in target.iterdir() if d.is_dir() and (d / "SKILL.md").exists()
        }

        # Copy new/updated skills
        for skill_name in repo_skills:
            src_skill = src / skill_name
            dst_skill = target / skill_name

            if _needs_update(src_skill, dst_skill):
                _copy_skill(src_skill, dst_skill)
                if skill_name not in summary["synced"]:
                    summary["synced"].append(skill_name)
            else:
                if skill_name not in summary["unchanged"]:
                    summary["unchanged"].append(skill_name)

        # Remove skills that are no longer in the repo
        # Only remove skills that have a .skillshub marker (to avoid deleting user-created skills)
        for skill_name in existing_skills - repo_skills:
            marker = target / skill_name / ".skillshub"
            if marker.exists():
                shutil.rmtree(target / skill_name)
                if skill_name not in summary["removed"]:
                    summary["removed"].append(skill_name)

    return summary


def sync_single_skill(skill_name: str, skills_dir: Path | None = None) -> None:
    """Sync a single skill from repo to all agent directories."""
    src = (skills_dir or get_skills_dir()) / skill_name
    if not src.exists():
        return

    targets = [Path(t).expanduser() for t in get_sync_targets()]
    for target in targets:
        target.mkdir(parents=True, exist_ok=True)
        _copy_skill(src, target / skill_name)


def _needs_update(src: Path, dst: Path) -> bool:
    """Check if a skill directory needs to be updated by comparing file contents."""
    if not dst.exists():
        return True

    for src_file in src.rglob("*"):
        if src_file.is_file():
            rel = src_file.relative_to(src)
            dst_file = dst / rel
            if not dst_file.exists():
                return True
            # Compare size first (fast), then content if sizes match
            if src_file.stat().st_size != dst_file.stat().st_size:
                return True
            if src_file.read_bytes() != dst_file.read_bytes():
                return True

    return False


def _copy_skill(src: Path, dst: Path) -> None:
    """Copy a skill directory, preserving structure."""
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)

    # Add marker so we know this was managed by skillshub
    (dst / ".skillshub").write_text("")
