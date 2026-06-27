"""
Shared utilities: HuggingFace API, FEATURES.md parsing, TECHSTACK.md reading, logging.
"""

import os, re, time, json, requests
from pathlib import Path
from datetime import datetime, timezone

HF_API_KEY  = os.environ.get("HF_API_KEY", "")
HF_MODEL    = os.environ.get("HF_MODEL", "openai/gpt-oss-120b:fastest")
HF_CHAT_URL = "https://router.huggingface.co/v1/chat/completions"
HF_TEXT_URL = "https://router.huggingface.co/hf-inference/models"


def log(msg: str):
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    print(f"[{ts}] {msg}", flush=True)


# ── HuggingFace API ────────────────────────────────────────────────────────────

def _hf_headers() -> dict:
    return {
        "Authorization": f"Bearer {HF_API_KEY}",
        "Content-Type":  "application/json",
    }


def _normalize_model(model: str) -> str:
    """Append :fastest provider policy if no provider suffix given."""
    if ":" not in model:
        return f"{model}:fastest"
    return model


def _model_id(model: str) -> str:
    """Strip provider suffix (e.g. openai/gpt-oss-120b:fastest → openai/gpt-oss-120b)."""
    return model.split(":")[0]


def _parse_chat_response(data: dict) -> str:
    choices = data.get("choices") or []
    if choices:
        content = choices[0].get("message", {}).get("content", "")
        if content:
            return content.strip()
    err = data.get("error")
    if isinstance(err, dict):
        log(f"HF chat error — {err.get('message', err)}")
    elif err:
        log(f"HF chat error — {err}")
    return ""


def _parse_textgen_response(data) -> str:
    if isinstance(data, list) and data:
        text = data[0].get("generated_text", "")
        if text:
            return text.strip()
    if isinstance(data, dict):
        text = data.get("generated_text", "")
        if text:
            return text.strip()
    return ""


def _call_chat(prompt: str, model: str, max_tokens: int) -> str:
    payload = {
        "model":       model,
        "messages":    [{"role": "user", "content": prompt}],
        "max_tokens":  max_tokens,
        "temperature": 0.2,
    }
    resp = requests.post(HF_CHAT_URL, headers=_hf_headers(), json=payload, timeout=120)
    if resp.status_code in (401, 403):
        log(f"HF: auth error ({resp.status_code}) — check HF_API_KEY has Inference Providers permission")
        log(f"HF: {resp.text[:300]}")
        return ""
    if resp.status_code == 400:
        log(f"HF chat 400 for model '{model}': {resp.text[:400]}")
        return ""
    if resp.status_code == 429:
        return "__RATE_LIMIT__"
    if resp.status_code == 503:
        return "__LOADING__"
    resp.raise_for_status()
    return _parse_chat_response(resp.json())


def _call_textgen(prompt: str, model: str, max_tokens: int) -> str:
    """Fallback: legacy inputs format via hf-inference provider."""
    url = f"{HF_TEXT_URL}/{model}"
    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens":   max_tokens,
            "temperature":      0.2,
            "return_full_text": False,
        },
    }
    resp = requests.post(url, headers=_hf_headers(), json=payload, timeout=120)
    if resp.status_code in (401, 403):
        log(f"HF: auth error ({resp.status_code}) on textgen")
        return ""
    if resp.status_code == 400:
        log(f"HF textgen 400 for model '{model}': {resp.text[:400]}")
        return ""
    if resp.status_code == 429:
        return "__RATE_LIMIT__"
    if resp.status_code == 503:
        return "__LOADING__"
    resp.raise_for_status()
    return _parse_textgen_response(resp.json())


def call_hf(prompt: str, max_tokens: int = 2000, retries: int = 3) -> str:
    """Call HuggingFace Inference Providers. Returns text or empty string."""
    if not HF_API_KEY:
        log("WARNING: HF_API_KEY not set — model calls will fail")
        return ""

    chat_model = _normalize_model(HF_MODEL)
    text_model = _model_id(HF_MODEL)
    log(f"HF: model={chat_model}")

    for attempt in range(1, retries + 1):
        try:
            result = _call_chat(prompt, chat_model, max_tokens)
            if result in ("__RATE_LIMIT__", "__LOADING__"):
                wait = 60 if result == "__RATE_LIMIT__" else 20
                log(f"HF: {'rate limited' if wait == 60 else 'model loading'}. Waiting {wait}s...")
                time.sleep(wait)
                continue
            if not result:
                log("HF: chat failed — trying text-generation fallback")
                result = _call_textgen(prompt, text_model, max_tokens)
                if result in ("__RATE_LIMIT__", "__LOADING__"):
                    wait = 60 if result == "__RATE_LIMIT__" else 20
                    time.sleep(wait)
                    continue
            if result:
                return result
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
