#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

DEFAULT_SECRET_NAME = "TELEGRAM_BOT_TOKEN"


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def telegram_config(profile: dict[str, Any]) -> dict[str, Any]:
    project_id = profile.get("active_project_id")
    projects = profile.get("projects")
    if not isinstance(project_id, str) or not isinstance(projects, dict) or not isinstance(projects.get(project_id), dict):
        raise ValueError("active project is missing from user profile")
    project = projects[project_id]
    notifications = project.get("notifications")
    if not isinstance(notifications, dict):
        return {}
    telegram = notifications.get("telegram")
    return telegram if isinstance(telegram, dict) else {}


def iso_from_epoch(value: Any) -> str | None:
    try:
        epoch = int(value)
    except (TypeError, ValueError):
        return None
    if epoch <= 0:
        return None
    return dt.datetime.fromtimestamp(epoch, dt.timezone.utc).isoformat().replace("+00:00", "Z")


def report_message(platform: str, record: dict[str, Any]) -> str:
    candidate = record.get("candidate") if isinstance(record.get("candidate"), dict) else {}
    execution = record.get("execution") if isinstance(record.get("execution"), dict) else {}
    post_id = str(candidate.get("post_id") or record.get("post_id") or "unknown")
    planned_at = str(candidate.get("planned_at") or "unknown")
    evidence = execution.get("evidence") if isinstance(execution.get("evidence"), dict) else {}
    published_at = iso_from_epoch(evidence.get("published_at")) or str(execution.get("last_attempt_at") or "unknown")
    state = str(execution.get("state") or "unknown")

    lines = [f"Rapport de publication {post_id}", f"Plateforme : {platform}", f"Planifié : {planned_at}"]

    if platform == "facebook":
        verification = execution.get("verification") if isinstance(execution.get("verification"), dict) else {}
        verification_state = str(verification.get("verification_state") or verification.get("state") or "unknown")
        if state == "remote_verified" or verification_state == "remote_verified":
            lines.append("Statut : ✅ publié et vérifié sur Facebook (remote_verified)")
            lines.append(f"Publié : {published_at}")
            permalink = str(verification.get("permalink_url") or "")
            if permalink:
                lines.append(f"Lien : {permalink}")
        elif state == "published":
            lines.append("Statut : ⚠️ publication Facebook confirmée, mais relecture distante non vérifiée")
            lines.append(f"Publié : {published_at}")
            error = verification.get("error") if isinstance(verification.get("error"), dict) else execution.get("verification_error")
            if isinstance(error, dict) and error.get("code"):
                lines.append(f"Vérification : {error.get('code')}")
        elif state == "uncertain_external_result":
            lines.append("Statut : ❓ résultat Facebook incertain, réconciliation humaine requise")
        else:
            lines.append(f"Statut : ❌ publication Facebook non terminée ({state})")
    elif platform == "linkedin":
        if state == "provider_acknowledged":
            lines.append("Statut : ✅ création confirmée par LinkedIn (provider_acknowledged)")
            lines.append(f"Publié : {published_at}")
            lines.append("Relecture distante : non disponible avec l’accès LinkedIn actuel")
        else:
            lines.append(f"Statut : ❌ publication LinkedIn non terminée ({state})")
    else:
        raise ValueError("unsupported platform")

    remote_id = str(evidence.get("remote_post_id") or "")
    if remote_id:
        lines.append(f"ID distant : {remote_id}")
    return "\n".join(lines)


def should_send(config: dict[str, Any], record: dict[str, Any]) -> bool:
    if config.get("enabled") is not True:
        return False
    reports = config.get("publication_reports") if isinstance(config.get("publication_reports"), dict) else {}
    execution = record.get("execution") if isinstance(record.get("execution"), dict) else {}
    state = str(execution.get("state") or "unknown")
    if state in {"remote_verified", "provider_acknowledged"}:
        return reports.get("success", True) is not False
    if state == "uncertain_external_result":
        return reports.get("uncertain", True) is not False
    return reports.get("failure", True) is not False


def report_signature(platform: str, record: dict[str, Any]) -> str:
    execution = record.get("execution") if isinstance(record.get("execution"), dict) else {}
    evidence = execution.get("evidence") if isinstance(execution.get("evidence"), dict) else {}
    verification = execution.get("verification") if isinstance(execution.get("verification"), dict) else {}
    material = {
        "platform": platform,
        "post_id": (record.get("candidate") or {}).get("post_id") if isinstance(record.get("candidate"), dict) else None,
        "state": execution.get("state"),
        "publication_state": execution.get("publication_state"),
        "remote_post_id": evidence.get("remote_post_id"),
        "remote_media_id": evidence.get("remote_media_id"),
        "published_at": evidence.get("published_at"),
        "verification_state": verification.get("verification_state") or verification.get("state"),
        "verification_error": execution.get("verification_error"),
        "last_error": execution.get("last_error"),
    }
    encoded = json.dumps(material, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def already_reported(record: dict[str, Any], signature: str) -> bool:
    notifications = record.get("notifications") if isinstance(record.get("notifications"), dict) else {}
    telegram = notifications.get("telegram") if isinstance(notifications.get("telegram"), dict) else {}
    return telegram.get("state") == "sent" and telegram.get("reported_signature") == signature


def send_message(token: str, chat_id: str, text: str) -> tuple[bool, int | None, str | None]:
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = json.dumps({
        "chat_id": chat_id,
        "text": text,
        "disable_web_page_preview": True,
    }).encode("utf-8")
    request = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        return False, None, f"telegram_http_{exc.code}"
    except urllib.error.URLError:
        return False, None, "telegram_transport_error"
    except Exception:
        return False, None, "telegram_unexpected_error"
    if not isinstance(payload, dict) or payload.get("ok") is not True:
        return False, None, "telegram_api_rejected"
    result = payload.get("result") if isinstance(payload.get("result"), dict) else {}
    message_id = result.get("message_id")
    return True, int(message_id) if isinstance(message_id, int) else None, None


def persist_notification(
    record_path: Path,
    record: dict[str, Any],
    state: str,
    signature: str,
    message_id: int | None = None,
    error: str | None = None,
) -> None:
    notifications = record.setdefault("notifications", {})
    if not isinstance(notifications, dict):
        notifications = {}
        record["notifications"] = notifications
    telegram = notifications.setdefault("telegram", {})
    if not isinstance(telegram, dict):
        telegram = {}
        notifications["telegram"] = telegram
    telegram["last_attempt_at"] = utc_now()
    telegram["state"] = state
    telegram["reported_signature"] = signature
    if message_id is not None:
        telegram["message_id"] = message_id
    else:
        telegram.pop("message_id", None)
    if error:
        telegram["last_error"] = error
    else:
        telegram.pop("last_error", None)
    record_path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", required=True)
    parser.add_argument("--authorization", required=True)
    parser.add_argument("--platform", choices=["facebook", "linkedin"], required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    profile_path = Path(args.profile)
    record_path = Path(args.authorization)
    profile = load_json(profile_path)
    record = load_json(record_path)
    config = telegram_config(profile)

    if config.get("enabled") is not True:
        print("Telegram publication reports are disabled for the active user/project.")
        return 0
    if not should_send(config, record):
        print("Telegram report skipped by user publication-report preferences.")
        return 0

    signature = report_signature(args.platform, record)
    if already_reported(record, signature):
        print("Telegram publication report already sent for this exact publication state; skipping duplicate.")
        return 0

    chat_id = str(config.get("chat_id") or "").strip()
    secret_name = str(config.get("secret_name") or DEFAULT_SECRET_NAME)
    if secret_name != DEFAULT_SECRET_NAME:
        persist_notification(record_path, record, "failed", signature, error="unsupported_secret_name")
        print("Telegram notification configuration uses an unsupported secret name.")
        return 2
    token = os.environ.get(DEFAULT_SECRET_NAME, "").strip()
    if not chat_id or not token:
        persist_notification(record_path, record, "failed", signature, error="telegram_not_configured")
        print("Telegram notifications are enabled but chat_id or repository secret is missing.")
        return 2

    text = report_message(args.platform, record)
    if args.dry_run:
        print(text)
        return 0

    ok, message_id, error = send_message(token, chat_id, text)
    if not ok:
        persist_notification(record_path, record, "failed", signature, error=error or "telegram_send_failed")
        print(f"Telegram publication report failed: {error or 'telegram_send_failed'}")
        return 2
    persist_notification(record_path, record, "sent", signature, message_id=message_id)
    print("Telegram publication report sent.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
