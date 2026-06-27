"""
Shared utilities: HuggingFace API, FEATURES.md parsing, TECHSTACK.md reading, logging.
"""

import os, re, time, json, requests
from pathlib import Path
from datetime import datetime, timezone

HF_API_KEY  = os.environ.get("HF_API_KEY", "")
HF_MODEL    = os.environ.get("HF_MODEL", "mistralai/Mistral-7B-Instruct-v0.3")
HF_API_URL  = "https://router.huggingface.co/v1/chat/completions"


def log(msg: str):
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    print(f"[{ts}] {msg}", flush=True)


# ── HuggingFace API ────────────────────────────────────────────────────────────

def call_hf(prompt: str, max_tokens: int = 2000, retries: int = 3) -> str:
    """Call HuggingFace Inference Providers (router API). Returns text or empty string."""
    if not HF_API_KEY:
        log("WARNING: HF_API_KEY not set — model calls will fail")
        return ""

    headers = {
        "Authorization": f"Bearer {HF_API_KEY}",
        "Content-Type":  "application/json",
    }
    payload = {
        "model": HF_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": 0.2,
        "stream": False,
    }

    for attempt in range(1, retries + 1):
        try:
            resp = requests.post(HF_API_URL, headers=headers, json=payload, timeout=120)
            if resp.status_code == 503:
                log(f"HF: model loading (503). Waiting 20s... (attempt {attempt})")
                time.sleep(20)
                continue
            if resp.status_code == 429:
                log(f"HF: rate limited (429). Waiting 60s... (attempt {attempt})")
                time.sleep(60)
                continue
            if resp.status_code in (401, 403):
                log(f"HF: auth error ({resp.status_code}) — check HF_API_KEY has Inference Providers permission")
                log(f"HF: {resp.text[:300]}")
                return ""
            resp.raise_for_status()
            data = resp.json()
            choices = data.get("choices") or []
            if choices:
                content = choices[0].get("message", {}).get("content", "")
                if content:
                    return content.strip()
            if data.get("error"):
                log(f"HF: API error — {data['error']}")
            return ""
        except requests.RequestException as e:
            log(f"HF: request error on attempt {attempt}: {e}")
            if attempt < retries:
                time.sleep(10 * attempt)
    return ""


# ── TECHSTACK.md ───────────────────────────────────────────────────────────────

def read_techstack(repo_root: Path) -> str:
    """Read TECHSTACK.md for injection into prompts."""
    ts_file = repo_root / "TECHSTACK.md"
    if ts_file.exists():
        return ts_file.read_text()
    return ""


def update_techstack(repo_root: Path, section: str, key: str, value: str):
    """
    Update a specific entry in TECHSTACK.md.
    section: 'Backend' | 'Frontend' | 'Deployment' | 'DevAgent'
    key: the package/tool name
    value: new version or note
    """
    ts_file = repo_root / "TECHSTACK.md"
    if not ts_file.exists():
        return
    content = ts_file.read_text()
    # Update the _Last updated by_ line
    content = re.sub(
        r"_Last updated by:.*_",
        f"_Last updated by: DevAgent on {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}_",
        content,
    )
    ts_file.write_text(content)
    log(f"TECHSTACK.md updated: [{section}] {key} = {value}")


# ── FEATURES.md ────────────────────────────────────────────────────────────────

def read_md(path: Path) -> str:
    return path.read_text() if path.exists() else ""


def write_md(path: Path, content: str):
    path.write_text(content)


def parse_features(features_path: Path) -> list[dict]:
    """
    Parse FEATURES.md into a list of feature dicts.
    Each feature has: name, status, priority, subtasks (list of dicts), note
    Each subtask: {text, status: pending|done|in_progress|blocked}
    """
    content = features_path.read_text()
    features = []
    blocks = re.split(r"\n## ", content)

    for block in blocks[1:]:
        lines = block.strip().split("\n")
        if not lines:
            continue

        name = lines[0].strip()
        status   = "pending"
        priority = "medium"
        subtasks = []
        note     = ""

        for line in lines[1:]:
            m = re.search(r"\*\*Status:\*\*\s*(\S+)", line)
            if m:
                status = m.group(1).strip().rstrip("*").rstrip("✅🔄❌⏳🔁")

            m = re.search(r"\*\*Priority:\*\*\s*(\S+)", line)
            if m:
                priority = m.group(1).strip().rstrip("*")

            m = re.search(r"\*\*Note:\*\*\s*(.+)", line)
            if m:
                note = m.group(1).strip()

            # Sub-tasks with status
            m = re.match(r"\s*-\s*\[([ xXpP~])\]\s*(.+)", line)
            if m:
                cb, text = m.group(1), m.group(2).strip()
                sub_status = (
                    "done"        if cb in ("x", "X") else
                    "in_progress" if cb == "p" else
                    "blocked"     if cb == "~" else
                    "pending"
                )
                subtasks.append({"text": text, "status": sub_status})

        features.append({
            "name":     name,
            "status":   status,
            "priority": priority,
            "subtasks": subtasks,
            "note":     note,
        })

    return features


def get_next_subtask(feature: dict) -> dict | None:
    """Return the first pending subtask of a feature."""
    for st in feature.get("subtasks", []):
        if st["status"] == "pending":
            return st
    return None


def mark_subtask(feature: dict, subtask_text: str, status: str):
    """Update a subtask's status in the feature dict."""
    for st in feature.get("subtasks", []):
        if st["text"] == subtask_text:
            st["status"] = status
            return


def save_features(features: list[dict], features_path: Path):
    """Serialise feature list back to FEATURES.md."""
    STATUS_ICON = {
        "done": "✅", "in_progress": "🔄", "blocked": "❌",
        "needs_revision": "🔁", "pending": "⏳",
    }
    SUBTASK_CB = {
        "done": "x", "in_progress": "p", "blocked": "~", "pending": " ",
    }

    lines = ["# FEATURES\n"]
    for f in features:
        icon = STATUS_ICON.get(f["status"], "⏳")
        lines.append(f"## {f['name']}")
        lines.append(f"**Status:** {f['status']} {icon}  ")
        lines.append(f"**Priority:** {f.get('priority', 'medium')}  ")
        if f.get("note"):
            lines.append(f"**Note:** {f['note']}  ")
        lines.append("**Sub-tasks:**")
        for st in f.get("subtasks", []):
            cb = SUBTASK_CB.get(st["status"], " ")
            lines.append(f"- [{cb}] {st['text']}")
        lines.append("\n---\n")

    features_path.write_text("\n".join(lines))
