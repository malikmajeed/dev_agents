"""
Emailer v2 — Gmail SMTP send + IMAP reply checking.
Includes PR links in feature-complete emails.
"""

import os, smtplib, imaplib, email as emaillib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from utils import log

GMAIL_USER          = os.environ.get("GMAIL_USER", "")
GMAIL_APP_PASS      = os.environ.get("GMAIL_APP_PASS", "")
NOTIFY_EMAIL        = os.environ.get("NOTIFY_EMAIL", GMAIL_USER)
REPO_NAME           = os.environ.get("GITHUB_REPOSITORY", "your-repo")
APPROVAL_WAIT_HOURS = float(os.environ.get("APPROVAL_WAIT_HOURS", "999"))

GITHUB_URL = f"https://github.com/{REPO_NAME}"


def _send(subject: str, html_body: str):
    if not GMAIL_USER or not GMAIL_APP_PASS:
        log("Emailer: credentials not set — skipping email")
        return
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"]    = GMAIL_USER
        msg["To"]      = NOTIFY_EMAIL
        msg.attach(MIMEText(html_body, "html"))
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
            s.login(GMAIL_USER, GMAIL_APP_PASS)
            s.sendmail(GMAIL_USER, NOTIFY_EMAIL, msg.as_string())
        log(f"Emailer: sent '{subject}'")
    except Exception as e:
        log(f"Emailer: FAILED — {e}")


def _base(content: str) -> str:
    return f"""
<div style="font-family:system-ui,sans-serif;max-width:600px;margin:0 auto;color:#1a1a1a">
  {content}
  <hr style="margin:32px 0;border:none;border-top:1px solid #e5e5e5">
  <p style="color:#888;font-size:12px">
    DevAgent · <a href="{GITHUB_URL}" style="color:#888">{REPO_NAME}</a>
  </p>
</div>
"""


def send_plan_notification(features_md: str):
    subject = f"[DevAgent] 📋 Feature plan ready — {REPO_NAME}"
    body = _base(f"""
<h2 style="margin-top:0">📋 Your project has been planned</h2>
<p>DevAgent has generated a feature list and will start building shortly.
Each feature will arrive as a GitHub PR for you to review.</p>
<pre style="background:#f6f8fa;padding:16px;border-radius:8px;font-size:12px;overflow:auto">{features_md[:3000]}</pre>
<p><a href="{GITHUB_URL}" style="background:#0070f3;color:#fff;padding:10px 20px;border-radius:6px;text-decoration:none;display:inline-block">View on GitHub →</a></p>
""")
    _send(subject, body)


def send_feature_complete(
    feature_name: str,
    done_count: int,
    total: int,
    next_feature: str,
    pr_url: str | None = None,
    pr_urls: dict[str, str] | None = None,
):
    pct  = int(done_count / total * 100)
    subject = f"[DevAgent] ✅ '{feature_name}' done ({done_count}/{total}) — PR ready"

    pr_section = ""
    urls = pr_urls or ({"repo": pr_url} if pr_url else {})
    if urls:
        links = "<br>".join(
            f"<strong>{name}:</strong> <a href=\"{url}\" style=\"color:#15803d\">{url}</a>"
            for name, url in urls.items() if url
        )
        pr_section = f"""
<div style="background:#f0fdf4;border-left:4px solid #22c55e;padding:12px 16px;margin:16px 0;border-radius:4px">
  <strong>PR(s) open and ready for review:</strong><br>
  {links}
</div>
"""

    wait_note = (
        f"Reply <b>OK</b> to merge and continue, or <b>SKIP</b> to move on.<br>"
        f"If no reply in {APPROVAL_WAIT_HOURS:.0f}h, the agent will continue automatically."
        if APPROVAL_WAIT_HOURS < 999
        else "Reply <b>OK</b> to merge and continue, or <b>SKIP</b> to move on.<br>"
             "<em>Auto-continue is disabled — waiting for your reply.</em>"
    )

    body = _base(f"""
<h2 style="margin-top:0">✅ Feature complete: {feature_name}</h2>
<p><strong>Progress:</strong> {done_count} / {total} features ({pct}%)</p>
<div style="background:#f6f8fa;border-radius:8px;padding:4px 0;margin:16px 0">
  <div style="background:#22c55e;height:8px;width:{pct}%;border-radius:8px"></div>
</div>
{pr_section}
<p><strong>Next up:</strong> {next_feature}</p>
<hr style="margin:24px 0;border:none;border-top:1px solid #e5e5e5">
<p style="color:#555">{wait_note}</p>
""")
    _send(subject, body)


def send_blocked_notification(feature_name: str, subtask_text: str, error_log: str):
    subject = f"[DevAgent] ⚠️ Sub-task blocked in '{feature_name}'"
    body = _base(f"""
<h2 style="margin-top:0">⚠️ Sub-task blocked</h2>
<p><strong>Feature:</strong> {feature_name}</p>
<p><strong>Sub-task:</strong> {subtask_text}</p>
<p>The agent tried to implement this sub-task but couldn't pass checks after multiple attempts.
It has moved on to the next sub-task or feature.</p>
<pre style="background:#fff5f5;border-left:4px solid #ef4444;padding:12px 16px;font-size:12px;border-radius:4px;overflow:auto">{error_log[:2000]}</pre>
<p>You can fix this manually on the feature branch, or edit FEATURES.md to reset the sub-task status to <code>pending</code>.</p>
<p><a href="{GITHUB_URL}" style="background:#0070f3;color:#fff;padding:10px 20px;border-radius:6px;text-decoration:none;display:inline-block">View repo →</a></p>
""")
    _send(subject, body)


def send_env_request(
    feature_name: str,
    subtask_text: str,
    pending_env: list[dict],
    secrets_url: str,
):
    keys_html = ""
    for item in pending_env:
        scope = item.get("scope", "github_actions")
        keys_html += f"""
<li>
  <code>{item['key']}</code>
  <span style="color:#666">({scope})</span>
  — {item.get('description', 'Required for this feature')}
</li>"""

    subject = f"[DevAgent] 🔑 Env required for '{feature_name}'"
    body = _base(f"""
<h2 style="margin-top:0">🔑 Environment variables needed</h2>
<p>Feature <strong>{feature_name}</strong> needs credentials before DevAgent can continue.</p>
<p><strong>Sub-task:</strong> {subtask_text}</p>
<ul>{keys_html}</ul>
<hr style="margin:24px 0;border:none;border-top:1px solid #e5e5e5">
<p><strong>Option A — reply with values</strong> (one per line):</p>
<pre style="background:#f6f8fa;padding:12px;border-radius:6px;font-size:13px">STRIPE_SECRET_KEY=sk_live_xxx
SENDGRID_API_KEY=SG.xxx</pre>
<p style="color:#c2410c;font-size:13px">⚠️ Email is not fully secure. Prefer Option B for production secrets.</p>
<p><strong>Option B — add manually</strong>, then reply <b>DONE</b>:</p>
<ol>
  <li>Open <a href="{secrets_url}">GitHub Actions Secrets</a> and add each key above.</li>
  <li>For frontend vars (<code>NEXT_PUBLIC_*</code>), set them in Vercel or <code>frontend/.env</code> locally.</li>
  <li>Check <code>ENV_REGISTRY.md</code> and <code>.env.example</code> files in the repo for placeholders.</li>
</ol>
<p>Reply <b>DONE</b> or <b>CONFIGURED</b> when finished. DevAgent will resume on the next run.</p>
""")
    _send(subject, body)


def send_env_configured_notification(feature_name: str, keys: list[str]):
    subject = f"[DevAgent] ✅ Env configured for '{feature_name}'"
    keys_list = ", ".join(f"<code>{k}</code>" for k in keys) if keys else "all required keys"
    body = _base(f"""
<h2 style="margin-top:0">✅ Environment ready</h2>
<p>Configured: {keys_list}</p>
<p>DevAgent will continue building <strong>{feature_name}</strong> on the next step.</p>
""")
    _send(subject, body)


def send_completion_email(pr_url: str | None = None, pr_urls: dict[str, str] | None = None):
    subject = f"[DevAgent] 🎉 All features complete — {REPO_NAME}"
    urls = pr_urls or ({"repo": pr_url} if pr_url else {})
    pr_section = ""
    if urls:
        links = "<br>".join(
            f"<strong>{name}:</strong> <a href=\"{url}\" style=\"color:#15803d\">{url}</a>"
            for name, url in urls.items() if url
        )
        pr_section = f"""
<div style="background:#f0fdf4;border-left:4px solid #22c55e;padding:12px 16px;margin:16px 0;border-radius:4px">
  <strong>Production PR(s) (staging → main):</strong><br>
  {links}<br>
  <em>Review staging previews before merging to production.</em>
</div>
"""
    body = _base(f"""
<h2 style="margin-top:0">🎉 Project complete!</h2>
<p>DevAgent has finished building all planned features for <strong>{REPO_NAME}</strong>.</p>
{pr_section}
<p><a href="{GITHUB_URL}" style="background:#0070f3;color:#fff;padding:10px 20px;border-radius:6px;text-decoration:none;display:inline-block">View on GitHub →</a></p>
""")
    _send(subject, body)


def check_for_reply(feature_name: str) -> bool | None:
    """
    Check Gmail inbox for a reply to the feature complete email.
    Returns True (OK/approve), False (SKIP/STOP), None (no reply yet).
    """
    if not GMAIL_USER or not GMAIL_APP_PASS:
        return None
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(GMAIL_USER, GMAIL_APP_PASS)
        mail.select("inbox")

        search = f'SUBJECT "[DevAgent] ✅ \'{feature_name}\'"'
        _, data = mail.search(None, search)
        ids = data[0].split()
        if not ids:
            mail.logout()
            return None

        _, msg_data = mail.fetch(ids[-1], "(RFC822)")
        mail.logout()

        raw = msg_data[0][1]
        msg = emaillib.message_from_bytes(raw)
        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    body = part.get_payload(decode=True).decode(errors="ignore")
                    break
        else:
            body = msg.get_payload(decode=True).decode(errors="ignore")

        body_up = body.strip().upper()
        if any(w in body_up for w in ("OK", "APPROVE", "LGTM", "YES", "CONTINUE", "MERGE")):
            return True
        if any(w in body_up for w in ("SKIP", "STOP", "NO", "REJECT", "PAUSE")):
            return False
        return None

    except Exception as e:
        log(f"Emailer: IMAP check failed — {e}")
        return None


def _fetch_reply_body(subject_fragment: str) -> str | None:
    """Fetch plain-text body of the latest inbox message matching subject fragment."""
    if not GMAIL_USER or not GMAIL_APP_PASS:
        return None
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(GMAIL_USER, GMAIL_APP_PASS)
        mail.select("inbox")

        _, data = mail.search(None, f'SUBJECT "{subject_fragment}"')
        ids = data[0].split()
        if not ids:
            mail.logout()
            return None

        _, msg_data = mail.fetch(ids[-1], "(RFC822)")
        mail.logout()

        raw = msg_data[0][1]
        msg = emaillib.message_from_bytes(raw)
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    return part.get_payload(decode=True).decode(errors="ignore")
        return msg.get_payload(decode=True).decode(errors="ignore")
    except Exception as e:
        log(f"Emailer: IMAP fetch failed — {e}")
        return None


def check_for_env_reply(feature_name: str) -> dict | None:
    """
    Check inbox for env configuration reply.
    Returns None (no reply), {"action": "done"}, or {"action": "values", "values": {...}}.
    """
    from env_manager import parse_env_from_text

    body = _fetch_reply_body(f"[DevAgent] 🔑 Env required for '{feature_name}'")
    if not body:
        return None

    body_up = body.strip().upper()
    if any(w in body_up for w in ("DONE", "CONFIGURED", "READY", "SET", "ADDED")):
        return {"action": "done"}

    values = parse_env_from_text(body)
    if values:
        return {"action": "values", "values": values}
    return None
