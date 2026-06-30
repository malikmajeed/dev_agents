"""
Repository layout — Next.js mono-repo at control root.

The control repo holds dev_agent/, FEATURES.md, and the Next.js app (app/, models/, lib/, etc.).
"""

import os
from dataclasses import dataclass
from pathlib import Path
from utils import log

APP_PREFIXES = ("app/", "models/", "lib/", "components/", "hooks/", "services/")


@dataclass
class RepoLayout:
    control_root: Path
    control_repo: str

    @classmethod
    def load(cls, control_root: Path | None = None) -> "RepoLayout":
        root = Path(control_root or os.environ.get("REPO_ROOT", Path(__file__).parent.parent))
        control_repo = os.environ.get("GITHUB_REPOSITORY", "")
        layout = cls(root, control_repo)
        log(f"Layout: Next.js mono-repo — {control_repo or root}")
        return layout

    @property
    def app_root(self) -> Path:
        return self.control_root

    def github_repo(self, target: str = "control") -> str:
        return self.control_repo

    def git_root(self, target: str = "control") -> Path:
        return self.control_root

    def active_git_targets(self) -> list[str]:
        return ["control"]

    def resolve_path(self, path_str: str) -> tuple[Path, str]:
        """Map a logical file path to (absolute_path, git_target)."""
        path_str = path_str.strip().lstrip("/")
        return self.control_root / path_str, "control"

    def targets_for_paths(self, paths: list[str]) -> list[str]:
        return ["control"]

    def targets_for_subtask(self, subtask_text: str) -> list[str]:
        return ["control"]

    def repo_label(self, target: str = "control") -> str:
        slug = self.control_repo
        return slug.split("/")[-1] if slug else "repo"

    def app_source_dirs(self) -> list[Path]:
        """Directories scanned for syntax checks and healer context."""
        dirs = []
        for name in ("app", "models", "lib", "components", "hooks", "services"):
            p = self.control_root / name
            if p.exists():
                dirs.append(p)
        return dirs
