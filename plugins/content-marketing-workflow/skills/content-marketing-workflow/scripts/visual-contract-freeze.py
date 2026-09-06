#!/usr/bin/env python3
"""Freeze or verify one effective visual contract with a deterministic SHA-256 revision.

The hash covers the complete contract payload except ``contract_revision`` itself,
using UTF-8 JSON with sorted keys and compact separators. The resulting revision
is stored as ``sha256:<64 lowercase hex>``.

This helper is credential-free and does not mutate project state. Owning article
or social workflows persist the frozen JSON/revision with durable review/final
state before calling media ``verified_final``.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

REVISION_PREFIX = "sha256:"
REQUIRED_FIELDS = {
    "content_kind",
    "source_policy",
    "applied_user_directives",
    "logo_application",
    "generic_defaults_applied",
}
LOGO_APPLICATIONS = {"always", "auto", "never"}
CONTENT_KINDS = {"article", "social"}


class VisualContractError(ValueError):
    """Raised when an effective visual contract is invalid or revision drifts."""


def _as_mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise VisualContractError(f"{label} must be an object")
    return value


def _validate_string_list(value: Any, label: str) -> list[str]:
    if not isinstance(value, list):
        raise VisualContractError(f"{label} must be an array")
    result: list[str] = []
    for index, item in enumerate(value):
        if not isinstance(item, str) or not item.strip():
            raise VisualContractError(f"{label}[{index}] must be a non-empty string")
        result.append(item)
    return result


def _validate_contract_payload(payload: Mapping[str, Any]) -> None:
    missing = sorted(REQUIRED_FIELDS - set(payload))
    if missing:
        raise VisualContractError(
            "effective visual contract missing required fields: " + ", ".join(missing)
        )

    if payload.get("content_kind") not in CONTENT_KINDS:
        raise VisualContractError("content_kind must be article or social")
    if payload.get("logo_application") not in LOGO_APPLICATIONS:
        raise VisualContractError("logo_application must be always, auto or never")

    _as_mapping(payload.get("source_policy"), "source_policy")

    directives = _as_mapping(
        payload.get("applied_user_directives"), "applied_user_directives"
    )
    for key in ("project_global", "channel", "content_local"):
        _validate_string_list(directives.get(key, []), f"applied_user_directives.{key}")

    _validate_string_list(
        payload.get("generic_defaults_applied"), "generic_defaults_applied"
    )


def canonical_contract_bytes(contract: Mapping[str, Any]) -> bytes:
    """Return canonical bytes used for the revision hash."""
    payload = dict(_as_mapping(contract, "effective visual contract"))
    payload.pop("contract_revision", None)
    _validate_contract_payload(payload)
    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def compute_revision(contract: Mapping[str, Any]) -> str:
    digest = hashlib.sha256(canonical_contract_bytes(contract)).hexdigest()
    return REVISION_PREFIX + digest


def freeze_contract(contract: Mapping[str, Any]) -> dict[str, Any]:
    payload = dict(_as_mapping(contract, "effective visual contract"))
    payload.pop("contract_revision", None)
    revision = compute_revision(payload)
    payload["contract_revision"] = revision
    return payload


def verify_contract(contract: Mapping[str, Any]) -> dict[str, Any]:
    current = contract.get("contract_revision")
    if not isinstance(current, str) or not current.startswith(REVISION_PREFIX):
        raise VisualContractError("contract_revision is missing or invalid")
    expected = compute_revision(contract)
    if current != expected:
        raise VisualContractError(
            f"contract_revision drift: stored {current}, computed {expected}"
        )
    return dict(contract)


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Verify an existing contract_revision instead of replacing it.",
    )
    args = parser.parse_args()

    contract = _as_mapping(_read_json(args.input), "effective visual contract")
    result = verify_contract(contract) if args.verify else freeze_contract(contract)

    if args.output:
        _write_json(args.output, result)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
