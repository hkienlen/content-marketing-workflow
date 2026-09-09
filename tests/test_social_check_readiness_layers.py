import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "content-marketing-workflow"

class SocialCheckReadinessLayersTests(unittest.TestCase):
    def read(self, rel):
        return (SKILL / rel).read_text()

    def test_check_has_three_independent_layers(self):
        doc = self.read("docs/architecture/capabilities/social-check-before-publish.md")
        for token in ("content_readiness", "schedule_readiness", "unattended_execution_readiness"):
            self.assertIn(token, doc)
        self.assertIn("later layer must not rewrite an earlier passing layer as failed", doc)

    def test_wordpress_article_publish_flag_never_blocks_social(self):
        check = self.read("docs/architecture/capabilities/social-check-before-publish.md")
        schedule = self.read("docs/architecture/capabilities/social-schedule.md")
        publish = self.read("docs/architecture/capabilities/social-publish.md")
        matrix = self.read("docs/architecture/runtime-compatibility-matrix.md")
        self.assertIn("wordpress.publish_enabled` controls **WordPress article publication only**", check)
        self.assertIn("`wordpress.publish_enabled=false` alone is **not** evidence", schedule)
        self.assertIn("`wordpress.publish_enabled` is not a social prerequisite", publish)
        self.assertIn("wordpress.publish_enabled = false", matrix)
        self.assertIn("LinkedIn/Facebook publication disabled", matrix)

    def test_authorization_is_precreated_and_dormant_until_due(self):
        check = self.read("docs/architecture/capabilities/social-check-before-publish.md")
        schedule = self.read("docs/architecture/capabilities/social-schedule.md")
        self.assertIn("normally materialized **before the due date**", check)
        self.assertIn("authorization created before planned_at", check)
        self.assertIn("Exact authorization may already exist long before that timestamp", schedule)

    def test_scheduler_issue_is_execution_layer_only(self):
        check = self.read("docs/architecture/capabilities/social-check-before-publish.md")
        matrix = self.read("docs/architecture/runtime-compatibility-matrix.md")
        self.assertIn("unverified/missing GitHub Actions scheduler is an unattended-execution infrastructure issue", check)
        self.assertIn("do not mislabel approved content or schedule readiness as failed", matrix)

if __name__ == "__main__":
    unittest.main()
