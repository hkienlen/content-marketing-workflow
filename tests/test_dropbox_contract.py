import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "content-marketing-workflow"


class DropboxProviderContractTests(unittest.TestCase):
    def read(self, relative: str) -> str:
        return (SKILL / relative).read_text()

    def test_runtime_declares_both_implemented_providers(self):
        matrix = self.read("docs/architecture/runtime-compatibility-matrix.md")
        self.assertIn("google_drive", matrix)
        self.assertIn("dropbox", matrix)
        self.assertIn("exactly one cloud-media provider is active per project", matrix)
        self.assertIn("Google Drive is the recommended/default choice", matrix)

    def test_dropbox_workspace_contract_is_packaged(self):
        contract = SKILL / "docs/architecture/dropbox-workspace.md"
        self.assertTrue(contract.is_file())
        text = contract.read_text()
        for required in (
            "source-user/",
            "proposals/",
            "final/",
            "tmp-outbox/",
            "public read-only shared link",
            "Never persist OAuth/access tokens in GitHub",
        ):
            self.assertIn(required, text)

    def test_provider_neutral_media_identity(self):
        media = self.read("docs/architecture/media-delivery-architecture.md")
        self.assertIn("source_provider: google_drive|dropbox|chat_upload", media)
        self.assertIn("provider: google_drive|dropbox", media)
        self.assertIn("Provider switching and migration", media)

    def test_asset_ingest_supports_dropbox(self):
        ingest = self.read("docs/architecture/capabilities/asset-ingest.md")
        self.assertIn("provider (`google_drive` or `dropbox`)", ingest)
        self.assertIn("source_provider: google_drive|dropbox|chat_upload", ingest)
        self.assertIn("explicit provider migration/rebinding", ingest)

    def test_article_and_social_visual_contracts_are_provider_neutral(self):
        article = self.read("docs/architecture/capabilities/seo-create-article.md")
        social = self.read("docs/architecture/capabilities/social-create-visual.md")
        self.assertIn("Implemented adapters are Google Drive and Dropbox", article)
        self.assertIn("Implemented adapters are Google Drive and Dropbox", social)

    def test_social_final_package_has_dropbox_text_artifact(self):
        final_package = self.read("docs/architecture/social-final-drive-package.md")
        self.assertIn("Social final cloud package contract", final_package)
        self.assertIn("### Dropbox", final_package)
        self.assertIn("UTF-8 plain-text file", final_package)
        self.assertIn("text_plain_utf8", final_package)

    def test_direct_runtime_and_skill_entrypoint_offer_dropbox(self):
        runtime = self.read("docs/architecture/chatgpt-skill-runtime.md")
        skill = self.read("SKILL.md")
        self.assertIn("Dropbox (`dropbox`)", runtime)
        self.assertIn("implemented providers are Google Drive and Dropbox", skill)


if __name__ == "__main__":
    unittest.main()
