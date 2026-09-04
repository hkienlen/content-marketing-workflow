#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

SECRET_NAME = "TELEGRAM_BOT_TOKEN"


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def api_call(token: str, method: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    url = f"https://api.telegram.org/bot{token}/{method}"
    data = None
    headers: dict[str, str] = {}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=data, headers=headers, method="POST" if data is not None else "GET")
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            body = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"telegram_http_{exc.code}") from None
    except urllib.error.URLError:
        raise RuntimeError("telegram_transport_error") from None
    if not isinstance(body, dict) or body.get("ok") is not True:
        raise RuntimeError("telegram_api_rejected")
    return body


def load_profile(path: Path) -> tuple[dict[str, Any], str, dict[str, Any]]:
    profile = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(profile, dict):
        raise ValueError("profile must be a JSON object")
    project_id = profile.get("active_project_id")
    projects = profile.get("projects")
    if not isinstance(project_id, str) or not isinstance(projects, dict) or not isinstance(projects.get(project_id), dict):
        raise ValueError("active project is missing from profile")
    return profile, project_id, projects[project_id]


def candidate_chats(updates: dict[str, Any]) -> list[dict[str, str]]:
    result = updates.get("result") if isinstance(updates.get("result"), list) else []
    found: dict[str, dict[str, str]] = {}
    for update in result:
        if not isinstance(update, dict):
            continue
        message = update.get("message") if isinstance(update.get("message"), dict) else update.get("my_chat_member")
        if not isinstance(message, dict):
            continue
        chat = message.get("chat") if isinstance(message.get("chat"), dict) else {}
        chat_id = chat.get("id")
        if not isinstance(chat_id, int):
            continue
        title = str(chat.get("title") or "").strip()
        first = str(chat.get("first_name") or "").strip()
        last = str(chat.get("last_name") or "").strip()
        username = str(chat.get("username") or "").strip()
        label = title or " ".join(part for part in (first, last) if part) or (f"@{username}" if username else "Telegram chat")
        found[str(chat_id)] = {
            "chat_id": str(chat_id),
            "type": str(chat.get("type") or "unknown"),
            "label": label,
            "username": username,
        }
    return list(found.values())


def write_profile(path: Path, profile: dict[str, Any]) -> None:
    path.write_text(json.dumps(profile, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", required=True)
    parser.add_argument("--mode", choices=["discover", "verify", "disable"], required=True)
    parser.add_argument("--chat-id")
    args = parser.parse_args()

    profile_path = Path(args.profile)
    profile, project_id, project = load_profile(profile_path)
    notifications = project.setdefault("notifications", {})
    if not isinstance(notifications, dict):
        raise ValueError("project.notifications must be an object")
    telegram = notifications.setdefault("telegram", {})
    if not isinstance(telegram, dict):
        raise ValueError("project.notifications.telegram must be an object")

    if args.mode == "disable":
        telegram["enabled"] = False
        telegram["disabled_at"] = utc_now()
        write_profile(profile_path, profile)
        print("Telegram publication notifications disabled. Existing bot/chat metadata was retained for easy re-enable.")
        return 0

    token = os.environ.get(SECRET_NAME, "").strip()
    if not token:
        raise SystemExit(f"Missing GitHub Actions repository secret {SECRET_NAME}")

    me = api_call(token, "getMe")
    bot = me.get("result") if isinstance(me.get("result"), dict) else {}
    bot_username = str(bot.get("username") or "").strip()
    if not bot_username:
        raise SystemExit("Telegram getMe returned no bot username")

    if args.mode == "discover":
        updates = api_call(token, "getUpdates")
        chats = candidate_chats(updates)
        print(f"Bot verified: @{bot_username}")
        if not chats:
            print("No candidate chat found. Open the bot in Telegram, press Start or send /start, then rerun discover.")
            return 4
        print("Candidate chats:")
        for chat in chats:
            username = f" @{chat['username']}" if chat.get("username") else ""
            print(f"- chat_id={chat['chat_id']} type={chat['type']} label={chat['label']}{username}")
        return 0

    chat_id = str(args.chat_id or "").strip()
    if not chat_id or not chat_id.lstrip("-").isdigit():
        raise SystemExit("verify mode requires a numeric --chat-id")
    chat = api_call(token, "getChat", {"chat_id": chat_id})
    chat_result = chat.get("result") if isinstance(chat.get("result"), dict) else {}
    returned_id = str(chat_result.get("id") or "")
    if returned_id != chat_id:
        raise SystemExit("Telegram getChat returned a different chat ID")

    test = api_call(token, "sendMessage", {
        "chat_id": chat_id,
        "text": "✅ Notifications de publication configurées. Ce message confirme que le bot Telegram peut envoyer les rapports de publication.",
        "disable_web_page_preview": True,
    })
    message = test.get("result") if isinstance(test.get("result"), dict) else {}
    if not isinstance(message.get("message_id"), int):
        raise SystemExit("Telegram test message returned no message_id")

    now = utc_now()
    telegram.update({
        "enabled": True,
        "setup_status": "verified",
        "chat_id": chat_id,
        "bot_username": bot_username,
        "secret_name": SECRET_NAME,
        "configured_at": telegram.get("configured_at") or now,
        "last_verified_at": now,
    })
    telegram.pop("disabled_at", None)
    reports = telegram.setdefault("publication_reports", {})
    if not isinstance(reports, dict):
        reports = {}
        telegram["publication_reports"] = reports
    reports.setdefault("success", True)
    reports.setdefault("failure", True)
    reports.setdefault("uncertain", True)
    write_profile(profile_path, profile)
    print(f"Telegram notifications verified for @{bot_username}, chat_id={chat_id}, project={project_id}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
