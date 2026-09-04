#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import secrets
from pathlib import Path
from typing import Any

AUTH_DIR = Path("social/publication-authorizations/linkedin")
AUTHORIZED = "authorized_for_scheduled_publication"
DUE_STATES = {"pending", "retryable_error"}


def parse_time(value: str) -> dt.datetime:
    parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("timestamp must include timezone")
    return parsed


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def intent_material(c: dict[str, Any]) -> str:
    keys = [
        "post_id", "planned_at", "author_urn", "text_sha256", "image_sha256",
        "alt_text_sha256", "image_mime_type", "image_size_bytes",
        "delivery_provider", "delivery_file_id",
    ]
    return "\n".join(str(c[k]) for k in keys)


def validate(record: dict[str, Any]) -> None:
    if record.get("schema_version") != 1:
        raise ValueError("authorization schema_version must be 1")
    c = record.get("candidate")
    a = record.get("authorization")
    if not isinstance(c, dict) or not isinstance(a, dict):
        raise ValueError("candidate and authorization are required")
    if a.get("status") != AUTHORIZED:
        raise ValueError("authorization is not active")
    connection_id = record.get("connection_id")
    if not isinstance(connection_id, str) or not connection_id.strip():
        raise ValueError("connection_id is required")
    if sha(str(c["text"])) != c.get("text_sha256"):
        raise ValueError("text hash drift")
    if sha(str(c["alt_text"])) != c.get("alt_text_sha256"):
        raise ValueError("ALT hash drift")
    if sha(intent_material(c)) != c.get("intent_sha256"):
        raise ValueError("intent hash drift")
    bound = [
        "post_id", "planned_at", "author_urn", "text_sha256", "alt_text_sha256",
        "image_sha256", "image_mime_type", "image_size_bytes", "delivery_provider",
        "delivery_file_id", "intent_sha256",
    ]
    for key in bound:
        if str(c.get(key, "")) != str(a.get(key, "")):
            raise ValueError(f"authorization drift: {key}")
    parse_time(str(c["planned_at"]))
    parse_time(str(a["authorized_at"]))


def list_due(now: dt.datetime) -> list[Path]:
    due: list[Path] = []
    for path in sorted(AUTH_DIR.glob("*.json")):
        record = json.loads(path.read_text(encoding="utf-8"))
        try:
            validate(record)
        except Exception as exc:
            print(f"SKIP invalid {path}: {exc}")
            continue
        state = str(record.get("execution", {}).get("state", "pending"))
        if state not in DUE_STATES:
            continue
        planned = parse_time(record["candidate"]["planned_at"])
        if planned <= now < planned + dt.timedelta(hours=24):
            due.append(path)
    return due


def build_request(path: Path) -> dict[str, Any]:
    record = json.loads(path.read_text(encoding="utf-8"))
    validate(record)
    now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0)
    post_id = record["candidate"]["post_id"]
    return {
        "schema_version": 1,
        "request_id": f"linkedin-scheduled-{post_id}-{now.strftime('%Y%m%dT%H%M%SZ')}-{secrets.token_hex(4)}",
        "connection_id": record["connection_id"],
        "operation": "linkedin_publish_authorized",
        "issued_at": now.isoformat().replace("+00:00", "Z"),
        "payload": {
            "schema_version": 2,
            "candidate": record["candidate"],
            "authorization": record["authorization"],
        },
    }


def update_post_frontmatter(post_path: Path, evidence: dict[str, Any]) -> None:
    text = post_path.read_text(encoding="utf-8")
    remote = str(evidence.get("remote_post_id", ""))
    published_at = int(evidence.get("published_at", 0))
    if not remote or published_at <= 0:
        raise ValueError("publication evidence is incomplete")
    published_iso = dt.datetime.fromtimestamp(published_at, dt.timezone.utc).isoformat().replace("+00:00", "Z")
    pattern = re.compile(r"linkedin:\n  status: scheduled\n  planned_at: ([^\n]+)(?:\n  published_at: [^\n]+)?(?:\n  remote_post_id: [^\n]+)?")
    replacement = (
        "linkedin:\n  status: published\n  planned_at: \\1"
        f"\n  published_at: {published_iso}\n  remote_post_id: {remote}"
        "\n  verification_state: provider_acknowledged"
        "\n  verification_note: provider_creation_acknowledged_readback_unavailable_with_current_access"
    )
    updated, count = pattern.subn(replacement, text, count=1)
    if count != 1:
        if "linkedin:\n  status: published" in text and "verification_state: provider_acknowledged" in text and remote in text:
            return
        raise ValueError("expected scheduled LinkedIn frontmatter block not found")
    post_path.write_text(updated, encoding="utf-8")


def apply_response(path: Path, response_path: Path) -> bool:
    record = json.loads(path.read_text(encoding="utf-8"))
    response = json.loads(response_path.read_text(encoding="utf-8"))
    execution = record.setdefault("execution", {})
    execution["attempts"] = int(execution.get("attempts", 0)) + 1
    execution["last_attempt_at"] = utc_now()
    if response.get("ok") is True and isinstance(response.get("result"), dict) and response["result"].get("published") is True:
        execution["state"] = "provider_acknowledged"
        execution["publication_state"] = "published"
        execution["evidence"] = response["result"]
        execution["verification"] = {
            "state": "provider_acknowledged",
            "checked_at": utc_now(),
            "readback_available": False,
            "reason": "current_connection_does_not_have_member_social_readback_access",
        }
        execution.pop("last_error", None)
        update_post_frontmatter(Path(record["post_file"]), response["result"])
        path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return True
    execution["state"] = "retryable_error"
    execution["last_error"] = response.get("error", {"code": "unknown", "message": "Unknown relay response"})
    path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return False


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)
    p_due = sub.add_parser("due")
    p_due.add_argument("--now")
    p_req = sub.add_parser("request")
    p_req.add_argument("--authorization", required=True)
    p_req.add_argument("--out", required=True)
    p_apply = sub.add_parser("apply")
    p_apply.add_argument("--authorization", required=True)
    p_apply.add_argument("--response", required=True)
    args = parser.parse_args()

    if args.cmd == "due":
        now = parse_time(args.now) if args.now else dt.datetime.now(dt.timezone.utc)
        for path in list_due(now):
            print(path)
        return 0
    if args.cmd == "request":
        request = build_request(Path(args.authorization))
        Path(args.out).write_text(json.dumps(request, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
        return 0
    if args.cmd == "apply":
        return 0 if apply_response(Path(args.authorization), Path(args.response)) else 2
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
