"""
Orchestrator — Next.js mono-repo, one sub-task per run, auto-merge to main.

Each run does exactly ONE thing:
  - One sub-task generated → one commit → push to feature branch
  - When all sub-tasks of a feature are done → open PR → auto-merge to main
  - When ALL features done → send completion email
"""

import os, sys, json, re
from pathlib import Path
from datetime import datetime, timezone

import coder, healer, emailer, pr_manager, env_manager, bootstrap, planner
from repo_config import RepoLayout
from utils import (
    log, read_techstack, save_features, parse_features,
    get_next_subtask, mark_subtask, update_techstack,
)

REPO_ROOT     = Path(os.environ.get("REPO_ROOT", Path(__file__).parent.parent))
LAYOUT        = RepoLayout.load(REPO_ROOT)
FEATURES_FILE = REPO_ROOT / "FEATURES.md"
PROGRESS_FILE = REPO_ROOT / "PROGRESS.md"
PROJECT_FILE  = REPO_ROOT / "PROJECT.md"

MAX_HEAL_RETRIES = int(os.environ.get("MAX_HEAL_RETRIES", "3"))


# ── Progress state ─────────────────────────────────────────────────────────────

def read_progress() -> dict:
    if not PROGRESS_FILE.exists():
        return {"state": "idle"}
    content = PROGRESS_FILE.read_text()
    match = re.search(r"```json\n(.*?)\n```", content, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except Exception:
            pass
    return {"state": "idle"}


def _pr_display(data: dict) -> str:
    if data.get("pr_urls"):
        return ", ".join(f"{k}: {v}" for k, v in data["pr_urls"].items())
    return data.get("pr_url") or "—"


def write_progress(data: dict):
    now = datetime.now(timezone.utc).isoformat()
    state_icons = {
        "idle": "💤", "working": "🔨", "awaiting_env": "🔑",
        "complete": "🎉", "planned": "📋",
    }
    icon = state_icons.get(data.get("state", "idle"), "❓")
    md = f"""# Agent Progress

_Last updated: {now}_

**State:** {icon} `{data.get('state', 'idle')}`  
**Feature:** {data.get('current_feature') or '—'}  
**Sub-task:** {data.get('current_subtask') or '—'}  
**Branch:** {data.get('branch') or '—'}  
**PR:** {_pr_display(data)}  
**Layout:** Next.js mono-repo  
**Last action:** {data.get('last_action') or '—'}

```json
{json.dumps(data, indent=2)}
```
"""
    PROGRESS_FILE.write_text(md)


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    global LAYOUT
    LAYOUT = RepoLayout.load(REPO_ROOT)
    log("=== DevAgent orchestrator starting (Next.js mono-repo) ===")

    pr_manager.sync_repo(REPO_ROOT)

    # ── First run: generate FEATURES.md from PROJECT.md ────────────────────────
    if not FEATURES_FILE.exists():
        if not PROJECT_FILE.exists():
            log("ERROR: PROJECT.md missing. Cannot plan features.")
            sys.exit(1)
        log("No FEATURES.md — running planner from PROJECT.md...")
        project_desc = PROJECT_FILE.read_text()
        techstack    = read_techstack(REPO_ROOT)
        planner.generate_features(project_desc, techstack, FEATURES_FILE)
        bootstrap.ensure_scaffold(REPO_ROOT)
        pr_manager.commit_control("chore: initial feature plan + scaffold [DevAgent]", LAYOUT)
        write_progress({"state": "planned", "last_action": "Generated FEATURES.md from PROJECT.md"})
        emailer.send_plan_notification(FEATURES_FILE.read_text())
        return

    if bootstrap.ensure_scaffold(REPO_ROOT):
        pr_manager.commit_control("chore: bootstrap Next.js scaffold [DevAgent]", LAYOUT)

    progress = read_progress()
    state    = progress.get("state", "idle")
    log(f"State: {state}")

    # ── Awaiting env vars for current sub-task ─────────────────────────────────
    if state == "awaiting_env":
        feature_name = progress.get("current_feature")
        subtask_text = progress.get("current_subtask")
        pending_env  = progress.get("pending_env", [])
        branch       = progress.get("branch", "")

        reply = emailer.check_for_env_reply(feature_name)
        configured_keys: list[str] = []

        if reply and reply.get("action") == "values":
            configured_keys = env_manager.apply_env_values(
                REPO_ROOT, reply.get("values", {})
            )

        ready = env_manager.all_pending_satisfied(REPO_ROOT, pending_env)

        if reply and reply.get("action") == "done":
            if not ready:
                log("Env: user replied DONE but some keys still missing — waiting.")
                return
            env_manager.mark_configured(
                REPO_ROOT, [e["key"] for e in pending_env]
            )
        elif not ready:
            log("Still waiting for env vars. Reply to the env email or add GitHub Secrets.")
            return
        else:
            env_manager.mark_configured(
                REPO_ROOT, [e["key"] for e in pending_env]
            )

        if configured_keys:
            emailer.send_env_configured_notification(feature_name, configured_keys)
        pr_manager.commit_control(
            f"chore: env configured for {feature_name} [DevAgent]", LAYOUT
        )

        features = parse_features(FEATURES_FILE)
        feature  = next((f for f in features if f["name"] == feature_name), None)
        subtask  = {"text": subtask_text} if subtask_text else None
        if not feature or not subtask:
            progress["state"] = "idle"
            write_progress(progress)
            return

        project_context = PROJECT_FILE.read_text() if PROJECT_FILE.exists() else ""
        techstack       = read_techstack(REPO_ROOT)
        commit_targets  = progress.get("commit_targets")
        _run_heal_and_commit(
            feature, subtask, features, branch, project_context, techstack, commit_targets,
        )
        return

    # ── Pick next feature ──────────────────────────────────────────────────────
    features = parse_features(FEATURES_FILE)
    pending  = [f for f in features if f["status"] in ("pending", "needs_revision", "in_progress")]

    if not pending:
        all_done = all(f["status"] == "done" for f in features)
        if all_done and state != "complete":
            log("All features done!")
            emailer.send_completion_email()
            write_progress({
                "state": "complete",
                "last_action": "All features done",
            })
        else:
            log("No pending features (some blocked). Exiting.")
        return

    feature = pending[0]
    log(f"Feature: '{feature['name']}' (status: {feature['status']})")

    slug   = pr_manager.slugify(feature["name"])
    branch = f"feat/{slug}"
    pr_manager.ensure_feature_branch(branch, LAYOUT)

    subtask = get_next_subtask(feature)

    if not subtask:
        feature["status"] = "done"
        save_features(features, FEATURES_FILE)
        pr_manager.commit_control(
            f"chore: mark {feature['name']} complete [DevAgent]", LAYOUT
        )

        result = pr_manager.auto_merge_feature_pr(feature["name"], branch, LAYOUT)
        if not result:
            log(f"ERROR: Auto-merge failed for '{feature['name']}'")
            feature["status"] = "in_progress"
            feature["note"] = "PR merge failed — will retry on next run"
            save_features(features, FEATURES_FILE)
            pr_manager.commit_control(
                f"chore: merge failed for {feature['name']} [DevAgent]", LAYOUT
            )
            emailer.send_blocked_notification(
                feature["name"],
                "Auto-merge PR",
                "Branch push or GitHub PR merge failed",
            )
            write_progress({
                "state":           "idle",
                "current_feature": feature["name"],
                "branch":          branch,
                "last_action":     f"Merge failed for {feature['name']}",
            })
            return

        done_count = sum(1 for f in features if f["status"] == "done")
        total      = len(features)
        next_feat  = pending[1]["name"] if len(pending) > 1 else "— last feature —"
        pr_url     = result.get("url", "")

        write_progress({
            "state":           "idle",
            "current_feature": feature["name"],
            "branch":          branch,
            "pr_url":          pr_url,
            "last_action":     f"Merged {feature['name']} to main",
        })

        emailer.send_feature_complete(
            feature_name=feature["name"],
            done_count=done_count,
            total=total,
            next_feature=next_feat,
            pr_url=pr_url,
        )
        log(f"Feature '{feature['name']}' merged to main.")
        return

    feature["status"] = "in_progress"
    mark_subtask(feature, subtask["text"], "in_progress")
    save_features(features, FEATURES_FILE)

    write_progress({
        "state":            "working",
        "current_feature":  feature["name"],
        "current_subtask":  subtask["text"],
        "branch":           branch,
        "last_action":      f"Started sub-task: {subtask['text']}",
    })

    project_context = PROJECT_FILE.read_text() if PROJECT_FILE.exists() else ""
    techstack       = read_techstack(REPO_ROOT)

    success = coder.generate_subtask(feature, subtask, project_context, techstack, LAYOUT)

    if not success["success"]:
        mark_subtask(feature, subtask["text"], "blocked")
        feature["note"] = f"Sub-task blocked: {subtask['text']}"
        save_features(features, FEATURES_FILE)
        emailer.send_blocked_notification(feature["name"], subtask["text"], "Model returned empty")
        write_progress({"state": "idle", "last_action": f"Blocked: {subtask['text']}"})
        pr_manager.commit_control(
            f"chore: block subtask '{subtask['text'][:50]}' [DevAgent]", LAYOUT
        )
        return

    commit_targets = success.get("targets") or LAYOUT.targets_for_subtask(subtask["text"])

    scanned = env_manager.scan_files_for_env(REPO_ROOT, success.get("written_paths"))
    pending_env = env_manager.merge_required_env(
        success.get("required_env", []),
        scanned,
        REPO_ROOT,
        feature["name"],
    )

    if pending_env:
        log(f"Env: {len(pending_env)} variable(s) need configuration — pausing")
        env_manager.register_pending(REPO_ROOT, pending_env, feature["name"])
        pr_manager.commit_control(
            f"chore: document env vars for {feature['name']} [DevAgent]", LAYOUT
        )
        emailer.send_env_request(
            feature_name=feature["name"],
            subtask_text=subtask["text"],
            pending_env=pending_env,
            secrets_url=env_manager.secrets_settings_url(),
        )
        write_progress({
            "state":            "awaiting_env",
            "current_feature":  feature["name"],
            "current_subtask":  subtask["text"],
            "branch":           branch,
            "pending_env":      pending_env,
            "commit_targets":   commit_targets,
            "last_action":      f"Awaiting env for: {subtask['text']}",
        })
        return

    _run_heal_and_commit(
        feature, subtask, features, branch, project_context, techstack, commit_targets,
    )


def _run_heal_and_commit(
    feature: dict,
    subtask: dict,
    features: list,
    branch: str,
    project_context: str,
    techstack: str,
    commit_targets: list[str] | None = None,
):
    """Self-heal, commit, and mark sub-task done."""
    passed, error_log = healer.run_tests(LAYOUT)
    retries = 0

    while not passed and retries < MAX_HEAL_RETRIES:
        retries += 1
        log(f"Tests failed. Healing attempt {retries}/{MAX_HEAL_RETRIES}")
        write_progress({
            "state":           "working",
            "current_feature": feature["name"],
            "current_subtask": subtask["text"],
            "branch":          branch,
            "last_action":     f"Healing attempt {retries}: {subtask['text']}",
        })
        healer.fix_code(feature, subtask, error_log, project_context, techstack, LAYOUT)
        passed, error_log = healer.run_tests(LAYOUT)

    if not passed:
        mark_subtask(feature, subtask["text"], "blocked")
        feature["note"] = f"Blocked after {MAX_HEAL_RETRIES} heal attempts on: {subtask['text']}"
        save_features(features, FEATURES_FILE)
        emailer.send_blocked_notification(feature["name"], subtask["text"], error_log)
        write_progress({"state": "idle", "last_action": f"Blocked after healing: {subtask['text']}"})
        pr_manager.commit_subtask(
            f"fix: attempted heal for '{subtask['text'][:50]}' [DevAgent]", LAYOUT,
        )
        return

    mark_subtask(feature, subtask["text"], "done")

    remaining = [st for st in feature["subtasks"] if st["status"] == "pending"]
    if not remaining:
        feature["status"] = "in_progress"

    save_features(features, FEATURES_FILE)

    commit_msg = _subtask_to_commit(feature["name"], subtask["text"])
    committed  = pr_manager.commit_subtask(commit_msg, LAYOUT)
    pr_manager.commit_control(f"chore: sync {feature['name']} progress [DevAgent]", LAYOUT)

    if committed:
        update_techstack(REPO_ROOT, "DevAgent", "last_commit", commit_msg)

    write_progress({
        "state":           "idle",
        "current_feature": feature["name"],
        "current_subtask": None,
        "branch":          branch,
        "last_action":     commit_msg,
    })
    log(f"Sub-task done: '{subtask['text']}'")


def _subtask_to_commit(feature: str, subtask: str) -> str:
    """Turn a sub-task description into a conventional commit message."""
    sub_lower = subtask.lower()
    if "database" in sub_lower or "model" in sub_lower or "schema" in sub_lower:
        prefix = "feat(db)"
    elif "api" in sub_lower or "route" in sub_lower:
        prefix = "feat(api)"
    elif "ui" in sub_lower or "component" in sub_lower or "page" in sub_lower:
        prefix = "feat(ui)"
    elif "integration" in sub_lower or "wiring" in sub_lower or "connect" in sub_lower:
        prefix = "feat(integration)"
    elif "test" in sub_lower:
        prefix = "test"
    elif "fix" in sub_lower or "bug" in sub_lower:
        prefix = "fix"
    else:
        prefix = "feat"

    slug_feat = feature.lower()[:30]
    desc      = subtask[:60]
    return f"{prefix}({slug_feat}): {desc} [DevAgent]"


if __name__ == "__main__":
    main()
