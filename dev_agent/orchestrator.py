"""
Orchestrator v2 — sub-task level commits, PR flow, TECHSTACK.md awareness.

Each run does exactly ONE thing:
  - One sub-task generated → one commit → push to feature branch
  - When all sub-tasks of a feature are done → open PR to staging → email you
  - You reply OK (or wait) → agent merges PR → moves to next feature
  - When ALL features done → open PR staging → main
"""

import os, sys, json, re
from pathlib import Path
from datetime import datetime, timezone

import planner, coder, healer, emailer, pr_manager, env_manager
from repo_config import RepoLayout
from utils import (
    log, read_techstack, save_features, parse_features,
    get_next_subtask, mark_subtask, update_techstack,
)

REPO_ROOT    = Path(os.environ.get("REPO_ROOT", Path(__file__).parent.parent))
LAYOUT       = RepoLayout.load(REPO_ROOT)
FEATURES_FILE = REPO_ROOT / "FEATURES.md"
PROGRESS_FILE = REPO_ROOT / "PROGRESS.md"
PROJECT_FILE  = REPO_ROOT / "PROJECT.md"
TECHSTACK_FILE = REPO_ROOT / "TECHSTACK.md"

APPROVAL_WAIT_HOURS = float(os.environ.get("APPROVAL_WAIT_HOURS", "999"))
MAX_HEAL_RETRIES    = int(os.environ.get("MAX_HEAL_RETRIES", "3"))


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


def _normalize_pr_numbers(progress: dict) -> dict[str, int]:
    """Support legacy single pr_number and new pr_numbers dict."""
    nums = progress.get("pr_numbers") or {}
    if not nums and progress.get("pr_number"):
        nums = {"control": progress["pr_number"]}
    return {k: v for k, v in nums.items() if v}


def write_progress(data: dict):
    now = datetime.now(timezone.utc).isoformat()
    state_icons = {
        "idle": "💤", "working": "🔨", "awaiting_approval": "⏳",
        "awaiting_env": "🔑", "complete": "🎉", "planned": "📋",
    }
    icon = state_icons.get(data.get("state", "idle"), "❓")
    md = f"""# Agent Progress

_Last updated: {now}_

**State:** {icon} `{data.get('state', 'idle')}`  
**Feature:** {data.get('current_feature') or '—'}  
**Sub-task:** {data.get('current_subtask') or '—'}  
**Branch:** {data.get('branch') or '—'}  
**PR:** {_pr_display(data)}  
**Repos:** {'dual (backend + frontend)' if LAYOUT.dual_repo else 'mono'}  
**Last action:** {data.get('last_action') or '—'}

```json
{json.dumps(data, indent=2)}
```
"""
    PROGRESS_FILE.write_text(md)


def hours_since(iso_str: str) -> float:
    if not iso_str:
        return 999
    dt = datetime.fromisoformat(iso_str)
    now = datetime.now(timezone.utc)
    return (now - dt).total_seconds() / 3600


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    global LAYOUT
    LAYOUT = RepoLayout.load(REPO_ROOT)
    log("=== DevAgent v2 orchestrator starting ===")

    # ── 0. First run: generate FEATURES.md ────────────────────────────────────
    if not FEATURES_FILE.exists():
        if not PROJECT_FILE.exists():
            log("ERROR: PROJECT.md missing. Cannot plan.")
            sys.exit(1)
        log("No FEATURES.md — running planner...")
        project_desc = PROJECT_FILE.read_text()
        techstack    = read_techstack(REPO_ROOT)
        planner.generate_features(project_desc, techstack, FEATURES_FILE)

        pr_manager.ensure_all_staging(LAYOUT)
        pr_manager.commit_control("chore: initial feature plan [DevAgent]", LAYOUT)
        write_progress({"state": "planned", "last_action": "Generated FEATURES.md"})
        emailer.send_plan_notification(FEATURES_FILE.read_text())
        return

    # ── 1. Read state ──────────────────────────────────────────────────────────
    progress = read_progress()
    state    = progress.get("state", "idle")
    log(f"State: {state}")

    # ── 2. Awaiting approval after a completed feature ─────────────────────────
    if state == "awaiting_approval":
        feature_name = progress.get("current_feature")
        pr_numbers   = _normalize_pr_numbers(progress)
        waiting_since = progress.get("waiting_since")

        reply = emailer.check_for_reply(feature_name)

        approved = (
            reply is True or
            (reply is None and hours_since(waiting_since) >= APPROVAL_WAIT_HOURS)
        )
        rejected = reply is False

        if approved:
            action = "Approval received" if reply is True else f"Auto-approved after {APPROVAL_WAIT_HOURS:.0f}h"
            log(f"{action} — merging PR(s) {pr_numbers}")
            pr_manager.merge_feature_prs(pr_numbers, feature_name, LAYOUT)
            progress["state"] = "idle"
            progress["waiting_since"] = None
            progress["pr_numbers"] = None
            progress["pr_urls"] = None

        elif rejected:
            log("Rejected — marking feature needs_revision")
            features = parse_features(FEATURES_FILE)
            for f in features:
                if f["name"] == feature_name:
                    f["status"] = "needs_revision"
                    f["note"]   = "Rejected by reviewer — awaiting manual fix"
            save_features(features, FEATURES_FILE)
            pr_manager.commit_control(
                f"chore: mark {feature_name} needs_revision [DevAgent]", LAYOUT
            )
            progress["state"] = "idle"

        else:
            waited = hours_since(waiting_since)
            log(f"Still waiting for approval ({waited:.1f}h / {APPROVAL_WAIT_HOURS:.0f}h). Exiting.")
            return

        write_progress(progress)

    # ── 2b. Awaiting env vars for current sub-task ─────────────────────────────
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
            waited = hours_since(progress.get("waiting_since"))
            log(f"Still waiting for env vars ({waited:.1f}h). Reply to the 🔑 email.")
            return
        else:
            # Satisfied via email values or manual GitHub Secrets — mark configured
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

    # ── 3. Pick next feature ───────────────────────────────────────────────────
    features = parse_features(FEATURES_FILE)
    pending  = [f for f in features if f["status"] in ("pending", "needs_revision", "in_progress")]

    if not pending:
        all_done = all(f["status"] in ("done",) for f in features)
        if all_done:
            log("🎉 All features done! Opening staging → main PR(s).")
            done_count = len(features)
            release_prs = pr_manager.open_release_prs(done_count, done_count, LAYOUT)
            emailer.send_completion_email(pr_urls=release_prs)
            write_progress({
                "state": "complete",
                "last_action": "All features done",
                "pr_urls": release_prs,
            })
        else:
            log("No pending features (some blocked). Exiting.")
        return

    feature = pending[0]
    log(f"Feature: '{feature['name']}' (status: {feature['status']})")

    # ── 4. Ensure feature branch ───────────────────────────────────────────────
    slug   = pr_manager.slugify(feature["name"])
    branch = f"feat/{slug}"
    pr_manager.ensure_feature_branches(branch, LAYOUT)

    # ── 5. Pick next sub-task ──────────────────────────────────────────────────
    subtask = get_next_subtask(feature)

    if not subtask:
        # All sub-tasks done — open PR if not already open
        feature["status"] = "done"
        save_features(features, FEATURES_FILE)

        pr_manager.commit_control(
            f"chore: mark {feature['name']} complete [DevAgent]", LAYOUT
        )

        prs = pr_manager.open_feature_prs(feature["name"], branch, LAYOUT)
        pr_urls    = {k: v["url"] for k, v in prs.items()}
        pr_numbers = {k: v["number"] for k, v in prs.items() if v.get("number")}

        done_count = sum(1 for f in features if f["status"] == "done")
        total      = len(features)
        next_feat  = pending[1]["name"] if len(pending) > 1 else "— last feature —"

        write_progress({
            "state":           "awaiting_approval",
            "current_feature": feature["name"],
            "branch":          branch,
            "pr_urls":         pr_urls,
            "pr_numbers":      pr_numbers,
            "waiting_since":   datetime.now(timezone.utc).isoformat(),
            "last_action":     f"PR(s) opened for {feature['name']}",
        })

        emailer.send_feature_complete(
            feature_name=feature["name"],
            done_count=done_count,
            total=total,
            next_feature=next_feat,
            pr_urls=pr_urls,
        )
        log(f"PR opened for '{feature['name']}'. Awaiting your approval.")
        return

    # ── 6. Mark feature in_progress ───────────────────────────────────────────
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

    # ── 7. Generate code for this sub-task ────────────────────────────────────
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
            "waiting_since":    datetime.now(timezone.utc).isoformat(),
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
    targets = commit_targets or LAYOUT.targets_for_subtask(subtask["text"])

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
            f"fix: attempted heal for '{subtask['text'][:50]}' [DevAgent]", LAYOUT, targets,
        )
        return

    mark_subtask(feature, subtask["text"], "done")

    remaining = [st for st in feature["subtasks"] if st["status"] == "pending"]
    if not remaining:
        feature["status"] = "in_progress"

    save_features(features, FEATURES_FILE)

    commit_msg = _subtask_to_commit(feature["name"], subtask["text"])
    committed  = pr_manager.commit_subtask(commit_msg, LAYOUT, targets)
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
    if "backend" in sub_lower or "model" in sub_lower or "schema" in sub_lower:
        prefix = "feat(backend)"
    elif "api" in sub_lower or "route" in sub_lower or "endpoint" in sub_lower:
        prefix = "feat(api)"
    elif "frontend" in sub_lower or "component" in sub_lower or "page" in sub_lower or "ui" in sub_lower:
        prefix = "feat(ui)"
    elif "wiring" in sub_lower or "integration" in sub_lower or "connect" in sub_lower:
        prefix = "feat(wiring)"
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
