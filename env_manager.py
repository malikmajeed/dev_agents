"""
Environment variable manager — detect missing keys, ask the user, apply secrets.

Never commits secret values to the repo. Placeholders go in .env.example only.
Values from email replies are stored as GitHub Actions secrets when possible.
"""

import os, re, base64, json, requests
from pathlib import Path
from utils import log

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
GITHUB_REPO  = os.environ.get("GITHUB_REPOSITORY", "")
API_BASE     = "https://api.github.com"

HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}

# Vars DevAgent itself uses — never prompt for these
AGENT_INTERNAL = {
    "HF_API_KEY", "HF_MODEL", "GMAIL_USER", "GMAIL_APP_PASS", "NOTIFY_EMAIL",
    "GITHUB_TOKEN", "GITHUB_REPOSITORY", "REPO_ROOT", "APPROVAL_WAIT_HOURS",
    "MAX_HEAL_RETRIES", "FORCE_FEATURE", "BACKEND_REPOSITORY", "FRONTEND_REPOSITORY",
    "RUNNER_OS", "GITHUB_WORKSPACE", "GITHUB_ACTIONS", "GITHUB_RUN_ID",
}

ENV_SCAN_RE = re.compile(
    r"""
    process\.env\.([A-Z][A-Z0-9_]*)|
    process\.env\[['"]([A-Z][A-Z0-9_]*)['"]\]|
    os\.environ\.get\(\s*['"]([A-Z][A-Z0-9_]*)['"]|
    os\.getenv\(\s*['"]([A-Z][A-Z0-9_]*)['"]|
    (NEXT_PUBLIC_[A-Z0-9_]+)
    """,
    re.VERBOSE,
)


def _api(method: str, path: str, **kwargs) -> dict | list | None:
    if not GITHUB_TOKEN or not GITHUB_REPO:
        return None
    url = f"{API_BASE}/repos/{GITHUB_REPO}{path}"
    resp = requests.request(method, url, headers=HEADERS, **kwargs)
    if resp.status_code in (200, 201, 204):
        return resp.json() if resp.content else {}
    log(f"Env: GitHub API {method} {path} → {resp.status_code}: {resp.text[:200]}")
    return None


def registry_path(repo_root: Path) -> Path:
    return repo_root / "ENV_REGISTRY.md"


def parse_documented_env(repo_root: Path) -> set[str]:
    """Collect env var names from PROJECT.md, TECHSTACK.md, and .env.example files."""
    keys: set[str] = set()
    for rel in ("PROJECT.md", "TECHSTACK.md", "ENV_REGISTRY.md"):
        p = repo_root / rel
        if p.exists():
            keys |= _keys_from_text(p.read_text())
    for example in repo_root.rglob(".env.example"):
        if "node_modules" not in str(example):
            keys |= _keys_from_text(example.read_text())
    return keys


def _keys_from_text(text: str) -> set[str]:
    keys = set()
    for line in text.splitlines():
        m = re.match(r"^([A-Z][A-Z0-9_]*)=", line.strip())
        if m:
            keys.add(m.group(1))
        m = re.search(r"`([A-Z][A-Z0-9_]*)`", line)
        if m:
            keys.add(m.group(1))
    return keys


def load_registry(repo_root: Path) -> list[dict]:
    """Parse ENV_REGISTRY.md rows: key, description, scope, status, feature."""
    path = registry_path(repo_root)
    if not path.exists():
        return []
    entries = []
    for line in path.read_text().splitlines():
        if not line.startswith("|") or line.startswith("| Key") or line.startswith("|-"):
            continue
        cols = [c.strip() for c in line.strip("|").split("|")]
        if len(cols) < 4 or cols[0] in ("Key", ""):
            continue
        entries.append({
            "key":         cols[0],
            "description": cols[1] if len(cols) > 1 else "",
            "scope":       cols[2] if len(cols) > 2 else "github_actions",
            "status":      cols[3] if len(cols) > 3 else "pending",
            "feature":     cols[4] if len(cols) > 4 else "",
        })
    return entries


def save_registry(repo_root: Path, entries: list[dict]):
    lines = [
        "# Environment Variables Registry",
        "",
        "Managed by DevAgent. **Never put real secret values in this file.**",
        "",
        "| Key | Description | Scope | Status | Feature |",
        "|-----|-------------|-------|--------|---------|",
    ]
    for e in entries:
        lines.append(
            f"| {e['key']} | {e.get('description', '')} | "
            f"{e.get('scope', 'github_actions')} | {e.get('status', 'pending')} | "
            f"{e.get('feature', '')} |"
        )
    lines.append("")
    registry_path(repo_root).write_text("\n".join(lines))


def scan_files_for_env(repo_root: Path, paths: list[str] | None = None) -> set[str]:
    """Find env var references in generated source files."""
    found: set[str] = set()
    targets: list[Path] = []
    if paths:
        targets = [repo_root / p for p in paths if (repo_root / p).exists()]
    else:
        for folder in ("backend", "frontend"):
            root = repo_root / folder
            if root.exists():
                for ext in ("*.js", "*.jsx", "*.ts", "*.tsx"):
                    targets.extend(root.rglob(ext))

    for fp in targets:
        if "node_modules" in str(fp):
            continue
        text = fp.read_text(errors="ignore")
        for m in ENV_SCAN_RE.finditer(text):
            key = next(g for g in m.groups() if g)
            if key not in AGENT_INTERNAL:
                found.add(key)
    return found


def infer_scope(key: str) -> str:
    if key.startswith("NEXT_PUBLIC_"):
        return "frontend"
    if key in ("DATABASE_URL", "JWT_SECRET", "JWT_EXPIRES_IN", "PORT",
               "EMAIL_HOST", "EMAIL_PORT", "EMAIL_USER", "EMAIL_PASS", "CLIENT_URL"):
        return "backend"
    return "github_actions"


def list_github_secret_names() -> set[str]:
    data = _api("GET", "/actions/secrets?per_page=100")
    if not data or "secrets" not in data:
        return set()
    return {s["name"] for s in data["secrets"]}


def is_configured(key: str, repo_root: Path, registry: list[dict]) -> bool:
    if key in os.environ and os.environ[key].strip():
        return True
    for e in registry:
        if e["key"] == key and e.get("status") == "configured":
            return True
    if key in list_github_secret_names():
        return True
    return False


def _looks_like_user_secret(key: str) -> bool:
    """True for keys that typically need user-provided credentials."""
    if key in ("PORT", "NODE_ENV", "CLIENT_URL", "JWT_EXPIRES_IN"):
        return False
    patterns = ("API", "KEY", "SECRET", "TOKEN", "PASS", "WEBHOOK", "PRIVATE", "CREDENTIAL")
    return any(p in key for p in patterns)


def merge_required_env(
    model_env: list[dict],
    scanned: set[str],
    repo_root: Path,
    feature_name: str,
) -> list[dict]:
    """Build deduplicated list of env vars that still need user input."""
    registry = load_registry(repo_root)
    documented = parse_documented_env(repo_root)
    results: dict[str, dict] = {}

    for item in model_env:
        key = item.get("key", "").strip()
        if not key or key in AGENT_INTERNAL:
            continue
        results[key] = {
            "key":         key,
            "description": item.get("description", "Required for this feature"),
            "scope":       item.get("scope") or infer_scope(key),
        }

    for key in scanned:
        if key in AGENT_INTERNAL or key in documented:
            continue
        if key in results:
            continue
        if not _looks_like_user_secret(key):
            continue
        results[key] = {
            "key":         key,
            "description": "Referenced in generated code",
            "scope":       infer_scope(key),
        }

    missing = []
    for key, meta in results.items():
        if not is_configured(key, repo_root, registry):
            meta["feature"] = feature_name
            missing.append(meta)
    return missing


def register_pending(repo_root: Path, pending: list[dict], feature_name: str):
    """Add pending keys to ENV_REGISTRY and update .env.example files."""
    entries = load_registry(repo_root)
    by_key = {e["key"]: e for e in entries}

    for item in pending:
        key = item["key"]
        scope = item.get("scope", infer_scope(key))
        by_key[key] = {
            "key":         key,
            "description": item.get("description", ""),
            "scope":       scope,
            "status":      "pending",
            "feature":     feature_name,
        }
        _append_env_example(repo_root, key, scope, item.get("description", ""))

    save_registry(repo_root, list(by_key.values()))
    for item in pending:
        if item.get("scope", infer_scope(item["key"])) == "github_actions":
            ensure_workflow_secret_ref(repo_root, item["key"])


def _append_env_example(repo_root: Path, key: str, scope: str, description: str):
    if scope == "frontend":
        path = repo_root / "frontend" / ".env.example"
    else:
        path = repo_root / "backend" / ".env.example"

    placeholder = "your-value-here"
    if "SECRET" in key or "KEY" in key or "PASS" in key or "TOKEN" in key:
        placeholder = "replace-me"
    if "URL" in key:
        placeholder = "https://example.com"

    line = f"{key}={placeholder}"
    if path.parent.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        existing = path.read_text() if path.exists() else ""
        if key not in existing:
            comment = f"# {description}\n" if description else ""
            path.write_text(existing.rstrip() + f"\n{comment}{line}\n")
            log(f"Env: added {key} to {path.relative_to(repo_root)}")

    _update_project_env_section(repo_root, key, scope)


def _update_project_env_section(repo_root: Path, key: str, scope: str):
    project = repo_root / "PROJECT.md"
    if not project.exists():
        return
    content = project.read_text()
    section = "### Frontend (.env)" if scope == "frontend" else "### Backend (.env)"
    if key in content:
        return
    if section not in content:
        return
    parts = content.split(section, 1)
    if len(parts) < 2:
        return
    before, after = parts
    fence_end = after.find("```", after.find("```") + 3)
    if fence_end == -1:
        return
    insert_at = after.rfind("\n", 0, fence_end)
    new_line = f"\n{key}=<your-value>"
    after = after[:insert_at] + new_line + after[insert_at:]
    project.write_text(before + section + after)


def ensure_workflow_secret_ref(repo_root: Path, key: str):
    """Add ${{ secrets.KEY }} to the DevAgent workflow env block if missing."""
    candidates = [
        repo_root / ".github" / "workflows" / "dev_agent.yml",
        repo_root / "dev_agent" / "dev_agent.yml",
    ]
    ref_line = f"          {key}:               ${{{{ secrets.{key} }}}}"
    for wf in candidates:
        if not wf.exists():
            continue
        content = wf.read_text()
        if f"secrets.{key}" in content:
            return
        marker = "REPO_ROOT:"
        if marker not in content:
            continue
        idx = content.index(marker)
        line_end = content.index("\n", idx)
        content = content[:line_end] + f"\n{ref_line}" + content[line_end:]
        wf.write_text(content)
        log(f"Env: added {key} ref to {wf.relative_to(repo_root)}")


def set_github_secret(name: str, value: str) -> bool:
    """Encrypt and store a GitHub Actions repository secret."""
    pk_data = _api("GET", "/actions/secrets/public-key")
    if not pk_data:
        log(f"Env: cannot set {name} — no public key (need secrets: write permission)")
        return False
    try:
        from nacl import encoding, public
    except ImportError:
        log("Env: PyNaCl not installed — cannot set GitHub secrets from email")
        return False

    public_key = public.PublicKey(
        pk_data["key"].encode("utf-8"), encoding.Base64Encoder()
    )
    sealed = public.SealedBox(public_key).encrypt(value.encode("utf-8"))
    encrypted = base64.b64encode(sealed).decode("utf-8")

    result = _api("PUT", f"/actions/secrets/{name}", json={
        "encrypted_value": encrypted,
        "key_id": pk_data["key_id"],
    })
    if result is not None:
        log(f"Env: stored GitHub secret '{name}'")
        return True
    return False


def mark_configured(repo_root: Path, keys: list[str]):
    entries = load_registry(repo_root)
    for e in entries:
        if e["key"] in keys:
            e["status"] = "configured"
    save_registry(repo_root, entries)


def all_pending_satisfied(repo_root: Path, pending: list[dict]) -> bool:
    registry = load_registry(repo_root)
    gh_secrets = list_github_secret_names()
    for item in pending:
        key = item["key"]
        scope = item.get("scope", infer_scope(key))
        in_registry = any(
            e["key"] == key and e.get("status") == "configured" for e in registry
        )
        in_env = bool(os.environ.get(key, "").strip())
        in_gh = key in gh_secrets
        if scope == "frontend":
            # Frontend vars are usually set in Vercel — user marks DONE manually
            if in_registry or in_env:
                continue
            return False
        if not (in_registry or in_env or in_gh):
            return False
    return True


def apply_env_values(repo_root: Path, values: dict[str, str]) -> list[str]:
    """Store provided values as GitHub secrets and mark configured."""
    configured = []
    for key, value in values.items():
        if key in AGENT_INTERNAL or not value.strip():
            continue
        if set_github_secret(key, value.strip()):
            configured.append(key)
        else:
            log(f"Env: could not auto-store {key} — add manually in GitHub Secrets")
    if configured:
        mark_configured(repo_root, configured)
    return configured


def parse_env_from_text(body: str) -> dict[str, str]:
    """Parse KEY=VALUE or KEY: VALUE lines from an email body."""
    values: dict[str, str] = {}
    for line in body.splitlines():
        line = line.strip()
        if not line or line.startswith(">"):
            continue
        m = re.match(r"^([A-Z][A-Z0-9_]*)=(.+)$", line)
        if m:
            values[m.group(1)] = m.group(2).strip().strip('"').strip("'")
            continue
        m = re.match(r"^([A-Z][A-Z0-9_]*)\s*:\s*(.+)$", line)
        if m:
            values[m.group(1)] = m.group(2).strip().strip('"').strip("'")
    return values


def secrets_settings_url() -> str:
    if GITHUB_REPO:
        return f"https://github.com/{GITHUB_REPO}/settings/secrets/actions"
    return "https://github.com/settings/secrets/actions"
