"""Validate skills against the agentskills.io specification."""

from __future__ import annotations

import re
from pathlib import Path

import frontmatter

# agentskills.io name rules: 1-64 chars, lowercase alphanumeric + hyphens,
# no leading/trailing hyphens, no consecutive hyphens
SKILL_NAME_PATTERN = re.compile(r"^[a-z0-9]([a-z0-9-]*[a-z0-9])?$")
MAX_NAME_LENGTH = 64
MAX_DESCRIPTION_LENGTH = 1024


def validate_skill_name(name: str) -> str | None:
    """Return error message if name is invalid, None if valid."""
    if not name:
        return "Name is required"
    if len(name) > MAX_NAME_LENGTH:
        return f"Name must be at most {MAX_NAME_LENGTH} characters"
    if "--" in name:
        return "Name must not contain consecutive hyphens"
    if not SKILL_NAME_PATTERN.match(name):
        return "Name must be lowercase alphanumeric with hyphens, not starting/ending with hyphen"
    return None


def validate_skill_dir(skill_dir: Path) -> list[str]:
    """Validate a skill directory. Returns list of errors (empty = valid)."""
    errors: list[str] = []

    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        errors.append(f"Missing SKILL.md in {skill_dir}")
        return errors

    try:
        post = frontmatter.load(str(skill_md))
    except Exception as e:
        errors.append(f"Failed to parse SKILL.md frontmatter: {e}")
        return errors

    name = post.metadata.get("name", "")
    description = post.metadata.get("description", "")

    if not name:
        errors.append("SKILL.md frontmatter missing 'name' field")
    else:
        name_error = validate_skill_name(name)
        if name_error:
            errors.append(f"Invalid skill name '{name}': {name_error}")

        # Name must match directory name
        if name != skill_dir.name:
            errors.append(
                f"Skill name '{name}' does not match directory name '{skill_dir.name}'"
            )

    if not description:
        errors.append("SKILL.md frontmatter missing 'description' field")
    elif len(description) > MAX_DESCRIPTION_LENGTH:
        errors.append(f"Description exceeds {MAX_DESCRIPTION_LENGTH} characters")

    return errors


def parse_skill_metadata(skill_md_path: Path) -> dict:
    """Parse SKILL.md and return metadata (name, description)."""
    post = frontmatter.load(str(skill_md_path))
    return {
        "name": post.metadata.get("name", ""),
        "description": post.metadata.get("description", ""),
        "metadata": dict(post.metadata),
    }
