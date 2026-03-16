"""Git repository operations for SkillsHub."""

from __future__ import annotations

from pathlib import Path

from git import Repo, InvalidGitRepositoryError, GitCommandError

from .config import get_repo_path, get_skills_dirs


def clone_repo(url: str, path: Path | None = None) -> Repo:
    """Clone a git repository to the given path."""
    target = path or get_repo_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    return Repo.clone_from(url, str(target))


def open_repo(path: Path | None = None) -> Repo:
    """Open an existing git repository."""
    target = path or get_repo_path()
    try:
        return Repo(str(target))
    except InvalidGitRepositoryError:
        raise RuntimeError(
            f"No skillshub repo found at {target}. Run 'skillshub init <github-url>' first."
        )


def pull(repo: Repo | None = None) -> str:
    """Pull latest changes from remote. Returns pull output."""
    r = repo or open_repo()
    try:
        return r.git.pull()
    except GitCommandError as e:
        raise RuntimeError(f"Git pull failed: {e}")


def commit_and_push(
    paths: list[str],
    message: str,
    repo: Repo | None = None,
) -> str:
    """Stage paths, commit with message, and push. Returns commit SHA."""
    r = repo or open_repo()

    # Stage the specified paths
    r.index.add(paths)

    # Stage deletions scoped to the specified paths only
    deleted = [
        item.a_path
        for item in r.index.diff(None)
        if item.deleted_file and any(item.a_path.startswith(p) for p in paths)
    ]
    if deleted:
        r.index.remove(deleted, working_tree=True)

    # Check if there's anything to commit
    if not r.index.diff("HEAD"):
        return "no-changes"

    commit = r.index.commit(message)

    try:
        r.remotes.origin.push()
    except GitCommandError as e:
        raise RuntimeError(
            f"Git push failed: {e}. Commit {commit.hexsha[:8]} is local only."
        )

    return commit.hexsha


def list_skills() -> list[dict]:
    """List all skills across all configured skills directories."""
    from .validation import parse_skill_metadata

    results = []
    seen = set()

    for skills_dir in get_skills_dirs():
        if not skills_dir.exists():
            continue
        for skill_dir in sorted(skills_dir.iterdir()):
            if not skill_dir.is_dir():
                continue
            skill_md = skill_dir / "SKILL.md"
            if not skill_md.exists():
                continue
            try:
                meta = parse_skill_metadata(skill_md)
                name = meta["name"] or skill_dir.name
                if name in seen:
                    continue
                seen.add(name)
                results.append(
                    {
                        "name": name,
                        "description": meta["description"],
                        "path": str(skill_dir),
                    }
                )
            except Exception:
                name = skill_dir.name
                if name in seen:
                    continue
                seen.add(name)
                results.append(
                    {
                        "name": name,
                        "description": "(failed to parse)",
                        "path": str(skill_dir),
                    }
                )

    return results


def find_skill_dir(skill_name: str) -> Path | None:
    """Find a skill directory by name across all skills paths."""
    for skills_dir in get_skills_dirs():
        candidate = skills_dir / skill_name
        if candidate.is_dir() and (candidate / "SKILL.md").exists():
            return candidate
    return None


def find_skill_repo_path(skill_name: str) -> str | None:
    """Find a skill's repo-relative path (for git operations)."""
    repo = get_repo_path()
    skill_dir = find_skill_dir(skill_name)
    if skill_dir is None:
        return None
    return str(skill_dir.relative_to(repo))


def get_default_skills_dir() -> Path:
    """Return the first configured skills dir (for creating new skills)."""
    dirs = get_skills_dirs()
    return dirs[0] if dirs else get_repo_path() / "skills"


def get_skill_log(skill_name: str, max_count: int = 20) -> list[dict]:
    """Get git log for a specific skill."""
    r = open_repo()
    skill_path = find_skill_repo_path(skill_name)
    if not skill_path:
        return []

    commits = []
    for commit in r.iter_commits(paths=skill_path, max_count=max_count):
        commits.append(
            {
                "sha": commit.hexsha[:8],
                "message": commit.message.strip(),
                "author": str(commit.author),
                "date": commit.committed_datetime.isoformat(),
            }
        )

    return commits


def get_skill_diff(skill_name: str, ref1: str = "HEAD~1", ref2: str = "HEAD") -> str:
    """Get diff for a skill between two refs."""
    r = open_repo()
    skill_path = find_skill_repo_path(skill_name) or f"skills/{skill_name}"
    return r.git.diff(ref1, ref2, "--", skill_path)


def rollback_skill(skill_name: str, ref: str) -> str:
    """Restore a skill to a previous version and commit."""
    r = open_repo()
    skill_path = find_skill_repo_path(skill_name) or f"skills/{skill_name}"

    r.git.checkout(ref, "--", skill_path)

    return commit_and_push(
        [skill_path],
        f"Rollback {skill_name} to {ref}",
        r,
    )
