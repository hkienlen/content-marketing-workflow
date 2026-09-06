#!/usr/bin/env python3
"""Resolve effective visual-source and structured brand policy for one content item.

This helper is intentionally credential-free. It performs deterministic profile
inheritance/validation for source/treatment and independent article/social logo
application, then computes the missing-source decision. Provider file resolution,
rich prose-guideline interpretation, image inspection, logo composition and
durable mutations remain orchestration concerns of the owning capabilities.
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
LOCAL_EXTRA_KEYS = ("logo_application", "visual_directives")
LOGO_APPLICATIONS = {"always", "auto", "never"}
LOGO_ASSET_KEYS = {"primary", "light", "dark"}

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

# Backward compatibility for profiles created before explicit visual settings.
# Source behavior preserves the historical AI-first path while configured=false.
LEGACY_COMPATIBILITY_POLICY = {
    "visual_source": "ai_first",
    "missing_user_images_behavior": "allow_ai_generation",
    "source_fidelity": "flexible",
    "ai_treatment": "natural_enhancement",
    "ai_treatment_directive": None,
}

# Branding did not exist in older generic profiles. Preserve the historical
# no-logo behavior rather than unexpectedly adding a mark, but report the
# structured identity as unconfigured so onboarding can gather the user's choice.
LEGACY_LOGO_APPLICATION = "never"


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


def _validate_local_override(layer: Mapping[str, Any]) -> tuple[dict[str, Any], str | None, list[str]]:
    supported = set(POLICY_KEYS) | set(LOCAL_EXTRA_KEYS)
    unknown = sorted(set(layer) - supported)
    if unknown:
        raise VisualPolicyError(
            f"local_override contains unsupported fields: {', '.join(unknown)}"
        )

    policy_part = _validate_layer(
        {key: value for key, value in layer.items() if key in POLICY_KEYS},
        "local_override",
        require_full=False,
    )

    logo_application = layer.get("logo_application")
    if logo_application is not None and logo_application not in LOGO_APPLICATIONS:
        allowed = ", ".join(sorted(LOGO_APPLICATIONS))
        raise VisualPolicyError(f"local_override.logo_application must be one of: {allowed}")

    directives_raw = layer.get("visual_directives", [])
    if directives_raw is None:
        directives_raw = []
    if not isinstance(directives_raw, list):
        raise VisualPolicyError("local_override.visual_directives must be an array")
    if len(directives_raw) > 50:
        raise VisualPolicyError("local_override.visual_directives exceeds 50 entries")

    directives: list[str] = []
    for index, value in enumerate(directives_raw):
        if not isinstance(value, str) or not value.strip():
            raise VisualPolicyError(
                f"local_override.visual_directives[{index}] must be a non-empty string"
            )
        if len(value) > 4000:
            raise VisualPolicyError(
                f"local_override.visual_directives[{index}] exceeds 4000 characters"
            )
        directives.append(value)

    if not policy_part and logo_application is None and not directives:
        raise VisualPolicyError("local_override must contain at least one supported field")

    return policy_part, logo_application, directives


def _merge(base: Mapping[str, Any], override: Mapping[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    # null directive intentionally clears an inherited free-text directive;
    # enum fields cannot be null after validation.
    merged.update(override)
    return merged


def _resolve_brand_identity(
    project: Mapping[str, Any],
    content_kind: str,
    *,
    local_logo_application: str | None,
    local_visual_directives: list[str],
) -> dict[str, Any]:
    identity = project.get("visual_identity")

    if identity is None:
        logo_application = LEGACY_LOGO_APPLICATION
        configured = False
        guidelines_path = None
        logo_assets: dict[str, Any] = {}
        inheritance = ["legacy_unconfigured_no_logo"]
    else:
        identity_map = _as_mapping(identity, "visual_identity")
        logo_policy = _as_mapping(identity_map.get("logo_policy"), "visual_identity.logo_policy")

        missing_channels = sorted({"article", "social"} - set(logo_policy))
        if missing_channels:
            raise VisualPolicyError(
                "visual_identity.logo_policy missing required fields: "
                + ", ".join(missing_channels)
            )

        for channel in ("article", "social"):
            value = logo_policy.get(channel)
            if value not in LOGO_APPLICATIONS:
                allowed = ", ".join(sorted(LOGO_APPLICATIONS))
                raise VisualPolicyError(
                    f"visual_identity.logo_policy.{channel} must be one of: {allowed}"
                )

        logo_application = str(logo_policy[content_kind])
        configured = True
        inheritance = ["project_visual_identity", f"project_{content_kind}_logo_policy"]

        guidelines_path = identity_map.get("guidelines_path")
        if guidelines_path is not None and (
            not isinstance(guidelines_path, str) or not guidelines_path.strip()
        ):
            raise VisualPolicyError("visual_identity.guidelines_path must be non-empty string or null")

        assets_raw = identity_map.get("logo_assets", {})
        logo_assets_map = _as_mapping(assets_raw, "visual_identity.logo_assets")
        unknown_assets = sorted(set(logo_assets_map) - LOGO_ASSET_KEYS)
        if unknown_assets:
            raise VisualPolicyError(
                "visual_identity.logo_assets contains unsupported variants: "
                + ", ".join(unknown_assets)
            )
        logo_assets = dict(logo_assets_map)

    if local_logo_application is not None:
        logo_application = local_logo_application
        inheritance.append("content_local_logo_override")

    if local_visual_directives:
        inheritance.append("content_local_visual_directives")

    logo_asset_available = bool(logo_assets)
    logo_status = (
        "awaiting_brand_asset"
        if logo_application == "always" and not logo_asset_available
        else "ready"
    )

    return {
        "configured": configured,
        "guidelines_path": guidelines_path,
        "logo_application": logo_application,
        "logo_policy_source": inheritance[-1] if local_logo_application is not None else inheritance[1] if configured else inheritance[0],
        "logo_assets": logo_assets,
        "logo_asset_available": logo_asset_available,
        "logo_required_for_final": logo_application == "always",
        "logo_allowed": logo_application != "never",
        "logo_status": logo_status,
        "local_visual_directives": local_visual_directives,
        "inheritance": inheritance,
    }


def resolve_visual_policy(
    profile: Mapping[str, Any],
    content_kind: str,
    local_override: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Return deterministic project -> kind -> local visual resolution."""

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

    local_policy: dict[str, Any] = {}
    local_logo_application: str | None = None
    local_visual_directives: list[str] = []
    if local_override is not None:
        local_policy, local_logo_application, local_visual_directives = _validate_local_override(
            _as_mapping(local_override, "local_override")
        )
        if local_policy:
            policy = _merge(policy, local_policy)
            sources.append("content_local_override")

    # Validate the final source/treatment policy even for compatibility fallback.
    policy = _validate_layer(policy, "resolved_policy", require_full=True)
    policy.setdefault("ai_treatment_directive", None)

    brand = _resolve_brand_identity(
        project,
        content_kind,
        local_logo_application=local_logo_application,
        local_visual_directives=local_visual_directives,
    )

    return {
        "configured": configured,
        "active_project_id": active_project_id,
        "content_kind": content_kind,
        "policy": policy,
        "inheritance": sources,
        "brand": brand,
    }


def decide_missing_source(resolution: Mapping[str, Any], has_user_images: bool) -> dict[str, Any]:
    """Return the truthful pre-draft state for the resolved source policy."""

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
