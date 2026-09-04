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

AUTH_DIR = Path("social/publication-authorizations/facebook")
AUTHORIZED = "authorized_for_scheduled_publication"
DUE_STATES = {"pending", "retryable_error"}
UNCERTAIN_ERRORS = {
    "facebook_page_publish_uncertain",
    "bridge_transport_uncertain",
    "bridge_response_invalid",
    "facebook_page_evidence_binding_mismatch",
}


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
        "post_id", "planned_at", "target_type", "page_id", "text_sha256", "image_sha256",
        "alt_text_sha256", "image_mime_type", "image_size_bytes", "delivery_provider", "delivery_file_id",
    ]
    return "\n".join(str(c[k]) for k in keys)


def validate(record: dict[str, Any]) -> None:
    if record.get("schema_version") != 1:
        raise ValueError("authorization schema_version must be 1")
    if not isinstance(record.get("bridge_connection_id"), str) or not record["bridge_connection_id"].strip():
        raise ValueError("bridge_connection_id is required")
    if not isinstance(record.get("facebook_connection_id"), str) or not record["facebook_connection_id"].strip():
        raise ValueError("facebook_connection_id is required")
    c = record.get("candidate")
    a = record.get("authorization")
    if not isinstance(c, dict) or not isinstance(a, dict):
        raise ValueError("candidate and authorization are required")
    if c.get("target_type") != "facebook_page" or a.get("target_type") != "facebook_page":
        raise ValueError("only facebook_page targets are supported")
    if a.get("status") != AUTHORIZED:
        raise ValueError("authorization is not active")
    if not re.fullmatch(r"[0-9]{5,32}", str(c.get("page_id", ""))):
        raise ValueError("page_id must be numeric")
    if sha(str(c["text"])) != c.get("text_sha256"):
        raise ValueError("text hash drift")
    if sha(str(c["alt_text"])) != c.get("alt_text_sha256"):
        raise ValueError("ALT hash drift")
    if sha(intent_material(c)) != c.get("intent_sha256"):
        raise ValueError("intent hash drift")
    bound = [
        "post_id", "planned_at", "target_type", "page_id", "text_sha256", "alt_text_sha256",
        "image_sha256", "image_mime_type", "image_size_bytes", "delivery_provider", "delivery_file_id",
        "intent_sha256",
    ]
    for key in bound:
        if str(c.get(key, "")) != str(a.get(key, "")):
            raise ValueError(f"authorization drift: {key}")
    parse_time(str(c["planned_at"]))
    parse_time(str(a["authorized_at"]))


def success_evidence_error(record: dict[str, Any], evidence: dict[str, Any]) -> dict[str, str] | None:
    c = record["candidate"]
    a = record["authorization"]
    expected = {
        "post_id": c["post_id"],
        "authorization_id": a["authorization_id"],
        "target_type": c["target_type"],
        "page_id": c["page_id"],
        "planned_at": c["planned_at"],
        "text_sha256": c["text_sha256"],
        "image_sha256": c["image_sha256"],
        "alt_text_sha256": c["alt_text_sha256"],
        "delivery_provider": c["delivery_provider"],
        "delivery_file_id": c["delivery_file_id"],
        "intent_sha256": c["intent_sha256"],
    }
    for key, value in expected.items():
        if str(evidence.get(key, "")) != str(value):
            return {
                "code": "facebook_page_evidence_binding_mismatch",
                "message": f"Bridge publication evidence does not match the exact current authorization: {key}",
            }
    remote_post_id = str(evidence.get("remote_post_id", ""))
    remote_media_id = str(evidence.get("remote_media_id", ""))
    try:
        published_at = int(evidence.get("published_at", 0))
    except (TypeError, ValueError):
        published_at = 0
    if not remote_post_id or not remote_media_id or published_at <= 0:
        return {
            "code": "facebook_page_evidence_binding_mismatch",
            "message": "Bridge publication evidence is missing definitive remote IDs or published_at.",
        }
    return None


def list_due(now: dt.datetime) -> list[Path]:
    due: list[Path] = []
    if not AUTH_DIR.is_dir():
        return due
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
        "request_id": f"facebook-page-scheduled-{post_id}-{now.strftime('%Y%m%dT%H%M%SZ')}-{secrets.token_hex(4)}",
        "connection_id": record["bridge_connection_id"],
        "operation": "facebook_page_publish_authorized",
        "issued_at": now.isoformat().replace("+00:00", "Z"),
        "payload": {
            "schema_version": 1,
            "candidate": record["candidate"],
            "authorization": record["authorization"],
        },
    }


def build_verification_request(path: Path) -> dict[str, Any]:
    record = json.loads(path.read_text(encoding="utf-8"))
    validate(record)
    execution = record.get("execution")
    evidence = execution.get("evidence") if isinstance(execution, dict) else None
    if not isinstance(evidence, dict) or evidence.get("published") is not True:
        raise ValueError("definitive publication evidence is required before remote verification")
    binding_error = success_evidence_error(record, evidence)
    if binding_error is not None:
        raise ValueError(binding_error["message"])
    remote_post_id = str(evidence.get("remote_post_id", ""))
    remote_media_id = str(evidence.get("remote_media_id", ""))
    c = record["candidate"]
    now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0)
    return {
        "schema_version": 1,
        "request_id": f"facebook-page-verify-{c['post_id']}-{now.strftime('%Y%m%dT%H%M%SZ')}-{secrets.token_hex(4)}",
        "connection_id": record["bridge_connection_id"],
        "operation": "facebook_page_verify_publication",
        "issued_at": now.isoformat().replace("+00:00", "Z"),
        "payload": {
            "post_id": c["post_id"],
            "authorization_id": record["authorization"]["authorization_id"],
            "page_id": c["page_id"],
            "remote_post_id": remote_post_id,
            "remote_media_id": remote_media_id,
            "text": c["text"],
            "text_sha256": c["text_sha256"],
        },
    }


def update_post_frontmatter(post_path: Path, evidence: dict[str, Any]) -> None:
    text = post_path.read_text(encoding="utf-8")
    remote_post = str(evidence.get("remote_post_id", ""))
    remote_media = str(evidence.get("remote_media_id", ""))
    published_at = int(evidence.get("published_at", 0))
    if not remote_post or not remote_media or published_at <= 0:
        raise ValueError("publication evidence is incomplete")
    published_iso = dt.datetime.fromtimestamp(published_at, dt.timezone.utc).isoformat().replace("+00:00", "Z")
    pattern = re.compile(
        r"facebook:\n  status: scheduled\n  planned_at: ([^\n]+)\n  target_type: facebook_page\n  connection_id: ([^\n]+)"
        r"(?:\n  published_at: [^\n]+)?(?:\n  remote_post_id: [^\n]+)?(?:\n  remote_media_id: [^\n]+)?"
    )
    replacement = (
        "facebook:\n  status: published\n  planned_at: \\1\n  target_type: facebook_page\n  connection_id: \\2"
        f"\n  published_at: {published_iso}\n  remote_post_id: {remote_post}\n  remote_media_id: {remote_media}"
    )
    updated, count = pattern.subn(replacement, text, count=1)
    if count != 1:
        if "facebook:\n  status: published" in text and remote_post in text:
            return
        raise ValueError("expected scheduled Facebook Page frontmatter block not found")
    post_path.write_text(updated, encoding="utf-8")


def update_post_verification_frontmatter(post_path: Path, verification: dict[str, Any]) -> None:
    text = post_path.read_text(encoding="utf-8")
    checked_at = int(verification.get("checked_at", 0))
    if checked_at <= 0:
        raise ValueError("remote verification timestamp is missing")
    checked_iso = dt.datetime.fromtimestamp(checked_at, dt.timezone.utc).isoformat().replace("+00:00", "Z")
    permalink = str(verification.get("permalink_url") or "")
    pattern = re.compile(
        r"facebook:\n  status: published\n  planned_at: ([^\n]+)\n  target_type: facebook_page\n  connection_id: ([^\n]+)"
        r"\n  published_at: ([^\n]+)\n  remote_post_id: ([^\n]+)\n  remote_media_id: ([^\n]+)"
        r"(?:\n  verification_state: [^\n]+)?(?:\n  remote_verified_at: [^\n]+)?(?:\n  permalink_url: [^\n]+)?"
    )
    replacement = (
        "facebook:\n  status: published\n  planned_at: \\1\n  target_type: facebook_page\n  connection_id: \\2"
        "\n  published_at: \\3\n  remote_post_id: \\4\n  remote_media_id: \\5"
        f"\n  verification_state: remote_verified\n  remote_verified_at: {checked_iso}"
    )
    if permalink:
        replacement += f"\n  permalink_url: {permalink}"
    updated, count = pattern.subn(replacement, text, count=1)
    if count != 1:
        if "verification_state: remote_verified" in text:
            return
        raise ValueError("expected published Facebook Page frontmatter block not found")
    post_path.write_text(updated, encoding="utf-8")


def apply_response(path: Path, response_path: Path) -> int:
    record = json.loads(path.read_text(encoding="utf-8"))
    response = json.loads(response_path.read_text(encoding="utf-8"))
    execution = record.setdefault("execution", {})
    execution["attempts"] = int(execution.get("attempts", 0)) + 1
    execution["last_attempt_at"] = utc_now()
    if response.get("ok") is True and isinstance(response.get("result"), dict) and response["result"].get("published") is True:
        binding_error = success_evidence_error(record, response["result"])
        if binding_error is not None:
            execution["state"] = "uncertain_external_result"
            execution["last_error"] = binding_error
            execution["requires_human_reconciliation"] = True
            path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            return 3
        execution["state"] = "published"
        execution["publication_state"] = "published"
        execution["evidence"] = response["result"]
        execution["verification"] = {"state": "pending"}
        execution.pop("last_error", None)
        execution.pop("requires_human_reconciliation", None)
        update_post_frontmatter(Path(record["post_file"]), response["result"])
        path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return 0

    error = response.get("error") if isinstance(response.get("error"), dict) else {"code": "unknown", "message": "Unknown relay response"}
    execution["last_error"] = error
    if str(error.get("code", "")) in UNCERTAIN_ERRORS:
        execution["state"] = "uncertain_external_result"
        execution["requires_human_reconciliation"] = True
        rc = 3
    else:
        execution["state"] = "retryable_error"
        execution.pop("requires_human_reconciliation", None)
        rc = 2
    path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return rc


def apply_verification_response(path: Path, response_path: Path) -> int:
    record = json.loads(path.read_text(encoding="utf-8"))
    response = json.loads(response_path.read_text(encoding="utf-8"))
    execution = record.setdefault("execution", {})
    if execution.get("publication_state") != "published" and execution.get("state") not in {"published", "remote_verified"}:
        raise ValueError("publication must be definitive before verification state can be applied")
    if response.get("ok") is True and isinstance(response.get("result"), dict) and response["result"].get("verification_state") == "remote_verified":
        result = response["result"]
        c = record["candidate"]
        a = record["authorization"]
        for key, expected in {
            "post_id": c["post_id"],
            "authorization_id": a["authorization_id"],
            "page_id": c["page_id"],
        }.items():
            if str(result.get(key, "")) != str(expected):
                raise ValueError(f"verification evidence does not match exact authorization: {key}")
        publication_evidence = execution.get("evidence") if isinstance(execution.get("evidence"), dict) else {}
        for key in ("remote_post_id", "remote_media_id"):
            if str(result.get(key, "")) != str(publication_evidence.get(key, "")):
                raise ValueError(f"verification evidence does not match publication evidence: {key}")
        execution["state"] = "remote_verified"
        execution["publication_state"] = "published"
        execution["verification"] = result
        execution.pop("verification_error", None)
        update_post_verification_frontmatter(Path(record["post_file"]), result)
        path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return 0

    error = response.get("error") if isinstance(response.get("error"), dict) else {"code": "unknown", "message": "Unknown verification response"}
    execution["state"] = "published"
    execution["publication_state"] = "published"
    execution["verification"] = {
        "state": "verification_failed",
        "checked_at": utc_now(),
        "error": error,
    }
    execution["verification_error"] = error
    path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 4


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
    p_verify_req = sub.add_parser("verify-request")
    p_verify_req.add_argument("--authorization", required=True)
    p_verify_req.add_argument("--out", required=True)
    p_verify_apply = sub.add_parser("apply-verification")
    p_verify_apply.add_argument("--authorization", required=True)
    p_verify_apply.add_argument("--response", required=True)
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
        return apply_response(Path(args.authorization), Path(args.response))
    if args.cmd == "verify-request":
        request = build_verification_request(Path(args.authorization))
        Path(args.out).write_text(json.dumps(request, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
        return 0
    if args.cmd == "apply-verification":
        return apply_verification_response(Path(args.authorization), Path(args.response))
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
