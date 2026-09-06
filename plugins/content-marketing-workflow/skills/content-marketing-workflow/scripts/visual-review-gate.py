#!/usr/bin/env python3
"""Validate that a durable visual review package is actually review-ready.

The primary hard gate implemented here is for `logo_application=always`:
reviewable A/B/C candidates must be clean-base derivatives composed with the exact
verified official logo before they can be presented as selectable human-review
candidates.

This helper validates evidence; it does not inspect pixels itself. The owning visual
workflow must truthfully record base-logo inspection results after visual inspection.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

SHA256_RE = re.compile(r"^[a-f0-9]{64}$")
REVISION_RE = re.compile(r"^sha256:[a-f0-9]{64}$")


class VisualReviewGateError(ValueError):
    """Raised when a visual package must not enter durable human review."""


def _sha(value: Any, field: str) -> str:
    if not isinstance(value, str) or not SHA256_RE.fullmatch(value):
        raise VisualReviewGateError(f"{field} must be a 64-character lowercase SHA-256")
    return value


def _verify_contract_revision(contract: dict[str, Any]) -> str:
    revision = contract.get("contract_revision")
    if not isinstance(revision, str) or not REVISION_RE.fullmatch(revision):
        raise VisualReviewGateError("effective contract has no valid contract_revision")

    payload = dict(contract)
    payload.pop("contract_revision", None)
    canonical = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    expected = "sha256:" + hashlib.sha256(canonical).hexdigest()
    if revision != expected:
        raise VisualReviewGateError(
            f"effective contract revision mismatch: expected {expected}, got {revision}"
        )
    return revision


def validate_review_package(package: dict[str, Any]) -> dict[str, Any]:
    contract = package.get("effective_contract")
    candidates = package.get("candidates")

    if not isinstance(contract, dict):
        raise VisualReviewGateError("effective_contract must be an object")
    if not isinstance(candidates, list):
        raise VisualReviewGateError("candidates must be an array")

    revision = _verify_contract_revision(contract)
    logo_application = contract.get("logo_application")

    if package.get("workflow_mode") == "generated_or_materially_transformed" and len(candidates) != 3:
        raise VisualReviewGateError(
            "generated/materially transformed durable review must contain exactly three candidates"
        )

    expected_logo_sha = None
    if logo_application == "always":
        identity = contract.get("logo_asset_identity")
        if not isinstance(identity, dict):
            raise VisualReviewGateError(
                "logo_application=always requires logo_asset_identity in the effective contract"
            )
        expected_logo_sha = _sha(identity.get("sha256"), "logo_asset_identity.sha256")

    ids: list[str] = []
    for index, candidate in enumerate(candidates):
        if not isinstance(candidate, dict):
            raise VisualReviewGateError(f"candidate[{index}] must be an object")

        candidate_id = candidate.get("candidate_id")
        if not isinstance(candidate_id, str) or not candidate_id.strip():
            raise VisualReviewGateError(f"candidate[{index}].candidate_id is required")
        if candidate_id in ids:
            raise VisualReviewGateError(f"duplicate candidate_id: {candidate_id}")
        ids.append(candidate_id)

        if candidate.get("contract_revision") != revision:
            raise VisualReviewGateError(
                f"candidate {candidate_id} is not bound to the effective contract revision"
            )

        base_asset = candidate.get("base_asset")
        review_asset = candidate.get("review_asset")
        if not isinstance(base_asset, dict) or not isinstance(review_asset, dict):
            raise VisualReviewGateError(
                f"candidate {candidate_id} requires base_asset and review_asset evidence"
            )
        base_sha = _sha(base_asset.get("sha256"), f"candidate {candidate_id} base_asset.sha256")
        review_sha = _sha(review_asset.get("sha256"), f"candidate {candidate_id} review_asset.sha256")

        inspection = candidate.get("base_logo_inspection")
        if not isinstance(inspection, dict) or inspection.get("status") != "clear":
            raise VisualReviewGateError(
                f"candidate {candidate_id} base is not verified clear of generated/unverified project branding"
            )

        if logo_application == "always":
            manifest = candidate.get("logo_composition_manifest")
            if not isinstance(manifest, dict):
                raise VisualReviewGateError(
                    f"candidate {candidate_id} requires deterministic official-logo composition evidence"
                )
            manifest_base = manifest.get("base")
            manifest_logo = manifest.get("official_logo")
            manifest_output = manifest.get("output")
            if not all(isinstance(item, dict) for item in (manifest_base, manifest_logo, manifest_output)):
                raise VisualReviewGateError(
                    f"candidate {candidate_id} composition manifest is incomplete"
                )
            if _sha(manifest_base.get("sha256"), "composition base.sha256") != base_sha:
                raise VisualReviewGateError(
                    f"candidate {candidate_id} composition base hash does not match base asset"
                )
            if _sha(manifest_logo.get("sha256"), "composition official_logo.sha256") != expected_logo_sha:
                raise VisualReviewGateError(
                    f"candidate {candidate_id} does not use the effective official logo SHA-256"
                )
            if _sha(manifest_output.get("sha256"), "composition output.sha256") != review_sha:
                raise VisualReviewGateError(
                    f"candidate {candidate_id} review asset is not the deterministic composition output"
                )
            if review_sha == base_sha:
                raise VisualReviewGateError(
                    f"candidate {candidate_id} branded review output unexpectedly equals its clean base"
                )

    return {
        "review_ready": True,
        "contract_revision": revision,
        "candidate_ids": ids,
        "logo_application": logo_application,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    args = parser.parse_args()

    package = json.loads(args.input.read_text(encoding="utf-8"))
    result = validate_review_package(package)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
