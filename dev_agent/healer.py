"""
Healer — runs syntax checks, collects errors, asks the model to fix them.
Next.js mono-repo at control root.
"""

import subprocess, re, json
from pathlib import Path
from repo_config import RepoLayout
from utils import call_hf, log

HEALER_PROMPT = """You are debugging a Next.js full-stack application (App Router + Sequelize).

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
{{"files": [{{"path": "app/... or models/... or lib/...", "content": "...complete corrected file..."}}]}}

Fix ALL listed errors. Use app/, models/, lib/, components/, hooks/, services/ paths. Output complete files, not diffs. No markdown fences.
"""


def run_tests(layout: RepoLayout) -> tuple[bool, str]:
    """Run syntax checks and optional build. Returns (passed, error_log)."""
    errors = []
    workspace = layout.control_root

    for src_dir in layout.app_source_dirs():
        for pattern in ("*.js", "*.jsx"):
            for js_file in src_dir.rglob(pattern):
                if "node_modules" in str(js_file) or ".next" in str(js_file):
                    continue
                result = subprocess.run(
                    ["node", "--check", str(js_file)],
                    capture_output=True, text=True,
                )
                if result.returncode != 0:
                    rel = js_file.relative_to(workspace)
                    errors.append(f"[Syntax error] {rel}:\n{result.stderr.strip()}")

    pkg = layout.control_root / "package.json"
    if pkg.exists():
        try:
            pkg_data = json.loads(pkg.read_text())
            scripts = pkg_data.get("scripts", {})
            if "test" in scripts:
                result = subprocess.run(
                    ["npm", "test", "--", "--passWithNoTests"],
                    capture_output=True, text=True,
                    cwd=layout.control_root,
                    timeout=60,
                )
                if result.returncode != 0:
                    out = (result.stdout + result.stderr)[-1500:]
                    errors.append(f"[Test failure]\n{out}")
        except Exception as e:
            log(f"Healer: could not run tests: {e}")

    if errors:
        error_log = "\n\n".join(errors)
        log(f"Healer: {len(errors)} error group(s) found")
        return False, error_log

    log("Healer: all checks passed")
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
    skip_dirs = {".git", "node_modules", ".next", "dev_agent", "__pycache__"}
    for root in layout.app_source_dirs() + [layout.control_root]:
        if not root.exists():
            continue
        for ext in ("*.js", "*.jsx"):
            for p in root.rglob(ext):
                if any(s in p.parts for s in skip_dirs):
                    continue
                try:
                    all_files.append(str(p.relative_to(layout.control_root)))
                except ValueError:
                    all_files.append(str(p))
    file_list = "\n".join(sorted(set(all_files))[:50])

    prompt = HEALER_PROMPT.format(
        techstack=techstack[:800] if techstack else "Next.js 14 + Sequelize",
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
        for prefix in ("backend/", "frontend/"):
            if path_str.startswith(prefix):
                path_str = path_str[len(prefix):]
                if path_str.startswith("src/"):
                    path_str = path_str[4:]
        target, _ = layout.resolve_path(path_str)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content)
        log(f"  Fixed: {path_str}")
