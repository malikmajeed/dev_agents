"""
Repository layout — mono-repo or separate backend / frontend GitHub repos.

Configure via GitHub Actions variables (recommended):
  BACKEND_REPOSITORY=org/ngo-backend
  FRONTEND_REPOSITORY=org/ngo-frontend

Or via REPOS.md in the control repo (see template in that file).

Control repo (where DevAgent runs) holds: dev_agent/, PROJECT.md, FEATURES.md, etc.
Backend and frontend are checked out into backend/ and frontend/ subdirectories.
"""

import os, re
from dataclasses import dataclass
from pathlib import Path
from utils import log


def normalize_github_slug(value: str) -> str:
    """Convert owner/repo, URL, or git@github.com:owner/repo.git → owner/repo."""
    v = (value or "").strip()
    if not v:
        return ""
    v = re.sub(r"^https?://github\.com/", "", v)
    v = re.sub(r"^git@github\.com:", "", v)
    v = v.removesuffix(".git").strip("/")
    return v


@dataclass
class RepoLayout:
    control_root: Path
    control_repo: str
    backend_repo: str | None
    frontend_repo: str | None

    @classmethod
    def load(cls, control_root: Path | None = None) -> "RepoLayout":
        root = Path(control_root or os.environ.get("REPO_ROOT", Path(__file__).parent.parent))
        control_repo = os.environ.get("GITHUB_REPOSITORY", "")
        backend_repo = normalize_github_slug(os.environ.get("BACKEND_REPOSITORY", "")) or None
        frontend_repo = normalize_github_slug(os.environ.get("FRONTEND_REPOSITORY", "")) or None

        repos_file = root / "REPOS.md"
        if repos_file.exists():
            b, f = _parse_repos_md(repos_file.read_text())
            backend_repo = backend_repo or normalize_github_slug(b or "")
            frontend_repo = frontend_repo or normalize_github_slug(f or "")
        backend_repo = backend_repo or None
        frontend_repo = frontend_repo or None

        layout = cls(root, control_repo, backend_repo, frontend_repo)
        if layout.dual_repo:
            log(f"Layout: dual-repo — backend={backend_repo}, frontend={frontend_repo}")
        else:
            log(f"Layout: mono-repo — {control_repo or root}")
        return layout

    @property
    def dual_repo(self) -> bool:
        return bool(self.backend_repo and self.frontend_repo)

    @property
    def backend_root(self) -> Path:
        return self.control_root / "backend"

    @property
    def frontend_root(self) -> Path:
        return self.control_root / "frontend"

    def github_repo(self, target: str) -> str:
        if target == "backend":
            return self.backend_repo or self.control_repo
        if target == "frontend":
            return self.frontend_repo or self.control_repo
        return self.control_repo

    def git_root(self, target: str) -> Path:
        if self.dual_repo:
            if target == "backend":
                return self.backend_root
            if target == "frontend":
                return self.frontend_root
        return self.control_root

    def active_git_targets(self) -> list[str]:
        if self.dual_repo:
            return ["backend", "frontend"]
        return ["control"]

    def resolve_path(self, path_str: str) -> tuple[Path, str]:
        """
        Map a logical file path to (absolute_path, git_target).
        Paths use backend/ or frontend/ prefix (mono or dual mode).
        """
        path_str = path_str.strip().lstrip("/")
        if path_str.startswith("backend/"):
            rel = path_str[len("backend/"):]
            if self.dual_repo:
                return self.backend_root / rel, "backend"
            return self.control_root / path_str, "control"
        if path_str.startswith("frontend/"):
            rel = path_str[len("frontend/"):]
            if self.dual_repo:
                return self.frontend_root / rel, "frontend"
            return self.control_root / path_str, "control"
        return self.control_root / path_str, "control"

    def targets_for_paths(self, paths: list[str]) -> list[str]:
        targets: set[str] = set()
        for p in paths:
            _, t = self.resolve_path(p)
            targets.add(t)
        return sorted(targets)

    def targets_for_subtask(self, subtask_text: str) -> list[str]:
        t = subtask_text.lower()
        if not self.dual_repo:
            return ["control"]
        if any(w in t for w in ("wiring", "integration", "connect")):
            return ["backend", "frontend"]
        if any(w in t for w in ("backend", "model", "schema", "sequelize", "mongoose")):
            return ["backend"]
        if any(w in t for w in ("api", "route", "endpoint", "controller", "middleware")):
            return ["backend"]
        if any(w in t for w in ("frontend", "component", "page", "ui", "next.js", "nextjs")):
            return ["frontend"]
        return ["backend", "frontend"]

    def repo_label(self, target: str) -> str:
        slug = self.github_repo(target)
        return slug.split("/")[-1] if slug else target


def _parse_repos_md(content: str) -> tuple[str | None, str | None]:
    backend = frontend = None
    for line in content.splitlines():
        m = re.search(r"backend\s*\|\s*([^\s|]+/[^\s|]+)", line, re.I)
        if m:
            backend = m.group(1).strip()
        m = re.search(r"frontend\s*\|\s*([^\s|]+/[^\s|]+)", line, re.I)
        if m:
            frontend = m.group(1).strip()
        if re.match(r"^\s*BACKEND_REPOSITORY\s*=\s*(\S+)", line, re.I):
            backend = line.split("=", 1)[1].strip()
        if re.match(r"^\s*FRONTEND_REPOSITORY\s*=\s*(\S+)", line, re.I):
            frontend = line.split("=", 1)[1].strip()
    return backend, frontend
