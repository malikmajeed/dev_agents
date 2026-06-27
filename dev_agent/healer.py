"""
Healer v2 — runs tests, collects errors, asks the model to fix them.
Works with mono-repo or separate backend / frontend checkouts.
"""

import subprocess, re, json
from pathlib import Path
from repo_config import RepoLayout
from utils import call_hf, log

HEALER_PROMPT = """You are debugging a Node.js/React application.

Tech stack:
{techstack}

The following errors occurred while implementing sub-task:
Feature: {feature_name}
Sub-task: {subtask_text}

ERROR LOG:
{error_log}

Files currently in the repo (may need fixing):
{file_list}

Output ONLY a raw JSON object of files to CREATE or OVERWRITE to fix these errors:
{{"files": [{{"path": "backend/... or frontend/...", "content": "...complete corrected file..."}}]}}

Fix ALL listed errors. Use backend/ or frontend/ path prefixes. Output complete files, not diffs. No markdown fences.
"""


def _backend_src(layout: RepoLayout) -> Path | None:
    for candidate in (
        layout.backend_root / "src",
        layout.backend_root,
    ):
        if candidate.exists():
            return candidate
    return None


def _frontend_src(layout: RepoLayout) -> Path | None:
    for candidate in (
        layout.frontend_root / "app",
        layout.frontend_root / "src",
        layout.frontend_root,
    ):
        if candidate.exists():
            return candidate
    return None


def run_tests(layout: RepoLayout) -> tuple[bool, str]:
    """Run syntax checks and available tests. Returns (passed, error_log)."""
    errors = []
    workspace = layout.control_root

    backend_src = _backend_src(layout)
    if backend_src:
        for js_file in backend_src.rglob("*.js"):
            if "node_modules" in str(js_file):
                continue
            result = subprocess.run(
                ["node", "--check", str(js_file)],
                capture_output=True, text=True,
            )
            if result.returncode != 0:
                rel = js_file.relative_to(workspace)
                errors.append(f"[Syntax error] {rel}:\n{result.stderr.strip()}")

    backend_pkg = layout.backend_root / "package.json"
    if backend_pkg.exists():
        try:
            pkg = json.loads(backend_pkg.read_text())
            if "test" in pkg.get("scripts", {}):
                result = subprocess.run(
                    ["npm", "test", "--", "--passWithNoTests"],
                    capture_output=True, text=True,
                    cwd=layout.backend_root,
                    timeout=60,
                )
                if result.returncode != 0:
                    out = (result.stdout + result.stderr)[-1500:]
                    errors.append(f"[Backend test failure]\n{out}")
        except Exception as e:
            log(f"Healer: could not run backend tests: {e}")

    frontend_src = _frontend_src(layout)
    if frontend_src:
        for js_file in frontend_src.rglob("*.js"):
            if "node_modules" in str(js_file):
                continue
            result = subprocess.run(
                ["node", "--check", str(js_file)],
                capture_output=True, text=True,
            )
            if result.returncode != 0:
                rel = js_file.relative_to(workspace)
                errors.append(f"[Syntax error] {rel}:\n{result.stderr.strip()}")

    if errors:
        error_log = "\n\n".join(errors)
        log(f"Healer: {len(errors)} error group(s) found")
        return False, error_log

    log("Healer: all checks passed ✓")
    return True, ""


def fix_code(
    feature: dict,
    subtask: dict,
    error_log: str,
    project_context: str,
    techstack: str,
    layout: RepoLayout,
):
    """Ask the model to fix errors and overwrite files."""
    log("Healer: requesting fix from model...")

    all_files = []
    for root in (layout.backend_root, layout.frontend_root, layout.control_root):
        if not root.exists():
            continue
        for ext in ("*.js", "*.jsx", "*.json"):
            for p in root.rglob(ext):
                if ".git" not in str(p) and "node_modules" not in str(p):
                    try:
                        all_files.append(str(p.relative_to(layout.control_root)))
                    except ValueError:
                        all_files.append(str(p))
    file_list = "\n".join(sorted(set(all_files))[:50])

    prompt = HEALER_PROMPT.format(
        techstack=techstack[:800] if techstack else "Node.js + Express + React",
        feature_name=feature["name"],
        subtask_text=subtask["text"],
        error_log=error_log[:2000],
        file_list=file_list,
    )

    response = call_hf(prompt, max_tokens=2500)
    if not response:
        log("Healer: model returned nothing")
        return

    response = re.sub(r"^```(?:json)?\n?", "", response.strip())
    response = re.sub(r"\n?```$", "", response.strip())

    try:
        data  = json.loads(response)
        files = data.get("files", [])
    except json.JSONDecodeError:
        log("Healer: could not parse fix response")
        return

    for file_def in files:
        path_str = file_def.get("path", "").strip().lstrip("/")
        content  = file_def.get("content", "")
        if not path_str or not content:
            continue
        target, _ = layout.resolve_path(path_str)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content)
        log(f"  Fixed: {path_str}")
