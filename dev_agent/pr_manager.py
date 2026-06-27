"""
GitHub PR Manager — mono-repo or separate backend / frontend repositories.
"""

import os, subprocess, time, requests
from pathlib import Path
from repo_config import RepoLayout
from utils import log

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
API_BASE     = "https://api.github.com"

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
    return result.stdout.strip() or "main"


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


def _sync_with_remote(repo_root: Path, hard_reset: bool = False) -> bool:
    """Fetch and rebase current branch onto origin. Returns False on conflict."""
    branch = _current_branch(repo_root)
    git(["fetch", "origin"], repo_root)

    if hard_reset:
        git(["reset", "--hard", f"origin/{branch}"], repo_root)
        subprocess.run(
            ["git", "clean", "-fd"], cwd=repo_root, env=_git_env(), check=False,
        )
        log(f"PR: reset '{branch}' to origin/{branch}")
        return True

    if _is_dirty(repo_root):
        # Caller has uncommitted work — do not pull/rebase over it
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
    """Pull --rebase then push. Retries on non-fast-forward races."""
    branch = _current_branch(repo_root)
    for attempt in range(1, retries + 1):
        if not _sync_with_remote(repo_root):
            time.sleep(2 * attempt)
            continue
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
    """Public: sync repo with remote at start of a run."""
    if not _has_git(repo_root):
        return True
    return _sync_with_remote(repo_root, hard_reset=True)


def _has_git(repo_root: Path) -> bool:
    return (repo_root / ".git").exists()


def ensure_branch(branch: str, base: str, layout: RepoLayout, target: str):
    """Create branch from base if it doesn't exist, else switch."""
    repo_root = layout.git_root(target)
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
            log(f"PR [{target}]: switched to '{branch}'")
        else:
            git(["fetch", "origin", base], repo_root)
            git(["checkout", "-b", branch, f"origin/{base}"], repo_root)
            log(f"PR [{target}]: created '{branch}' from '{base}'")
    finally:
        if stashed:
            _stash_pop(repo_root)


def ensure_feature_branches(branch: str, layout: RepoLayout):
    for target in layout.active_git_targets():
        ensure_staging(layout, target)
        ensure_branch(branch, "staging", layout, target)


def ensure_staging(layout: RepoLayout, target: str):
    """Make sure staging branch exists in the target repo."""
    repo_root = layout.git_root(target)
    if not _has_git(repo_root):
        return

    result = subprocess.run(
        ["git", "ls-remote", "--heads", "origin", "staging"],
        cwd=repo_root, capture_output=True, text=True,
    )
    if "staging" not in result.stdout:
        git(["fetch", "origin", "main"], repo_root)
        git(["checkout", "-b", "staging", "origin/main"], repo_root)
        if not _push(repo_root, target):
            log(f"PR [{target}]: failed to push new staging branch")
        else:
            log(f"PR [{target}]: created staging from main")


def ensure_all_staging(layout: RepoLayout):
    if layout.dual_repo:
        for target in layout.active_git_targets():
            ensure_staging(layout, target)
    else:
        ensure_staging(layout, "control")


def _commit_one(message: str, layout: RepoLayout, target: str) -> bool:
    repo_root = layout.git_root(target)
    if not _has_git(repo_root):
        return False

    label = layout.repo_label(target)
    git(["config", "user.email", "dev-agent@noreply.local"], repo_root)
    git(["config", "user.name", "DevAgent"], repo_root)

    git(["add", "-A"], repo_root)
    result = subprocess.run(
        ["git", "diff", "--cached", "--quiet"], cwd=repo_root,
    )
    if result.returncode == 0:
        return False

    git(["commit", "-m", message], repo_root)
    if not _push(repo_root, label):
        log(f"PR [{label}]: commit created locally but push failed — '{message}'")
        return False
    log(f"PR [{label}]: committed '{message}'")
    return True


def commit_control(message: str, layout: RepoLayout) -> bool:
    """Commit only to the control repo (FEATURES.md, PROGRESS.md, etc.)."""
    return _commit_one(message, layout, "control")


def commit_subtask(
    message: str,
    layout: RepoLayout,
    targets: list[str] | None = None,
) -> bool:
    """
    Commit to one or more repos. In dual-repo mode, targets backend/frontend.
    In mono-repo mode, commits to control only.
    """
    if layout.dual_repo:
        commit_targets = targets or layout.active_git_targets()
    else:
        commit_targets = ["control"]

    committed = False
    for target in commit_targets:
        if _commit_one(message, layout, target):
            committed = True
    if not committed:
        log("PR: nothing to commit in any repo")
    return committed


def _branch_on_remote(branch: str, repo_root: Path) -> bool:
    result = subprocess.run(
        ["git", "ls-remote", "--heads", "origin", branch],
        cwd=repo_root, capture_output=True, text=True,
    )
    return f"refs/heads/{branch}" in result.stdout or branch in result.stdout


def push_feature_branch(branch: str, layout: RepoLayout, target: str) -> bool:
    """Ensure feature branch exists locally and is pushed to origin."""
    repo_root = layout.git_root(target)
    if not _has_git(repo_root):
        return False
    ensure_branch(branch, "staging", layout, target)

    if not _branch_on_remote(branch, repo_root):
        return _push(repo_root, layout.repo_label(target))

    ahead = subprocess.run(
        ["git", "rev-list", "--count", f"origin/{branch}..HEAD"],
        cwd=repo_root, capture_output=True, text=True, env=_git_env(),
    )
    if ahead.returncode != 0:
        return _push(repo_root, layout.repo_label(target))
    try:
        commits_ahead = int((ahead.stdout or "0").strip())
    except ValueError:
        commits_ahead = 1

    if commits_ahead == 0:
        return True
    return _push(repo_root, layout.repo_label(target))


def push_all_feature_branches(branch: str, layout: RepoLayout) -> dict[str, bool]:
    """Push feature branch on every active repo. Returns {target: ok}."""
    results: dict[str, bool] = {}
    for target in layout.active_git_targets():
        ok = push_feature_branch(branch, layout, target)
        results[target] = ok
        if not ok:
            log(f"PR [{target}]: failed to push '{branch}'")
    return results


# ── PR lifecycle ─────────────────────────────────────────────────────────────

def open_pr(
    feature_name: str,
    branch: str,
    layout: RepoLayout,
    target: str,
    base: str = "staging",
) -> str | None:
    github_repo = layout.github_repo(target)
    body = (
        f"## {feature_name}\n\n"
        f"Auto-generated by DevAgent.\n\n"
        f"**Repo:** `{github_repo}`\n"
        f"**Branch:** `{branch}` → `{base}`\n\n"
        f"Reply `OK` to the notification email to merge, or merge manually here."
    )
    data = _api("POST", github_repo, "/pulls", json={
        "title": f"feat: {feature_name}",
        "head":  branch,
        "base":  base,
        "body":  body,
    })
    if data:
        url = data.get("html_url", "")
        log(f"PR [{target}]: opened #{data.get('number')} → {url}")
        return url
    return None


def get_open_pr(
    branch: str,
    layout: RepoLayout,
    target: str,
    base: str = "staging",
) -> dict | None:
    github_repo = layout.github_repo(target)
    owner = github_repo.split("/")[0]
    data = _api(
        "GET", github_repo,
        f"/pulls?head={owner}:{branch}&base={base}&state=open",
    )
    if data and isinstance(data, list) and data:
        return data[0]
    return None


def open_feature_prs(
    feature_name: str,
    branch: str,
    layout: RepoLayout,
) -> dict[str, dict]:
    """Open PRs on every active repo for this feature. Returns {target: {url, number}}."""
    push_results = push_all_feature_branches(branch, layout)
    prs: dict[str, dict] = {}
    for target in layout.active_git_targets():
        if not push_results.get(target):
            log(f"PR [{target}]: skip open — '{branch}' not on remote")
            continue
        repo_root = layout.git_root(target)
        if not _branch_on_remote(branch, repo_root):
            log(f"PR [{target}]: skip open — '{branch}' missing on origin")
            continue
        existing = get_open_pr(branch, layout, target)
        if existing:
            prs[target] = {
                "url":    existing["html_url"],
                "number": existing["number"],
            }
            continue
        url = open_pr(feature_name, branch, layout, target)
        pr = get_open_pr(branch, layout, target)
        if pr:
            prs[target] = {"url": pr["html_url"], "number": pr["number"]}
        elif url:
            prs[target] = {"url": url, "number": None}
        else:
            log(f"PR [{target}]: failed to open PR for '{branch}'")
    return prs


def merge_pr(pr_number: int, feature_name: str, layout: RepoLayout, target: str) -> bool:
    github_repo = layout.github_repo(target)
    data = _api("PUT", github_repo, f"/pulls/{pr_number}/merge", json={
        "commit_title":   f"feat: {feature_name}",
        "commit_message": "Auto-merged by DevAgent",
        "merge_method":   "squash",
    })
    if data:
        log(f"PR [{target}]: merged #{pr_number}")
        return True
    return False


def merge_feature_prs(pr_numbers: dict, feature_name: str, layout: RepoLayout):
    for target, num in pr_numbers.items():
        if num:
            merge_pr(int(num), feature_name, layout, target)


def open_staging_to_main_pr(
    done_count: int,
    total: int,
    layout: RepoLayout,
    target: str,
) -> str | None:
    github_repo = layout.github_repo(target)
    existing = get_open_pr("staging", layout, target, base="main")
    if existing:
        return existing.get("html_url")

    data = _api("POST", github_repo, "/pulls", json={
        "title": f"🚀 Release: all {total} features complete",
        "head":  "staging",
        "base":  "main",
        "body":  (
            f"## Production Release — {github_repo}\n\n"
            f"All {done_count}/{total} features merged to staging.\n\n"
            f"Review staging preview before merging to production."
        ),
    })
    if data:
        url = data.get("html_url", "")
        log(f"PR [{target}]: staging→main #{data.get('number')} → {url}")
        return url
    return None


def open_release_prs(done_count: int, total: int, layout: RepoLayout) -> dict[str, str]:
    """Open staging→main PRs on all active repos."""
    urls: dict[str, str] = {}
    for target in layout.active_git_targets():
        url = open_staging_to_main_pr(done_count, total, layout, target)
        if url:
            urls[target] = url
    return urls
