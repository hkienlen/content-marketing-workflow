#!/usr/bin/env python3
"""Evaluate social connection health without handling raw provider credentials.

The script reads one user profile, optional non-secret SEO Workflow Bridge health
output, scheduled social post metadata, and exact scheduled-publication
authorization records. It updates only non-secret profile metadata when --write
is supplied.
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

HEALTHY = "healthy"
HEALTHY_NO_FIXED_EXPIRY = "healthy_no_fixed_expiry"
RENEWAL_30 = "renewal_due_30"
RENEWAL_14 = "renewal_due_14"
RENEWAL_7 = "renewal_required_7"
INVALID = "expired_or_invalid"

ACTIVE_EXECUTION_STATES = {"pending", "retryable_error"}
AUTHORIZED = "authorized_for_scheduled_publication"


def parse_dt(value: Any) -> Optional[datetime]:
    if value in (None, ""):
        return None
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(float(value), tz=timezone.utc)
    text = str(value).strip().strip('"').strip("'")
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    parsed = datetime.fromisoformat(text)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def iso(value: Optional[datetime]) -> Optional[str]:
    if value is None:
        return None
    return value.isoformat(timespec="seconds")


def active_project(profile: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
    project_id = str(profile.get("active_project_id") or "")
    projects = profile.get("projects")
    if not project_id or not isinstance(projects, dict) or project_id not in projects:
        raise ValueError("active_project_id must resolve to one project")
    project = projects[project_id]
    if not isinstance(project, dict):
        raise ValueError("active project must be an object")
    return project_id, project


def bridge_health_payload(raw: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if not raw:
        return {}
    if raw.get("ok") is True and isinstance(raw.get("result"), dict):
        return raw["result"]
    if isinstance(raw.get("linkedin"), dict) or isinstance(raw.get("facebook"), dict):
        return raw
    return {}


def expiry_for(platform: str, connection: Dict[str, Any]) -> Tuple[Optional[datetime], Optional[str]]:
    del platform
    credential = connection.get("credential")
    credential = credential if isinstance(credential, dict) else {}
    token_expiry = parse_dt(credential.get("token_expires_at"))
    data_expiry = parse_dt(credential.get("data_access_expires_at"))

    candidates: List[Tuple[datetime, str]] = []
    if token_expiry is not None:
        candidates.append((token_expiry, "token_expires_at"))
    if data_expiry is not None:
        candidates.append((data_expiry, "data_access_expires_at"))
    if not candidates:
        return None, None
    candidates.sort(key=lambda item: item[0])
    return candidates[0]


def severity_for(now: datetime, expiry: Optional[datetime], live_valid: Optional[bool]) -> Tuple[str, Optional[float]]:
    if live_valid is False:
        return INVALID, None if expiry is None else (expiry - now).total_seconds() / 86400.0
    if expiry is None:
        return HEALTHY_NO_FIXED_EXPIRY, None
    days = (expiry - now).total_seconds() / 86400.0
    if days <= 0:
        return INVALID, days
    if days <= 7:
        return RENEWAL_7, days
    if days <= 14:
        return RENEWAL_14, days
    if days <= 30:
        return RENEWAL_30, days
    return HEALTHY, days


def load_authorizations(root: Path, platform: str) -> Iterable[Tuple[str, Dict[str, Any]]]:
    directory = root / platform
    if not directory.exists():
        return []
    records: List[Tuple[str, Dict[str, Any]]] = []
    for path in sorted(directory.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(data, dict):
            records.append((path.name, data))
    return records


def frontmatter(text: str) -> str:
    if not text.startswith("---\n"):
        return ""
    end = text.find("\n---\n", 4)
    if end < 0:
        return ""
    return text[4:end]


def scalar_from_block(block: str, key: str) -> Optional[str]:
    match = re.search(rf"(?m)^  {re.escape(key)}:\s*(.+?)\s*$", block)
    if not match:
        return None
    return match.group(1).strip().strip('"').strip("'")


def scheduled_posts(posts_root: Path, platform: str) -> Iterable[Tuple[str, datetime]]:
    if not posts_root.exists():
        return []
    found: List[Tuple[str, datetime]] = []
    for path in sorted(posts_root.rglob("*.md")):
        if path.name in {"README.md", "series-plan.md"} or path.name.endswith(".checklist.md"):
            continue
        try:
            fm = frontmatter(path.read_text(encoding="utf-8"))
        except OSError:
            continue
        if not fm:
            continue
        id_match = re.search(r"(?m)^post_id:\s*([^\n]+)$", fm)
        if not id_match:
            continue
        post_id = id_match.group(1).strip().strip('"').strip("'")
        block_match = re.search(rf"(?ms)^{re.escape(platform)}:\n((?:  .*(?:\n|$))*)", fm)
        if not block_match:
            continue
        block = block_match.group(1)
        if scalar_from_block(block, "status") != "scheduled":
            continue
        planned = parse_dt(scalar_from_block(block, "planned_at"))
        if post_id and planned is not None:
            found.append((post_id, planned))
    return found


def scheduled_after_expiry(
    authorizations_root: Path,
    posts_root: Path,
    platform: str,
    expiry: Optional[datetime],
) -> List[str]:
    if expiry is None:
        return []
    blocked: set[str] = set()

    # Exact authorization records are checked because they represent executable
    # unattended publication state.
    for _name, record in load_authorizations(authorizations_root, platform):
        authorization = record.get("authorization")
        execution = record.get("execution")
        candidate = record.get("candidate")
        if not isinstance(authorization, dict) or not isinstance(execution, dict) or not isinstance(candidate, dict):
            continue
        if authorization.get("status") != AUTHORIZED:
            continue
        if execution.get("state") not in ACTIVE_EXECUTION_STATES:
            continue
        planned = parse_dt(candidate.get("planned_at") or authorization.get("planned_at"))
        if planned is None or planned < expiry:
            continue
        post_id = str(candidate.get("post_id") or authorization.get("post_id") or "").strip()
        if post_id:
            blocked.add(post_id)

    # Scheduled post metadata is checked independently so a future post is not
    # missed merely because its exact technical authorization has not yet been
    # materialized.
    for post_id, planned in scheduled_posts(posts_root, platform):
        if planned >= expiry:
            blocked.add(post_id)

    return sorted(blocked)


def bridge_platform_state(bridge: Dict[str, Any], platform: str) -> Dict[str, Any]:
    value = bridge.get(platform)
    return value if isinstance(value, dict) else {}


def maybe_refresh_linkedin_expiry(connection: Dict[str, Any], bridge_state: Dict[str, Any]) -> None:
    expires_at = bridge_state.get("expires_at")
    parsed = parse_dt(expires_at)
    if parsed is None:
        return
    credential = connection.setdefault("credential", {})
    if isinstance(credential, dict):
        credential["token_expires_at"] = iso(parsed)


def next_action(platform: str, status: str, blocked: List[str]) -> Optional[str]:
    if status in {RENEWAL_30, RENEWAL_14, RENEWAL_7, INVALID} or blocked:
        return "renew_linkedin_oauth" if platform == "linkedin" else "renew_facebook_page_credential"
    return None


def evaluate(
    profile: Dict[str, Any],
    bridge_raw: Optional[Dict[str, Any]],
    authorizations_root: Path,
    posts_root: Path,
    now: datetime,
) -> Dict[str, Any]:
    project_id, project = active_project(profile)
    social = project.get("social")
    if not isinstance(social, dict):
        raise ValueError("active project social configuration is missing")
    connections = social.get("connections")
    if not isinstance(connections, dict):
        raise ValueError("active project social connections are missing")

    bridge = bridge_health_payload(bridge_raw)
    report_connections: Dict[str, Any] = {}
    requires_attention = False

    for platform in ("linkedin", "facebook"):
        connection = connections.get(platform)
        if not isinstance(connection, dict) or not connection.get("enabled", True):
            continue
        provider_state = bridge_platform_state(bridge, platform)
        if platform == "linkedin":
            maybe_refresh_linkedin_expiry(connection, provider_state)

        raw_valid = provider_state.get("credential_live_valid")
        live_valid: Optional[bool] = raw_valid if isinstance(raw_valid, bool) else None

        credential = connection.setdefault("credential", {})
        if isinstance(credential, dict) and live_valid is not None:
            credential["last_observed_valid"] = live_valid
            credential["last_observed_at"] = iso(now)

        expiry, basis = expiry_for(platform, connection)
        status, days = severity_for(now, expiry, live_valid)
        blocked = scheduled_after_expiry(authorizations_root, posts_root, platform, expiry)
        if blocked and status in {HEALTHY, HEALTHY_NO_FIXED_EXPIRY}:
            status = RENEWAL_30

        health = connection.setdefault("health", {})
        if not isinstance(health, dict):
            health = {}
            connection["health"] = health
        health.update(
            {
                "status": status,
                "checked_at": iso(now),
                "credential_live_valid": live_valid,
                "expiry_basis": basis,
                "effective_expiry_at": iso(expiry),
                "days_until_expiry": None if days is None else round(days, 2),
                "scheduled_after_expiry": blocked,
                "next_action": next_action(platform, status, blocked),
            }
        )
        if provider_state:
            health["bridge_probe"] = {
                "available": provider_state.get("available", True),
                "enabled": provider_state.get("enabled"),
                "identity_matches": provider_state.get("identity_matches"),
                "provider_http_status": provider_state.get("provider_http_status"),
            }

        attention = status not in {HEALTHY, HEALTHY_NO_FIXED_EXPIRY} or bool(blocked)
        requires_attention = requires_attention or attention
        report_connections[platform] = {
            "status": status,
            "days_until_expiry": None if days is None else round(days, 2),
            "effective_expiry_at": iso(expiry),
            "expiry_basis": basis,
            "credential_live_valid": live_valid,
            "scheduled_after_expiry": blocked,
            "next_action": next_action(platform, status, blocked),
        }

    return {
        "schema_version": 1,
        "project_id": project_id,
        "checked_at": iso(now),
        "requires_attention": requires_attention,
        "connections": report_connections,
    }


def report_markdown(report: Dict[str, Any]) -> str:
    lines = ["# Social connection health", "", f"Checked: `{report.get('checked_at')}`", ""]
    for platform, state in report.get("connections", {}).items():
        lines.append(f"## {platform.capitalize()}")
        lines.append(f"- Status: `{state.get('status')}`")
        lines.append(f"- Effective expiry: `{state.get('effective_expiry_at')}`")
        lines.append(f"- Days until expiry: `{state.get('days_until_expiry')}`")
        lines.append(f"- Live credential valid: `{state.get('credential_live_valid')}`")
        blocked = state.get("scheduled_after_expiry") or []
        lines.append(f"- Scheduled after expiry: `{', '.join(blocked) if blocked else 'none'}`")
        if state.get("next_action"):
            lines.append(f"- Next action: `{state.get('next_action')}`")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", required=True)
    parser.add_argument("--authorizations-root", default="social/publication-authorizations")
    parser.add_argument("--posts-root", default="social")
    parser.add_argument("--bridge-response")
    parser.add_argument("--now")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--report-json")
    parser.add_argument("--report-markdown")
    args = parser.parse_args()

    profile_path = Path(args.profile)
    profile = json.loads(profile_path.read_text(encoding="utf-8"))
    bridge = None
    if args.bridge_response:
        bridge = json.loads(Path(args.bridge_response).read_text(encoding="utf-8"))
    now = parse_dt(args.now) if args.now else datetime.now(timezone.utc)
    if now is None:
        raise ValueError("invalid --now")

    report = evaluate(
        profile,
        bridge,
        Path(args.authorizations_root),
        Path(args.posts_root),
        now,
    )
    if args.write:
        profile_path.write_text(json.dumps(profile, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if args.report_json:
        Path(args.report_json).write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown = report_markdown(report)
    if args.report_markdown:
        Path(args.report_markdown).write_text(markdown, encoding="utf-8")
    else:
        print(markdown, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
