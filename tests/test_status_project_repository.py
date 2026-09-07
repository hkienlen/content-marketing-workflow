import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "content-marketing-workflow"
PLUGIN_SKILL = ROOT / "plugins" / "content-marketing-workflow" / "skills" / "content-marketing-workflow"

class StatusProjectRepositoryTests(unittest.TestCase):
    def test_status_exposes_active_project_repository(self):
        entrypoint = (SKILL / "SKILL.md").read_text()
        behaviors = (SKILL / "docs" / "architecture" / "user-command-system-behaviors.md").read_text()
        runtime = (SKILL / "docs" / "architecture" / "user-command-runtime-contract.md").read_text()
        profile = (SKILL / "docs" / "architecture" / "user-profile-data-contract.md").read_text()
        self.assertIn("repository.full_name` as `Dépôt projet GitHub", entrypoint)
        self.assertIn("Dépôt projet GitHub: owner/repository | unknown", behaviors)
        self.assertIn("github_repository: <owner/repository|unknown>", runtime)
        self.assertIn("projects[active_project_id].repository.full_name", profile)

    def test_product_repo_is_not_project_repo_fallback(self):
        entrypoint = (SKILL / "SKILL.md").read_text()
        behaviors = (SKILL / "docs" / "architecture" / "user-command-system-behaviors.md").read_text()
        direct = (SKILL / "docs" / "architecture" / "chatgpt-skill-runtime.md").read_text()
        self.assertIn("Never use `hkienlen/content-marketing-workflow`", entrypoint)
        self.assertIn("never display `hkienlen/content-marketing-workflow` merely because", behaviors)
        self.assertIn("Never use `hkienlen/content-marketing-workflow` merely because", direct)

    def test_unknown_and_inconsistent_states_are_fail_closed(self):
        entrypoint = (SKILL / "SKILL.md").read_text()
        runtime = (SKILL / "docs" / "architecture" / "user-command-runtime-contract.md").read_text()
        self.assertIn("report `unknown`", entrypoint)
        self.assertIn("`STATE_INCONSISTENT`", entrypoint)
        self.assertIn("repository_consistency: consistent|unknown|inconsistent", runtime)
        self.assertIn("Absence of any usable active project repository makes overall compatibility `BLOCKED`", runtime)

    def test_046_version_is_synchronized(self):
        root_version = (ROOT / "VERSION").read_text().strip()
        skill_version = (SKILL / "VERSION").read_text().strip()
        plugin_skill_version = (PLUGIN_SKILL / "VERSION").read_text().strip()
        manifest = json.loads((ROOT / "plugins" / "content-marketing-workflow" / ".codex-plugin" / "plugin.json").read_text())
        self.assertEqual("0.4.6", root_version)
        self.assertEqual(root_version, skill_version)
        self.assertEqual(root_version, plugin_skill_version)
        self.assertEqual(root_version, manifest["version"])

if __name__ == "__main__":
    unittest.main()
