"""
Coder v2 — generates code for ONE sub-task at a time.
Writes to backend/ and frontend/ paths (separate repos when configured).
"""

import re, json
from pathlib import Path
from repo_config import RepoLayout
from utils import call_hf, log

CODER_PROMPT = """You are an expert full-stack developer. Generate code for ONE specific sub-task.

Tech stack (MUST follow exactly):
{techstack}

Project context:
{project_context}

Repository layout:
{repo_layout_note}

Feature: {feature_name}
Sub-task to implement NOW: {subtask_text}

All other sub-tasks in this feature (for context only — DO NOT implement these):
{other_subtasks}

Output ONLY a raw JSON object — no markdown fences, no explanation, nothing else.
Format:
{{"files": [{{"path": "relative/path/from/workspace.js", "content": "...complete file content..."}}], "required_env": [{{"key": "ENV_VAR_NAME", "description": "why it is needed", "scope": "backend|frontend|github_actions"}}]}}

If this sub-task needs NEW API keys or secrets not already in the project, list them in required_env.
If no new env vars are needed, use an empty array: "required_env": []

Rules:
- Implement ONLY the sub-task listed above
- Use exact folder structure from tech stack
- ALL file paths MUST be prefixed with backend/ or frontend/ (e.g. backend/src/models/User.js, frontend/app/page.js)
- Backend files: CommonJS (require/module.exports)
- Frontend files: ES modules (import/export), JSX for React/Next.js components
- Include proper error handling
- No placeholder comments like "// TODO implement later"
- If updating an existing file, output the complete new version
"""


def _layout_note(layout: RepoLayout) -> str:
    if layout.dual_repo:
        return (
            f"DUAL REPO: backend code → {layout.backend_repo} (path prefix backend/)\n"
            f"DUAL REPO: frontend code → {layout.frontend_repo} (path prefix frontend/)"
        )
    return "MONO REPO: use backend/ and frontend/ path prefixes under one repository."


def generate_subtask(
    feature: dict,
    subtask: dict,
    project_context: str,
    techstack: str,
    layout: RepoLayout,
) -> dict:
    """Returns {success, required_env, written_paths, targets}."""
    log(f"Coder: generating sub-task '{subtask['text']}'")

    other_subtasks = "\n".join(
        f"- {st['text']}"
        for st in feature.get("subtasks", [])
        if st["text"] != subtask["text"]
    )

    prompt = CODER_PROMPT.format(
        techstack=techstack[:1500] if techstack else "Node.js + Express + React",
        project_context=project_context[:800],
        repo_layout_note=_layout_note(layout),
        feature_name=feature["name"],
        subtask_text=subtask["text"],
        other_subtasks=other_subtasks,
    )

    response = call_hf(prompt, max_tokens=2500)

    if not response or len(response.strip()) < 20:
        log("Coder: empty response from model")
        return {"success": False, "required_env": [], "written_paths": [], "targets": []}

    response = re.sub(r"^```(?:json)?\n?", "", response.strip())
    response = re.sub(r"\n?```$", "", response.strip())

    json_match = re.search(r'\{.*"files"\s*:\s*\[', response, re.DOTALL)
    if json_match:
        response = response[json_match.start():]

    required_env: list[dict] = []
    try:
        data  = json.loads(response)
        files = data.get("files", [])
        required_env = data.get("required_env", []) or []
    except json.JSONDecodeError as e:
        log(f"Coder: JSON parse error ({e}) — trying heuristic extraction")
        files = _extract_files_heuristic(response)

    if not files:
        log("Coder: no files extracted")
        return {"success": False, "required_env": required_env, "written_paths": [], "targets": []}

    written_paths: list[str] = []
    for file_def in files:
        path_str = file_def.get("path", "").strip().lstrip("/")
        content  = file_def.get("content", "")
        if not path_str or not content:
            continue
        path_str = _normalize_path(path_str, subtask["text"], layout)
        target_path, _ = layout.resolve_path(path_str)
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(content)
        log(f"  Wrote: {path_str}")
        written_paths.append(path_str)

    targets = layout.targets_for_paths(written_paths) if written_paths else layout.targets_for_subtask(subtask["text"])

    log(f"Coder: wrote {len(written_paths)} file(s) → repos: {targets}")
    return {
        "success":       len(written_paths) > 0,
        "required_env":  required_env,
        "written_paths": written_paths,
        "targets":       targets,
    }


def _normalize_path(path_str: str, subtask_text: str, layout: RepoLayout) -> str:
    """Ensure path has backend/ or frontend/ prefix."""
    if path_str.startswith(("backend/", "frontend/")):
        return path_str
    t = subtask_text.lower()
    if any(w in t for w in ("frontend", "component", "page", "ui", "next")):
        return f"frontend/{path_str}"
    return f"backend/{path_str}"


def _extract_files_heuristic(text: str) -> list[dict]:
    results = []
    for m in re.finditer(r'"path"\s*:\s*"([^"]+)"', text):
        path = m.group(1)
        cm = re.search(r'"content"\s*:\s*"((?:[^"\\]|\\.)*)"', text[m.end():m.end()+8000])
        if cm:
            try:
                content = cm.group(1).encode().decode("unicode_escape")
                results.append({"path": path, "content": content})
            except Exception:
                pass
    return results
