import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "content-marketing-workflow"
ARCH = SKILL / "docs" / "architecture"
CAP = ARCH / "capabilities"


class RuntimeCompatibilityTests(unittest.TestCase):
    def test_central_compatibility_authority_exists(self):
        contract = (ARCH / "runtime-compatibility-matrix.md").read_text()
        for token in (
            "READY",
            "DEGRADED",
            "BLOCKED",
            "github_repository",
            "cloud_media_storage",
            "image_generation",
            "wordpress_bridge_runtime",
            "github_actions_scheduler",
        ):
            self.assertIn(token, contract)

    def test_github_is_fatal_prerequisite(self):
        contract = (ARCH / "runtime-compatibility-matrix.md").read_text()
        start = (CAP / "start.md").read_text()
        self.assertIn("fatal / BLOCKED", contract)
        self.assertIn("no usable GitHub repository access -> BLOCKED", start)
        self.assertIn("Conversation memory is not a replacement", contract)

    def test_cloud_storage_has_no_forbidden_fallback(self):
        contract = (ARCH / "runtime-compatibility-matrix.md").read_text()
        drive = (ARCH / "google-drive-workspace.md").read_text()
        media = (ARCH / "media-delivery-architecture.md").read_text()
        self.assertIn("google_drive", contract)
        self.assertIn("dropbox", contract)
        self.assertIn("WordPress, GitHub and local filesystem are not fallback media providers", contract)
        self.assertIn("never automatically fall back from cloud storage to repository binaries", contract)
        self.assertIn("GitHub, WordPress and local filesystem are not alternate media-storage providers", drive)
        self.assertIn("legacy compatibility/migration only", media)

    def test_strict_no_image_publication_is_preserved_everywhere(self):
        contract = (ARCH / "runtime-compatibility-matrix.md").read_text()
        skill = (SKILL / "SKILL.md").read_text()
        wp_prepare = (CAP / "wordpress-prepare-article.md").read_text()
        wp_publish = (CAP / "wordpress-publish-article.md").read_text()
        social_schedule = (CAP / "social-schedule.md").read_text()
        social_publish = (CAP / "social-publish.md").read_text()

        self.assertIn("no required verified final media", contract)
        self.assertIn("no WordPress publication/preparation-for-publication", contract)
        self.assertIn("no social publication", contract)
        self.assertIn("Do not silently degrade to image-less WordPress publication or text-only social publication", skill)
        self.assertIn("There is no image-less WordPress fallback", wp_prepare)
        self.assertIn("There is no image-less WordPress publication fallback", wp_publish)
        self.assertIn("There is no text-only degraded publication fallback", social_schedule)
        self.assertIn("must not introduce text-only social publication", social_publish)

    def test_wordpress_bridge_is_required_for_current_social_publication(self):
        contract = (ARCH / "runtime-compatibility-matrix.md").read_text()
        schedule = (CAP / "social-schedule.md").read_text()
        publish = (CAP / "social-publish.md").read_text()
        self.assertIn("current LinkedIn publication relay", contract)
        self.assertIn("current Facebook Page publication relay", contract)
        self.assertIn("wordpress_bridge_runtime", schedule)
        self.assertIn("wordpress_bridge_runtime", publish)
        self.assertIn("WordPress-hosted SEO Workflow Bridge", schedule)

    def test_image_generation_manual_handoff_is_available_for_article_and_social(self):
        contract = (ARCH / "runtime-compatibility-matrix.md").read_text()
        runtime = (ARCH / "chatgpt-skill-runtime.md").read_text()
        article = (CAP / "seo-create-article.md").read_text()
        social_visual = (CAP / "social-create-visual.md").read_text()
        for text in (contract, runtime, article, social_visual):
            self.assertIn("manual", text.lower())
            self.assertIn("prompt", text.lower())
        self.assertIn("return/upload the resulting image", runtime)
        self.assertIn("user returns/uploads image", article)
        self.assertIn("ask the user to return/upload the generated result", social_visual)

    def test_media_and_content_contracts_reference_central_authority(self):
        paths = [
            ARCH / "media-delivery-architecture.md",
            ARCH / "google-drive-workspace.md",
            CAP / "seo-create-article.md",
            CAP / "social-create-visual.md",
            CAP / "social-schedule.md",
            CAP / "social-publish.md",
            CAP / "wordpress-prepare-article.md",
            CAP / "wordpress-publish-article.md",
        ]
        for path in paths:
            self.assertIn("runtime-compatibility-matrix.md", path.read_text(), path.name)

    def test_runtime_compatibility_persistence_schema(self):
        schema = json.loads((ARCH / "schemas" / "user-profile.schema.json").read_text())
        project = schema["$defs"]["project"]["properties"]
        self.assertIn("runtime_compatibility", project)
        compat = schema["$defs"]["runtimeCompatibility"]
        self.assertIn("overall_status", compat["properties"])
        self.assertIn("cloud_media_storage", compat["properties"])
        self.assertIn("wordpress_bridge_runtime", compat["properties"])
        self.assertIn("github_actions_scheduler", compat["properties"])
        # Image-generation availability is surface/runtime state and must be re-detected,
        # not treated as a permanent durable capability flag.
        self.assertNotIn("image_generation", compat["properties"])

    def test_direct_chatgpt_install_docs_explain_dependency_discovery(self):
        doc = (ROOT / "docs" / "chatgpt-direct-skill.md").read_text()
        self.assertIn("not expected to know or pre-install", doc)
        self.assertIn("Google Drive: supported/current", doc)
        self.assertIn("Dropbox: future adapter", doc)
        self.assertIn("Free or Plus", doc)
        self.assertIn("WordPress + compatible Bridge", doc)

    def test_help_and_status_use_runtime_compatibility(self):
        behavior = (ARCH / "user-command-system-behaviors.md").read_text()
        self.assertIn("runtime-compatibility-matrix.md", behavior)
        self.assertIn("Compatibility: READY | DEGRADED | BLOCKED", behavior)
        self.assertIn("plugin eligibility", behavior)


if __name__ == "__main__":
    unittest.main()
