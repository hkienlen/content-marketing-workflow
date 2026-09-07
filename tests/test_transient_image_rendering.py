import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "content-marketing-workflow"


class TransientImageRenderingTests(unittest.TestCase):
    def test_tool_rendering_is_not_review_or_approval(self):
        social = (SKILL / "docs" / "architecture" / "capabilities" / "social-create-visual.md").read_text()
        review = (SKILL / "docs" / "architecture" / "social-post-review-loop.md").read_text()
        entrypoint = (SKILL / "SKILL.md").read_text()
        self.assertIn("transient tool rendering is not a review presentation", social)
        self.assertIn("do not label it Visual A/B/C", social)
        self.assertIn("do not ask the user to validate/choose it", review)
        self.assertIn("continue automatically without a user decision", entrypoint)

    def test_visibility_alone_is_not_a_blocker(self):
        social = (SKILL / "docs" / "architecture" / "capabilities" / "social-create-visual.md").read_text()
        runtime = (SKILL / "docs" / "architecture" / "chatgpt-skill-runtime.md").read_text()
        matrix = (SKILL / "docs" / "architecture" / "runtime-compatibility-matrix.md").read_text()
        self.assertIn("Transient visibility alone is not a blocker", social)
        self.assertIn("must not by itself degrade or block `/social create`", runtime)
        self.assertIn("must not be interpreted as `direct_asset_output_available=false`", matrix)

    def test_missing_exact_asset_retention_has_precise_blocker(self):
        for path in [
            SKILL / "docs" / "architecture" / "capabilities" / "social-create-visual.md",
            SKILL / "docs" / "architecture" / "chatgpt-skill-runtime.md",
            SKILL / "docs" / "architecture" / "runtime-compatibility-matrix.md",
        ]:
            self.assertIn("generated_base_retention_unavailable", path.read_text())

    def test_first_human_visual_decision_is_branded_abc(self):
        social = (SKILL / "docs" / "architecture" / "capabilities" / "social-create-visual.md").read_text()
        review = (SKILL / "docs" / "architecture" / "social-post-review-loop.md").read_text()
        self.assertIn("the first human visual decision is on those branded A/B/C candidates", social)
        self.assertIn("The first requested visual decision remains the branded A/B/C package", review)


if __name__ == "__main__":
    unittest.main()
