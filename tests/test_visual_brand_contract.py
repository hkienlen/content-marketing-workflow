import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "content-marketing-workflow"
SCHEMA_PATH = SKILL / "docs" / "architecture" / "schemas" / "user-profile.schema.json"
RESOLVER_PATH = SKILL / "scripts" / "visual-policy-resolve.py"
CONTRACT_FREEZE_PATH = SKILL / "scripts" / "visual-contract-freeze.py"
LOGO_COMPOSE_PATH = SKILL / "scripts" / "logo-compose.py"
CATALOGUE_PATH = SKILL / "docs" / "architecture" / "user-command-catalog.yaml"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path.name}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def base_profile(*, visual_identity=True, with_logo=True, active_provider=None):
    project = {
        "visual_preferences": {
            "default": {
                "visual_source": "ai_first",
                "missing_user_images_behavior": "allow_ai_generation",
                "source_fidelity": "flexible",
                "ai_treatment": "natural_enhancement",
                "ai_treatment_directive": None,
            }
        }
    }
    if active_provider is not None:
        project["storage"] = {
            "cloud_media_storage": {
                "provider": active_provider,
            }
        }
    if visual_identity:
        identity = {
            "guidelines_path": "strategy/visual-guidelines.md",
            "logo_policy": {
                "article": "never",
                "social": "always",
            },
        }
        if with_logo:
            identity["logo_assets"] = {
                "dark": {
                    "provider": "google_drive",
                    "asset_id": "logo-dark",
                    "filename": "logo-dark.png",
                    "sha256": "0" * 64,
                    "mime_type": "image/png",
                    "width": 1024,
                    "height": 170,
                }
            }
        project["visual_identity"] = identity

    return {
        "active_project_id": "project",
        "projects": {"project": project},
    }


class VisualBrandContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.resolver = load_module(RESOLVER_PATH, "visual_policy_resolve")
        cls.contract_freeze = load_module(
            CONTRACT_FREEZE_PATH, "visual_contract_freeze"
        )

    def test_schema_has_independent_article_social_logo_policy(self):
        schema = json.loads(SCHEMA_PATH.read_text())
        defs = schema["$defs"]

        self.assertEqual(set(defs["logoApplicationMode"]["enum"]), {"always", "auto", "never"})
        self.assertEqual(set(defs["logoPolicy"]["required"]), {"article", "social"})
        self.assertEqual(defs["logoPolicy"]["properties"]["article"]["$ref"], "#/$defs/logoApplicationMode")
        self.assertEqual(defs["logoPolicy"]["properties"]["social"]["$ref"], "#/$defs/logoApplicationMode")
        self.assertIn("visual_identity", defs["project"]["properties"])
        self.assertIn("brand_ref", defs["cloudMediaStorage"]["properties"])

    def test_article_never_and_social_always_are_resolved_independently(self):
        profile = base_profile()

        article = self.resolver.resolve_visual_policy(profile, "article")
        social = self.resolver.resolve_visual_policy(profile, "social")

        self.assertEqual(article["brand"]["logo_application"], "never")
        self.assertFalse(article["brand"]["logo_required_for_final"])
        self.assertEqual(article["brand"]["logo_status"], "ready")

        self.assertEqual(social["brand"]["logo_application"], "always")
        self.assertTrue(social["brand"]["logo_required_for_final"])
        self.assertTrue(social["brand"]["logo_asset_available"])
        self.assertEqual(social["brand"]["logo_status"], "ready")

    def test_social_always_without_logo_blocks_final_branding_only(self):
        social = self.resolver.resolve_visual_policy(
            base_profile(with_logo=False),
            "social",
        )

        self.assertEqual(social["brand"]["logo_application"], "always")
        self.assertFalse(social["brand"]["logo_asset_available"])
        self.assertEqual(social["brand"]["logo_status"], "awaiting_brand_asset")

        decision = self.resolver.decide_missing_source(social, has_user_images=False)
        self.assertEqual(decision["state"], "ai_generation_allowed")
        self.assertTrue(decision["drafting_allowed"])

    def test_logo_asset_from_inactive_provider_requires_rebinding(self):
        social = self.resolver.resolve_visual_policy(
            base_profile(active_provider="dropbox"),
            "social",
        )

        self.assertEqual(social["brand"]["active_media_provider"], "dropbox")
        self.assertFalse(social["brand"]["logo_asset_available"])
        self.assertTrue(social["brand"]["provider_rebinding_required"])
        self.assertEqual(social["brand"]["logo_status"], "awaiting_brand_asset")
        self.assertIn("dark", social["brand"]["mismatched_logo_assets"])
        self.assertEqual(social["brand"]["compatible_logo_assets"], {})

    def test_logo_asset_on_active_provider_is_ready(self):
        social = self.resolver.resolve_visual_policy(
            base_profile(active_provider="google_drive"),
            "social",
        )

        self.assertTrue(social["brand"]["logo_asset_available"])
        self.assertFalse(social["brand"]["provider_rebinding_required"])
        self.assertIn("dark", social["brand"]["compatible_logo_assets"])
        self.assertEqual(social["brand"]["logo_status"], "ready")

    def test_content_local_logo_override_does_not_change_project_policy(self):
        profile = base_profile()
        local = self.resolver.resolve_visual_policy(
            profile,
            "social",
            {"logo_application": "never"},
        )
        next_social = self.resolver.resolve_visual_policy(profile, "social")

        self.assertEqual(local["brand"]["logo_application"], "never")
        self.assertEqual(local["brand"]["logo_policy_source"], "content_local_logo_override")
        self.assertEqual(next_social["brand"]["logo_application"], "always")

    def test_content_local_free_visual_directives_are_supported(self):
        result = self.resolver.resolve_visual_policy(
            base_profile(),
            "article",
            {"visual_directives": ["For this image only, use a flat illustration."]},
        )
        self.assertEqual(
            result["brand"]["local_visual_directives"],
            ["For this image only, use a flat illustration."],
        )
        self.assertEqual(result["brand"]["logo_application"], "never")

    def test_legacy_profile_does_not_add_logo_silently(self):
        result = self.resolver.resolve_visual_policy(
            base_profile(visual_identity=False),
            "social",
        )

        self.assertFalse(result["brand"]["configured"])
        self.assertEqual(result["brand"]["logo_application"], "never")
        self.assertEqual(result["brand"]["logo_policy_source"], "legacy_unconfigured_no_logo")

    def test_effective_visual_contract_revision_is_deterministic_and_verified(self):
        contract = {
            "content_kind": "social",
            "source_policy": {"visual_source": "ai_first"},
            "visual_guidelines_path": "strategy/visual-guidelines.md",
            "applied_user_directives": {
                "project_global": ["Avoid generic 3D illustration."],
                "channel": ["Keep image text short."],
                "content_local": [],
            },
            "logo_application": "always",
            "logo_asset_identity": {
                "provider": "google_drive",
                "asset_id": "logo-dark",
                "sha256": "0" * 64,
            },
            "generic_defaults_applied": ["1080x1350", "mobile readability"],
        }

        frozen_a = self.contract_freeze.freeze_contract(contract)
        frozen_b = self.contract_freeze.freeze_contract(dict(reversed(list(contract.items()))))

        self.assertRegex(frozen_a["contract_revision"], r"^sha256:[a-f0-9]{64}$")
        self.assertEqual(frozen_a["contract_revision"], frozen_b["contract_revision"])
        verified = self.contract_freeze.verify_contract(frozen_a)
        self.assertEqual(verified["contract_revision"], frozen_a["contract_revision"])

        tampered = dict(frozen_a)
        tampered["logo_application"] = "never"
        with self.assertRaises(self.contract_freeze.VisualContractError):
            self.contract_freeze.verify_contract(tampered)

    def test_visual_command_family_is_public(self):
        catalogue = CATALOGUE_PATH.read_text()
        for command in (
            "/visual status",
            "/visual configure",
            "/visual logo",
            "/visual guidelines",
            "/logo",
        ):
            self.assertIn(f"command: {command}", catalogue)

    def test_generic_contracts_preserve_user_precedence_and_logo_integrity(self):
        visual = (SKILL / "docs" / "architecture" / "visual-generation-contract.md").read_text()
        brand = (SKILL / "docs" / "architecture" / "brand-assets-contract.md").read_text()
        article = (SKILL / "docs" / "architecture" / "capabilities" / "seo-create-article.md").read_text()
        social = (SKILL / "docs" / "architecture" / "capabilities" / "social-create-visual.md").read_text()

        self.assertIn("content-local user directives", visual)
        self.assertIn("generic CMW creative defaults", visual)
        self.assertIn("visual-contract-freeze.py", visual)
        self.assertIn("must have a `contract_revision`", visual)
        self.assertIn("article: never", brand)
        self.assertIn("social: always", brand)
        self.assertIn("recreate the logo approximately", brand)
        self.assertIn("logo-compose.py", brand)
        self.assertIn("logo_policy.article", article)
        self.assertIn("Never use `logo_policy.social` as a fallback", article)
        self.assertIn("logo_policy.social", social)
        self.assertIn("Never use `logo_policy.article` as a fallback", social)

    def test_logo_composition_helper_is_fail_closed_and_exact_asset_bound(self):
        source = LOGO_COMPOSE_PATH.read_text()
        self.assertIn("--expected-logo-sha256", source)
        self.assertIn("official logo SHA-256 mismatch", source)
        self.assertIn("output must not overwrite the official logo", source)
        self.assertIn("alpha_composite", source)
        self.assertIn("Image.Resampling.LANCZOS", source)

    def test_provider_contracts_include_private_brand_workspace(self):
        for name in ("google-drive-workspace.md", "dropbox-workspace.md"):
            text = (SKILL / "docs" / "architecture" / name).read_text()
            self.assertIn("brand/", text, name)
            self.assertIn("logos/", text, name)
            self.assertIn("remain private", text, name)
            self.assertIn("brand-assets-contract.md", text, name)


if __name__ == "__main__":
    unittest.main()
