import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "content-marketing-workflow"
PLUGIN_SKILL = ROOT / "plugins" / "content-marketing-workflow" / "skills" / "content-marketing-workflow"


class StatusRuntimeIdentityTests(unittest.TestCase):
    def test_status_uses_packaged_version_as_runtime_authority(self):
        entrypoint = (SKILL / "SKILL.md").read_text()
        behaviors = (SKILL / "docs" / "architecture" / "user-command-system-behaviors.md").read_text()
        runtime = (SKILL / "docs" / "architecture" / "user-command-runtime-contract.md").read_text()
        direct = (SKILL / "docs" / "architecture" / "chatgpt-skill-runtime.md").read_text()

        self.assertIn("packaged `VERSION`", entrypoint)
        self.assertIn("Version Skill: 0.x.y", behaviors)
        self.assertIn("skill_version: <exact trimmed packaged VERSION|unknown>", runtime)
        self.assertIn("version_source: packaged_skill_VERSION", runtime)
        self.assertIn("runtime version authority is the packaged `VERSION`", direct)

    def test_status_must_not_substitute_remote_version(self):
        entrypoint = (SKILL / "SKILL.md").read_text()
        behaviors = (SKILL / "docs" / "architecture" / "user-command-system-behaviors.md").read_text()
        runtime = (SKILL / "docs" / "architecture" / "user-command-runtime-contract.md").read_text()

        self.assertIn("Never infer the loaded runtime version from the product repository root `VERSION`", entrypoint)
        self.assertIn("If the packaged `VERSION` resource is unavailable, report `Version Skill: unknown`", behaviors)
        self.assertIn("Never silently substitute a remotely discovered version", runtime)

    def test_status_reports_distribution_from_runtime_context_only(self):
        behaviors = (SKILL / "docs" / "architecture" / "user-command-system-behaviors.md").read_text()
        runtime = (SKILL / "docs" / "architecture" / "user-command-runtime-contract.md").read_text()
        catalog = (SKILL / "docs" / "architecture" / "user-command-catalog.yaml").read_text()

        self.assertIn("Direct ChatGPT Skill | Codex plugin | unknown", behaviors)
        self.assertIn("distribution: direct_chatgpt_skill|codex_plugin|unknown", runtime)
        self.assertIn("loaded Skill runtime identity/version", catalog)

    def test_045_version_is_synchronized(self):
        root_version = (ROOT / "VERSION").read_text().strip()
        skill_version = (SKILL / "VERSION").read_text().strip()
        plugin_skill_version = (PLUGIN_SKILL / "VERSION").read_text().strip()
        manifest = json.loads((ROOT / "plugins" / "content-marketing-workflow" / ".codex-plugin" / "plugin.json").read_text())

        self.assertEqual("0.4.5", root_version)
        self.assertEqual(root_version, skill_version)
        self.assertEqual(root_version, plugin_skill_version)
        self.assertEqual(root_version, manifest["version"])


if __name__ == "__main__":
    unittest.main()
