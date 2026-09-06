import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "content-marketing-workflow"
SCHEMA_PATH = SKILL / "docs" / "architecture" / "schemas" / "user-profile.schema.json"
RESOLVER_PATH = SKILL / "scripts" / "visual-policy-resolve.py"
CATALOGUE_PATH = SKILL / "docs" / "architecture" / "user-command-catalog.yaml"


def load_resolver():
    spec = importlib.util.spec_from_file_location("visual_policy_resolve", RESOLVER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load visual-policy-resolve.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def base_profile(*, visual_identity=True, with_logo=True):
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
        cls.resolver = load_resolver()

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
        self.assertIn("article: never", brand)
        self.assertIn("social: always", brand)
        self.assertIn("recreate the logo approximately", brand)
        self.assertIn("logo_policy.article", article)
        self.assertIn("Never use `logo_policy.social` as a fallback", article)
        self.assertIn("logo_policy.social", social)
        self.assertIn("Never use `logo_policy.article` as a fallback", social)

    def test_provider_contracts_include_private_brand_workspace(self):
        for name in ("google-drive-workspace.md", "dropbox-workspace.md"):
            text = (SKILL / "docs" / "architecture" / name).read_text()
            self.assertIn("brand/", text, name)
            self.assertIn("logos/", text, name)
            self.assertIn("remain private", text, name)
            self.assertIn("brand-assets-contract.md", text, name)


if __name__ == "__main__":
    unittest.main()
