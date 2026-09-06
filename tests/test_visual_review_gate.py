import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "content-marketing-workflow"
FREEZE_PATH = SKILL / "scripts" / "visual-contract-freeze.py"
GATE_PATH = SKILL / "scripts" / "visual-review-gate.py"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path.name}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class VisualReviewGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.freeze = load_module(FREEZE_PATH, "visual_contract_freeze_review_gate")
        cls.gate = load_module(GATE_PATH, "visual_review_gate")

    def _contract(self):
        return self.freeze.freeze_contract(
            {
                "content_kind": "social",
                "source_policy": {"visual_source": "ai_first"},
                "visual_guidelines_path": "strategy/visual-guidelines.md",
                "applied_user_directives": {
                    "project_global": [],
                    "channel": [],
                    "content_local": [],
                },
                "logo_application": "always",
                "logo_asset_identity": {
                    "provider": "google_drive",
                    "asset_id": "official-logo",
                    "sha256": "1" * 64,
                },
                "generic_defaults_applied": ["mobile readability"],
            }
        )

    def _candidate(self, candidate_id, revision, base_hex, review_hex):
        base_sha = base_hex * 64
        review_sha = review_hex * 64
        return {
            "candidate_id": candidate_id,
            "contract_revision": revision,
            "base_asset": {"sha256": base_sha},
            "base_logo_inspection": {"status": "clear", "method": "visual_inspection"},
            "review_asset": {"sha256": review_sha},
            "logo_composition_manifest": {
                "base": {"sha256": base_sha},
                "official_logo": {"sha256": "1" * 64},
                "output": {"sha256": review_sha},
            },
        }

    def _package(self):
        contract = self._contract()
        revision = contract["contract_revision"]
        return {
            "workflow_mode": "generated_or_materially_transformed",
            "effective_contract": contract,
            "candidates": [
                self._candidate("A", revision, "a", "d"),
                self._candidate("B", revision, "b", "e"),
                self._candidate("C", revision, "c", "f"),
            ],
        }

    def test_social_always_accepts_only_exact_official_logo_review_outputs(self):
        result = self.gate.validate_review_package(self._package())
        self.assertTrue(result["review_ready"])
        self.assertEqual(result["candidate_ids"], ["A", "B", "C"])
        self.assertEqual(result["logo_application"], "always")

    def test_social_always_rejects_unbranded_review_candidate(self):
        package = self._package()
        package["candidates"][0].pop("logo_composition_manifest")
        with self.assertRaisesRegex(
            self.gate.VisualReviewGateError,
            "requires deterministic official-logo composition evidence",
        ):
            self.gate.validate_review_package(package)

    def test_social_always_rejects_generated_or_unverified_branding_in_base(self):
        package = self._package()
        package["candidates"][1]["base_logo_inspection"] = {
            "status": "contains_generated_or_unverified_branding"
        }
        with self.assertRaisesRegex(
            self.gate.VisualReviewGateError,
            "base is not verified clear",
        ):
            self.gate.validate_review_package(package)

    def test_social_always_rejects_wrong_logo_sha(self):
        package = self._package()
        package["candidates"][2]["logo_composition_manifest"]["official_logo"]["sha256"] = "2" * 64
        with self.assertRaisesRegex(
            self.gate.VisualReviewGateError,
            "does not use the effective official logo SHA-256",
        ):
            self.gate.validate_review_package(package)

    def test_social_always_rejects_raw_output_bound_as_review_asset(self):
        package = self._package()
        candidate = package["candidates"][0]
        candidate["review_asset"]["sha256"] = candidate["base_asset"]["sha256"]
        candidate["logo_composition_manifest"]["output"]["sha256"] = candidate["base_asset"]["sha256"]
        with self.assertRaisesRegex(
            self.gate.VisualReviewGateError,
            "branded review output unexpectedly equals its clean base",
        ):
            self.gate.validate_review_package(package)

    def test_generated_review_requires_exactly_three_candidates(self):
        package = self._package()
        package["candidates"] = package["candidates"][:2]
        with self.assertRaisesRegex(
            self.gate.VisualReviewGateError,
            "exactly three candidates",
        ):
            self.gate.validate_review_package(package)

    def test_contracts_close_late_logo_failure_loophole(self):
        social = (SKILL / "docs" / "architecture" / "capabilities" / "social-create-visual.md").read_text()
        brand = (SKILL / "docs" / "architecture" / "brand-assets-contract.md").read_text()
        visual = (SKILL / "docs" / "architecture" / "visual-generation-contract.md").read_text()
        review = (SKILL / "docs" / "architecture" / "social-post-review-loop.md").read_text()

        self.assertIn("There is no `when technically possible` exception", social)
        self.assertIn("visual-review-gate.py", social)
        self.assertIn("generated/unverified project branding", social)
        self.assertIn("Review-ready branding gate", brand)
        self.assertIn("late-failure case", brand)
        self.assertIn("Drafts are not automatically review candidates", visual)
        self.assertIn("review-ready A/B/C", review)
        self.assertIn("do not require a full A/B/C restart", social)


if __name__ == "__main__":
    unittest.main()
