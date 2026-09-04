#!/usr/bin/env python3
"""Resolve effective visual-source policy for one content item.

This helper is intentionally credential-free. It performs deterministic profile
inheritance/validation and computes the missing-source decision. Provider file
resolution, image inspection and durable mutations remain orchestration concerns
of the visual-source-resolve capability.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping

POLICY_KEYS = (
    "visual_source",
    "missing_user_images_behavior",
    "source_fidelity",
    "ai_treatment",
    "ai_treatment_directive",
)

ENUMS = {
    "visual_source": {
        "ai_first",
        "user_images_first",
        "strict_user_images",
        "hybrid_best_fit",
    },
    "missing_user_images_behavior": {
        "ask_before_drafting",
        "allow_ai_generation",
        "continue_without_visuals",
    },
    "source_fidelity": {"strict", "high", "moderate", "flexible"},
    "ai_treatment": {
        "none",
        "light_correction",
        "natural_enhancement",
        "marketing_enhancement",
        "creative_transformation",
    },
}

# Backward-compatibility only for project profiles created before visual
# preferences existed. New/updated projects are expected to persist an explicit
# policy through onboarding. The fallback preserves the historical AI-first
# production path while reporting configured=false.
LEGACY_COMPATIBILITY_POLICY = {
    "visual_source": "ai_first",
    "missing_user_images_behavior": "allow_ai_generation",
    "source_fidelity": "flexible",
    "ai_treatment": "natural_enhancement",
    "ai_treatment_directive": None,
}


class VisualPolicyError(ValueError):
    """Raised when visual policy input is invalid or ambiguous."""


def _as_mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise VisualPolicyError(f"{label} must be an object")
    return value


def _validate_layer(layer: Mapping[str, Any], label: str, *, require_full: bool) -> dict[str, Any]:
    unknown = sorted(set(layer) - set(POLICY_KEYS))
    if unknown:
        raise VisualPolicyError(f"{label} contains unsupported fields: {', '.join(unknown)}")

    if require_full:
        required = set(POLICY_KEYS) - {"ai_treatment_directive"}
        missing = sorted(required - set(layer))
        if missing:
            raise VisualPolicyError(f"{label} missing required fields: {', '.join(missing)}")

    result: dict[str, Any] = {}
    for key, value in layer.items():
        if key in ENUMS:
            if value not in ENUMS[key]:
                allowed = ", ".join(sorted(ENUMS[key]))
                raise VisualPolicyError(f"{label}.{key} must be one of: {allowed}")
            result[key] = value
            continue

        if key == "ai_treatment_directive":
            if value is not None and not isinstance(value, str):
                raise VisualPolicyError(f"{label}.ai_treatment_directive must be string or null")
            if isinstance(value, str) and len(value) > 4000:
                raise VisualPolicyError(f"{label}.ai_treatment_directive exceeds 4000 characters")
            result[key] = value

    return result


def _merge(base: Mapping[str, Any], override: Mapping[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    # null directive intentionally clears an inherited free-text directive;
    # enum fields cannot be null after validation.
    merged.update(override)
    return merged


def resolve_visual_policy(
    profile: Mapping[str, Any],
    content_kind: str,
    local_override: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Return deterministic project -> kind -> local policy resolution."""

    if content_kind not in {"article", "social"}:
        raise VisualPolicyError("content_kind must be article or social")

    active_project_id = profile.get("active_project_id")
    projects = _as_mapping(profile.get("projects"), "profile.projects")
    if not isinstance(active_project_id, str) or not active_project_id:
        raise VisualPolicyError("profile.active_project_id is required")
    if active_project_id not in projects:
        raise VisualPolicyError("active_project_id does not resolve to a project")

    project = _as_mapping(projects[active_project_id], f"projects.{active_project_id}")
    preferences = project.get("visual_preferences")

    sources: list[str] = []
    if preferences is None:
        policy = dict(LEGACY_COMPATIBILITY_POLICY)
        configured = False
        sources.append("legacy_compatibility_ai_first")
    else:
        preferences = _as_mapping(preferences, "visual_preferences")
        default_layer = _validate_layer(
            _as_mapping(preferences.get("default"), "visual_preferences.default"),
            "visual_preferences.default",
            require_full=True,
        )
        policy = dict(default_layer)
        policy.setdefault("ai_treatment_directive", None)
        configured = True
        sources.append("project_default")

        kind_layer = preferences.get(content_kind)
        if kind_layer is not None:
            kind_override = _validate_layer(
                _as_mapping(kind_layer, f"visual_preferences.{content_kind}"),
                f"visual_preferences.{content_kind}",
                require_full=False,
            )
            policy = _merge(policy, kind_override)
            sources.append(f"project_{content_kind}_override")

    if local_override is not None:
        local = _validate_layer(
            _as_mapping(local_override, "local_override"),
            "local_override",
            require_full=False,
        )
        if not local:
            raise VisualPolicyError("local_override must contain at least one supported field")
        policy = _merge(policy, local)
        sources.append("content_local_override")

    # Validate the final policy even for compatibility fallback.
    policy = _validate_layer(policy, "resolved_policy", require_full=True)
    policy.setdefault("ai_treatment_directive", None)

    return {
        "configured": configured,
        "active_project_id": active_project_id,
        "content_kind": content_kind,
        "policy": policy,
        "inheritance": sources,
    }


def decide_missing_source(resolution: Mapping[str, Any], has_user_images: bool) -> dict[str, Any]:
    """Return the truthful pre-draft state for the resolved policy."""

    policy = _as_mapping(resolution.get("policy"), "resolution.policy")
    source_mode = policy.get("visual_source")
    missing_behavior = policy.get("missing_user_images_behavior")

    if has_user_images:
        return {
            "state": "source_ready",
            "drafting_allowed": True,
            "requires_source_inspection": True,
            "synthetic_replacement_requires_explicit_local_override": source_mode == "strict_user_images",
        }

    if source_mode == "ai_first":
        return {
            "state": "ai_generation_allowed",
            "drafting_allowed": True,
            "requires_source_inspection": False,
            "synthetic_replacement_requires_explicit_local_override": False,
        }

    if missing_behavior == "ask_before_drafting":
        return {
            "state": "awaiting_user_images",
            "drafting_allowed": False,
            "requires_source_inspection": True,
            "synthetic_replacement_requires_explicit_local_override": source_mode == "strict_user_images",
        }

    if missing_behavior == "continue_without_visuals":
        return {
            "state": "continue_without_visuals",
            "drafting_allowed": True,
            "requires_source_inspection": False,
            "synthetic_replacement_requires_explicit_local_override": source_mode == "strict_user_images",
        }

    if missing_behavior == "allow_ai_generation":
        if source_mode == "strict_user_images":
            # Strict truth/fidelity wins over a generic missing-source fallback.
            # A content-local explicit source-mode override is required to permit
            # a synthetic replacement for that item.
            return {
                "state": "awaiting_user_images",
                "drafting_allowed": False,
                "requires_source_inspection": True,
                "synthetic_replacement_requires_explicit_local_override": True,
            }
        return {
            "state": "ai_generation_allowed",
            "drafting_allowed": True,
            "requires_source_inspection": False,
            "synthetic_replacement_requires_explicit_local_override": False,
        }

    raise VisualPolicyError("unsupported missing-source decision")


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", type=Path, required=True)
    parser.add_argument("--content-kind", choices=("article", "social"), required=True)
    parser.add_argument("--local-override", type=Path)
    parser.add_argument(
        "--has-user-images",
        choices=("true", "false", "unknown"),
        default="unknown",
        help="Optionally compute the pre-draft decision for known source availability.",
    )
    args = parser.parse_args()

    profile = _load_json(args.profile)
    local_override = _load_json(args.local_override) if args.local_override else None
    result = resolve_visual_policy(profile, args.content_kind, local_override)

    if args.has_user_images != "unknown":
        result["source_decision"] = decide_missing_source(
            result, args.has_user_images == "true"
        )

    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
