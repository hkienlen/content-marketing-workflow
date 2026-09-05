import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "content-marketing-workflow"
ARCH = SKILL / "docs" / "architecture"


class RuntimeCompatibilityTests(unittest.TestCase):
    def test_central_compatibility_authority_exists(self):
        contract = (ARCH / "runtime-compatibility-matrix.md").read_text()
        self.assertIn("READY", contract)
        self.assertIn("DEGRADED", contract)
        self.assertIn("BLOCKED", contract)
        self.assertIn("github_repository", contract)
        self.assertIn("cloud_media_storage", contract)
        self.assertIn("image_generation", contract)
        self.assertIn("wordpress_bridge_runtime", contract)
        self.assertIn("github_actions_scheduler", contract)

    def test_github_is_fatal_prerequisite(self):
        contract = (ARCH / "runtime-compatibility-matrix.md").read_text()
        start = (ARCH / "capabilities" / "start.md").read_text()
        self.assertIn("fatal / BLOCKED", contract)
        self.assertIn("no usable GitHub repository access -> BLOCKED", start)
        self.assertIn("Conversation memory is not a replacement", contract)

    def test_cloud_storage_has_no_forbidden_fallback(self):
        contract = (ARCH / "runtime-compatibility-matrix.md").read_text()
        self.assertIn("google_drive", contract)
        self.assertIn("dropbox", contract)
        self.assertIn("WordPress, GitHub and local filesystem are not fallback media providers", contract)
        self.assertIn("never automatically fall back from cloud storage to repository binaries", contract)

    def test_strict_no_image_publication_is_preserved(self):
        contract = (ARCH / "runtime-compatibility-matrix.md").read_text()
        skill = (SKILL / "SKILL.md").read_text()
        self.assertIn("no required verified final media", contract)
        self.assertIn("no WordPress publication/preparation-for-publication", contract)
        self.assertIn("no social publication", contract)
        self.assertIn("Do not silently degrade to image-less WordPress publication or text-only social publication", skill)

    def test_wordpress_bridge_is_required_for_current_social_publication(self):
        contract = (ARCH / "runtime-compatibility-matrix.md").read_text()
        self.assertIn("current LinkedIn publication relay", contract)
        self.assertIn("current Facebook Page publication relay", contract)
        self.assertIn("wordpress_bridge_runtime", contract)

    def test_image_generation_manual_handoff(self):
        contract = (ARCH / "runtime-compatibility-matrix.md").read_text()
        runtime = (ARCH / "chatgpt-skill-runtime.md").read_text()
        for text in (contract, runtime):
            self.assertIn("manual image handoff", text)
            self.assertIn("complete", text)
            self.assertIn("prompt", text)
        self.assertIn("return/upload the resulting image", runtime)

    def test_help_and_status_use_runtime_compatibility(self):
        behavior = (ARCH / "user-command-system-behaviors.md").read_text()
        self.assertIn("runtime-compatibility-matrix.md", behavior)
        self.assertIn("Compatibility: READY | DEGRADED | BLOCKED", behavior)
        self.assertIn("plugin eligibility", behavior)


if __name__ == "__main__":
    unittest.main()
