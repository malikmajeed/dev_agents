"""
GitHub PR Manager — Next.js mono-repo: feature branches → auto-merge to main.
"""

import os, subprocess, time, requests
from pathlib import Path
from repo_config import RepoLayout
from utils import log

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
API_BASE     = "https://api.github.com"
DEFAULT_BASE = "main"

BASE_HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}


def _api(method: str, github_repo: str, path: str, **kwargs) -> dict | list | None:
    if not GITHUB_TOKEN or not github_repo:
        return None
    url = f"{API_BASE}/repos/{github_repo}{path}"
    resp = requests.request(method, url, headers=BASE_HEADERS, **kwargs)
    if resp.status_code in (200, 201, 204):
        return resp.json() if resp.content else {}
    log(f"GitHub API {method} {github_repo}{path} → {resp.status_code}: {resp.text[:200]}")
    return None


def slugify(name: str) -> str:
    import re
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


# ── Git helpers ────────────────────────────────────────────────────────────────

def _git_env() -> dict:
    return {
        **os.environ,
        "GIT_AUTHOR_NAME":  "DevAgent",
        "GIT_AUTHOR_EMAIL": "dev-agent@noreply.local",
        "GIT_COMMITTER_NAME":  "DevAgent",
        "GIT_COMMITTER_EMAIL": "dev-agent@noreply.local",
    }


def git(cmd: list[str], cwd: Path, check=True):
    subprocess.run(
        ["git"] + cmd, cwd=cwd, check=check, env=_git_env(),
    )


def _current_branch(repo_root: Path) -> str:
    result = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        cwd=repo_root, capture_output=True, text=True, env=_git_env(),
    )
    return result.stdout.strip() or DEFAULT_BASE


def _is_dirty(repo_root: Path) -> bool:
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=repo_root, capture_output=True, text=True, env=_git_env(),
    )
    return bool(result.stdout.strip())


def _stash_if_dirty(repo_root: Path) -> bool:
    if not _is_dirty(repo_root):
        return False
    git(["stash", "push", "-u", "-m", "devagent-autostash"], repo_root)
    return True


def _stash_pop(repo_root: Path) -> None:
    subprocess.run(
        ["git", "stash", "pop"], cwd=repo_root, env=_git_env(), check=False,
    )


def _remote_branch_exists(repo_root: Path, branch: str) -> bool:
    result = subprocess.run(
        ["git", "show-ref", "--verify", f"refs/remotes/origin/{branch}"],
        cwd=repo_root, capture_output=True, env=_git_env(),
    )
    return result.returncode == 0


def _sync_with_remote(repo_root: Path, hard_reset: bool = False) -> bool:
    """Fetch and rebase current branch onto origin. Returns False on conflict."""
    branch = _current_branch(repo_root)
    git(["fetch", "origin"], repo_root)

    if hard_reset:
        if not _remote_branch_exists(repo_root, branch):
            log(f"PR: no origin/{branch} yet — skip hard reset")
            return True
        git(["reset", "--hard", f"origin/{branch}"], repo_root)
        subprocess.run(
            ["git", "clean", "-fd"], cwd=repo_root, env=_git_env(), check=False,
        )
        log(f"PR: reset '{branch}' to origin/{branch}")
        return True

    if _is_dirty(repo_root):
        return True

    if not _remote_branch_exists(repo_root, branch):
        return True

    result = subprocess.run(
        ["git", "rebase", f"origin/{branch}"],
        cwd=repo_root, capture_output=True, text=True, env=_git_env(),
    )
    if result.returncode == 0:
        return True
    log(f"PR: rebase failed on '{branch}' — {result.stderr.strip()[:200]}")
    subprocess.run(
        ["git", "rebase", "--abort"], cwd=repo_root, env=_git_env(), check=False,
    )
    return False


def _push(repo_root: Path, label: str = "", retries: int = 4) -> bool:
    """Rebase then push. Retries on non-fast-forward races."""
    for attempt in range(1, retries + 1):
        if not _sync_with_remote(repo_root):
            time.sleep(2 * attempt)
            continue
        branch = _current_branch(repo_root)
        result = subprocess.run(
            ["git", "push", "-u", "origin", branch],
            cwd=repo_root, capture_output=True, text=True, env=_git_env(),
        )
        if result.returncode == 0:
            return True
        err = (result.stderr or result.stdout or "").strip()
        log(f"PR [{label}]: push attempt {attempt}/{retries} failed — {err[:200]}")
        time.sleep(2 * attempt)
    return False


def sync_repo(repo_root: Path) -> bool:
    """Sync repo with remote at start of a run."""
    if not _has_git(repo_root):
        return True
    return _sync_with_remote(repo_root, hard_reset=True)


def _has_git(repo_root: Path) -> bool:
    return (repo_root / ".git").exists()


def ensure_branch(branch: str, base: str, layout: RepoLayout):
    """Create branch from base if it doesn't exist, else switch."""
    repo_root = layout.git_root()
    if not _has_git(repo_root):
        log(f"PR: skip branch '{branch}' — no git repo at {repo_root}")
        return

    stashed = _stash_if_dirty(repo_root)
    try:
        result = subprocess.run(
            ["git", "ls-remote", "--heads", "origin", branch],
            cwd=repo_root, capture_output=True, text=True,
        )
        if branch in result.stdout:
            git(["fetch", "origin", branch], repo_root)
            git(["checkout", branch], repo_root)
            _sync_with_remote(repo_root)
            git(["branch", "--set-upstream-to", f"origin/{branch}"], repo_root, check=False)
            log(f"PR: switched to '{branch}'")
        else:
            git(["fetch", "origin", base], repo_root)
            git(["checkout", "-b", branch, f"origin/{base}"], repo_root)
            log(f"PR: created '{branch}' from '{base}'")
    finally:
        if stashed:
            _stash_pop(repo_root)


def ensure_feature_branch(branch: str, layout: RepoLayout):
    ensure_branch(branch, DEFAULT_BASE, layout)


def _commit_one(message: str, layout: RepoLayout) -> bool:
    repo_root = layout.git_root()
    if not _has_git(repo_root):
        return False

    label = layout.repo_label()
    git(["config", "user.email", "dev-agent@noreply.local"], repo_root)
    git(["config", "user.name", "DevAgent"], repo_root)

    git(["add", "-A"], repo_root)
    result = subprocess.run(
        ["git", "diff", "--cached", "--quiet"], cwd=repo_root,
    )
    if result.returncode == 0:
        log(f"PR [{label}]: nothing to commit")
        return True

    git(["commit", "-m", message], repo_root)
    if not _push(repo_root, label):
        log(f"PR [{label}]: commit created locally but push failed — '{message}'")
        return False
    log(f"PR [{label}]: committed '{message}'")
    return True


def commit_control(message: str, layout: RepoLayout) -> bool:
    """Commit FEATURES.md, PROGRESS.md, app code, etc."""
    return _commit_one(message, layout)


def commit_subtask(
    message: str,
    layout: RepoLayout,
    targets: list[str] | None = None,
) -> bool:
    return _commit_one(message, layout)


def _branch_on_remote(branch: str, repo_root: Path) -> bool:
    result = subprocess.run(
        ["git", "ls-remote", "--heads", "origin", branch],
        cwd=repo_root, capture_output=True, text=True,
    )
    return f"refs/heads/{branch}" in result.stdout or branch in result.stdout


def push_feature_branch(branch: str, layout: RepoLayout) -> bool:
    """Ensure feature branch exists locally and is pushed to origin."""
    repo_root = layout.git_root()
    if not _has_git(repo_root):
        return False
    ensure_branch(branch, DEFAULT_BASE, layout)

    if not _branch_on_remote(branch, repo_root):
        return _push(repo_root, layout.repo_label())

    ahead = subprocess.run(
        ["git", "rev-list", "--count", f"origin/{branch}..HEAD"],
        cwd=repo_root, capture_output=True, text=True, env=_git_env(),
    )
    if ahead.returncode != 0:
        return _push(repo_root, layout.repo_label())
    try:
        commits_ahead = int((ahead.stdout or "0").strip())
    except ValueError:
        commits_ahead = 1

    if commits_ahead == 0:
        return True
    return _push(repo_root, layout.repo_label())


# ── PR lifecycle ─────────────────────────────────────────────────────────────

def open_pr(
    feature_name: str,
    branch: str,
    layout: RepoLayout,
    base: str = DEFAULT_BASE,
) -> dict | None:
    github_repo = layout.github_repo()
    body = (
        f"## {feature_name}\n\n"
        f"Auto-generated by DevAgent.\n\n"
        f"**Branch:** `{branch}` → `{base}`\n\n"
        f"Will be auto-merged."
    )
    data = _api("POST", github_repo, "/pulls", json={
        "title": f"feat: {feature_name}",
        "head":  branch,
        "base":  base,
        "body":  body,
    })
    if data:
        log(f"PR: opened #{data.get('number')} → {data.get('html_url', '')}")
        return data
    return None


def get_open_pr(
    branch: str,
    layout: RepoLayout,
    base: str = DEFAULT_BASE,
) -> dict | None:
    github_repo = layout.github_repo()
    owner = github_repo.split("/")[0]
    data = _api(
        "GET", github_repo,
        f"/pulls?head={owner}:{branch}&base={base}&state=open",
    )
    if data and isinstance(data, list) and data:
        return data[0]
    return None


def merge_pr(pr_number: int, feature_name: str, layout: RepoLayout) -> bool:
    github_repo = layout.github_repo()
    data = _api("PUT", github_repo, f"/pulls/{pr_number}/merge", json={
        "commit_title":   f"feat: {feature_name}",
        "commit_message": "Auto-merged by DevAgent",
        "merge_method":   "squash",
    })
    if data:
        log(f"PR: merged #{pr_number}")
        return True
    return False


def auto_merge_feature_pr(
    feature_name: str,
    branch: str,
    layout: RepoLayout,
) -> dict | None:
    """
    Push feature branch, open PR to main if needed, merge immediately.
    Returns {url, number} on success, None on failure.
    """
    repo_root = layout.git_root()
    if not push_feature_branch(branch, layout):
        log(f"PR: failed to push '{branch}'")
        return None

    if not _branch_on_remote(branch, repo_root):
        log(f"PR: '{branch}' not on origin after push")
        return None

    pr = get_open_pr(branch, layout)
    if not pr:
        pr = open_pr(feature_name, branch, layout)
        if not pr:
            pr = get_open_pr(branch, layout)

    if not pr:
        log(f"PR: could not open PR for '{branch}'")
        return None

    pr_number = pr.get("number")
    if pr_number and merge_pr(int(pr_number), feature_name, layout):
        git(["fetch", "origin", DEFAULT_BASE], repo_root)
        git(["checkout", DEFAULT_BASE], repo_root)
        _sync_with_remote(repo_root)
        return {"url": pr.get("html_url", ""), "number": pr_number}

    log(f"PR: merge failed for #{pr_number}")
    return None
