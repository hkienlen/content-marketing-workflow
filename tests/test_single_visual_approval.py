import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "content-marketing-workflow"

class SingleSocialVisualApprovalTests(unittest.TestCase):
    def test_clean_bases_are_not_review_candidates_and_branded_candidates_are_first_review(self):
        social = (SKILL / "docs" / "architecture" / "capabilities" / "social-create-visual.md").read_text()
        review = (SKILL / "docs" / "architecture" / "social-post-review-loop.md").read_text()
        checklist = (SKILL / "docs" / "architecture" / "social-execution-checklist.md").read_text()
        entrypoint = (SKILL / "SKILL.md").read_text()
        self.assertIn("transient tool rendering is not a review presentation", social)
        self.assertIn("must not ask the user to choose/validate it", social)
        self.assertIn("one visual approval gate", review)
        self.assertIn("no intermediate approval of unbranded clean bases", checklist)
        self.assertIn("never present them as review candidates or ask the user to approve them", entrypoint)

    def test_branded_selection_is_visual_approval_and_non_material_finalization_is_automatic(self):
        social = (SKILL / "docs" / "architecture" / "capabilities" / "social-create-visual.md").read_text()
        review = (SKILL / "docs" / "architecture" / "social-post-review-loop.md").read_text()
        ingest = (SKILL / "docs" / "architecture" / "capabilities" / "asset-ingest.md").read_text()
        checklist = (SKILL / "docs" / "architecture" / "social-execution-checklist.md").read_text()
        self.assertIn("selection of one review-ready branded A/B/C candidate is the human visual approval", social)
        self.assertIn("Non-material finalization", review)
        self.assertIn("must not ask the user to approve the same visual again", ingest)
        self.assertIn("without requesting another approval", ingest)
        self.assertNotIn("-> user reviews result", ingest)
        self.assertIn("without a second human approval request", checklist)

    def test_material_changes_require_only_targeted_reconfirmation(self):
        review = (SKILL / "docs" / "architecture" / "social-post-review-loop.md").read_text()
        ingest = (SKILL / "docs" / "architecture" / "capabilities" / "asset-ingest.md").read_text()
        social = (SKILL / "docs" / "architecture" / "capabilities" / "social-create-visual.md").read_text()
        for text in (review, ingest, social):
            self.assertIn("targeted re-confirmation", text)
        self.assertIn("meaningful crop/reframe", review)
        self.assertIn("logo position/size/variant change", ingest)

if __name__ == "__main__":
    unittest.main()
