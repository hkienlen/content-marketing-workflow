#!/usr/bin/env python3
"""Build and validate brand-isolated image-generation briefs.

Generated social visuals that will later receive official branding must not send the
full effective visual contract, logo identity, provider IDs, hashes, or placement
instructions to the image model. This helper derives a minimal creative brief for
base generation and keeps brand composition as a separate deterministic stage.
"""

from __future__ import annotations

import argparse
import json
import re
from typing import Any

REVISION_RE = re.compile(r"^sha256:[a-f0-9]{64}$")
FORBIDDEN_CREATIVE_PATTERNS = (
    re.compile(r"\blogo\b", re.IGNORECASE),
    re.compile(r"\bsha-?256\b", re.IGNORECASE),
    re.compile(r"\basset[_ -]?id\b", re.IGNORECASE),
    re.compile(r"\bbrand signature\b", re.IGNORECASE),
    re.compile(r"\bsignature de marque\b", re.IGNORECASE),
)
FORBIDDEN_BRIEF_KEYS = {
    "logo_application",
    "logo_asset",
    "logo_asset_identity",
    "logo_asset_id",
    "logo_provider",
    "logo_sha256",
    "official_logo",
    "brand_asset",
}


class BaseGenerationBriefError(ValueError):
    """Raised when generator input leaks brand-composition data."""


def _walk_keys(value: Any):
    if isinstance(value, dict):
        for key, nested in value.items():
            yield str(key)
            yield from _walk_keys(nested)
    elif isinstance(value, list):
        for nested in value:
            yield from _walk_keys(nested)


def validate_base_generation_brief(brief: dict[str, Any]) -> dict[str, Any]:
    if brief.get("content_kind") not in {"article", "social"}:
        raise BaseGenerationBriefError("content_kind must be article or social")
    revision = brief.get("contract_revision")
    if not isinstance(revision, str) or not REVISION_RE.fullmatch(revision):
        raise BaseGenerationBriefError("contract_revision must be sha256:<64 lowercase hex>")
    candidate_id = brief.get("candidate_id")
    if not isinstance(candidate_id, str) or not candidate_id.strip():
        raise BaseGenerationBriefError("candidate_id is required")
    prompt = brief.get("creative_prompt")
    if not isinstance(prompt, str) or not prompt.strip():
        raise BaseGenerationBriefError("creative_prompt is required")
    for pattern in FORBIDDEN_CREATIVE_PATTERNS:
        if pattern.search(prompt):
            raise BaseGenerationBriefError(
                "creative_prompt contains brand-composition instructions or identity data"
            )
    leaked = sorted(set(_walk_keys(brief)) & FORBIDDEN_BRIEF_KEYS)
    if leaked:
        raise BaseGenerationBriefError(
            "base-generation brief contains forbidden brand-composition keys: "
            + ", ".join(leaked)
        )
    constraints = brief.get("generator_constraints")
    if not isinstance(constraints, dict):
        raise BaseGenerationBriefError("generator_constraints is required")
    if constraints.get("project_branding") != "exclude":
        raise BaseGenerationBriefError("project_branding must be exclude")
    if constraints.get("watermarks") != "exclude":
        raise BaseGenerationBriefError("watermarks must be exclude")
    return brief


def build_base_generation_brief(
    effective_contract: dict[str, Any],
    candidate_id: str,
    creative_prompt: str,
    reserved_composition_space: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Derive only generator-safe fields from a frozen effective contract."""
    brief: dict[str, Any] = {
        "content_kind": effective_contract.get("content_kind"),
        "contract_revision": effective_contract.get("contract_revision"),
        "candidate_id": candidate_id,
        "creative_prompt": creative_prompt,
        "generator_constraints": {
            "project_branding": "exclude",
            "watermarks": "exclude",
            "negative_prompt": (
                "Do not render any project logo, brand signature, watermark, pseudo-logo, "
                "or substitute brand mark. Leave branding for a later deterministic composition step."
            ),
        },
    }
    if reserved_composition_space is not None:
        brief["reserved_composition_space"] = reserved_composition_space
    return validate_base_generation_brief(brief)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("contract_json")
    parser.add_argument("candidate_id")
    parser.add_argument("creative_prompt")
    args = parser.parse_args()
    with open(args.contract_json, "r", encoding="utf-8") as handle:
        contract = json.load(handle)
    brief = build_base_generation_brief(contract, args.candidate_id, args.creative_prompt)
    print(json.dumps(brief, ensure_ascii=False, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
