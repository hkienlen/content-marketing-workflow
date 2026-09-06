import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "content-marketing-workflow"
SCRIPT = SKILL / "scripts" / "base-generation-brief.py"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path.name}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class BaseGenerationBriefTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = load_module(SCRIPT, "base_generation_brief")

    def _contract(self):
        return {
            "content_kind": "social",
            "contract_revision": "sha256:" + "a" * 64,
            "logo_application": "always",
            "logo_asset_identity": {
                "provider": "google_drive",
                "asset_id": "official-logo-asset",
                "sha256": "1" * 64,
            },
            "applied_user_directives": {
                "channel": ["logo in lower-right corner"],
            },
        }

    def test_builder_does_not_leak_logo_identity_or_full_contract(self):
        brief = self.mod.build_base_generation_brief(
            self._contract(),
            "A",
            "Calm professional discussion around a table, natural light, vertical composition.",
            {"preferred_region": "lower-right", "keep_clear": True},
        )
        serialized = json.dumps(brief, sort_keys=True)
        self.assertNotIn("official-logo-asset", serialized)
        self.assertNotIn("google_drive", serialized)
        self.assertNotIn("1" * 64, serialized)
        self.assertNotIn("logo_application", serialized)
        self.assertNotIn("logo_asset_identity", serialized)
        self.assertEqual(brief["generator_constraints"]["project_branding"], "exclude")
        self.assertEqual(brief["generator_constraints"]["watermarks"], "exclude")

    def test_creative_prompt_rejects_logo_instruction(self):
        with self.assertRaisesRegex(
            self.mod.BaseGenerationBriefError,
            "brand-composition instructions",
        ):
            self.mod.build_base_generation_brief(
                self._contract(),
                "A",
                "Calm professional scene with the project logo in the lower-right corner.",
            )

    def test_brief_rejects_brand_keys_if_added_after_build(self):
        brief = self.mod.build_base_generation_brief(
            self._contract(), "A", "Minimal professional scene with an open doorway."
        )
        brief["logo_asset_id"] = "should-not-be-here"
        with self.assertRaisesRegex(
            self.mod.BaseGenerationBriefError,
            "forbidden brand-composition keys",
        ):
            self.mod.validate_base_generation_brief(brief)

    def test_contracts_make_regeneration_default_for_pure_ai_contamination(self):
        social = (SKILL / "docs" / "architecture" / "capabilities" / "social-create-visual.md").read_text()
        brand = (SKILL / "docs" / "architecture" / "brand-assets-contract.md").read_text()
        visual = (SKILL / "docs" / "architecture" / "visual-generation-contract.md").read_text()
        checklist = (SKILL / "docs" / "architecture" / "social-execution-checklist.md").read_text()
        entrypoint = (SKILL / "SKILL.md").read_text()

        self.assertIn("base-generation brief", social)
        self.assertIn("must not receive the full effective visual contract", social)
        self.assertIn("reject and regenerate the base by default", social)
        self.assertIn("not the normal path for a disposable pure-AI base", brand)
        self.assertIn("Generator-input boundary", visual)
        self.assertIn("base drafts, not A/B/C review candidates", checklist)
        self.assertIn("brand-isolated base-generation brief", entrypoint)
        self.assertIn("compose the exact official logo before human review", entrypoint)


if __name__ == "__main__":
    unittest.main()
