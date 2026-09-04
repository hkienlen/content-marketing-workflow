import json
import re
import subprocess
import unittest
import zipfile
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = "content-marketing-workflow"
SKILL = ROOT / "skills" / PLUGIN
TEXT_SUFFIXES = {".md", ".json", ".yaml", ".yml", ".py", ".php", ".txt", ".sh", ".bash"}
ALLOWED_URL_HOSTS = {
    "api.github.com",
    "api.linkedin.com",
    "api.telegram.org",
    "drive.google.com",
    "drive.usercontent.google.com",
    "example.invalid",
    "graph.facebook.com",
    "json-schema.org",
    "token.actions.githubusercontent.com",
    "www.linkedin.com",
}
URL_RE = re.compile(r"https?://[^\s\)\]\}>\"'`]+", re.IGNORECASE)
FR_HOST_RE = re.compile(r"\b(?:[a-z0-9-]+\.)+[a-z0-9-]*\.fr\b", re.IGNORECASE)
EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
CONCRETE_POST_ID_RE = re.compile(r"\b20\d{2}-\d{4}\b")
PERSONALIZED_REVIEW_RE = re.compile(r"présenter le résultat à (?!l'utilisateur\b)[A-ZÀ-Ý][A-Za-zÀ-ÿ'-]+", re.IGNORECASE)
INTEGRATION_STATE_PATTERNS = (
    re.compile(r"\bcurrent\s+pilot\s+authorizations\b", re.IGNORECASE),
    re.compile(r"\bhistorical\s+live\s+pilot\s+evidence\b", re.IGNORECASE),
)


def text_files(root: Path):
    for path in root.rglob("*"):
        if not path.is_file() or ".git" in path.parts or "build" in path.parts:
            continue
        if path.suffix.lower() in TEXT_SUFFIXES:
            yield path


def privacy_errors(label: str, text: str):
    errors = []
    if FR_HOST_RE.search(text):
        errors.append(f"{label}: concrete .fr hostname")
    if EMAIL_RE.search(text):
        errors.append(f"{label}: email literal")
    if CONCRETE_POST_ID_RE.search(text):
        errors.append(f"{label}: concrete social post id")
    if PERSONALIZED_REVIEW_RE.search(text):
        errors.append(f"{label}: personalized review recipient")
    for pattern in INTEGRATION_STATE_PATTERNS:
        if pattern.search(text):
            errors.append(f"{label}: embedded integration-state record")
    for raw_url in URL_RE.findall(text):
        host = (urlparse(raw_url).hostname or "").lower()
        if not host or host in {"...", "*"}:
            continue
        if host not in ALLOWED_URL_HOSTS:
            errors.append(f"{label}: non-allowlisted URL host {host}")
    return errors


class RepositoryTests(unittest.TestCase):
    def test_identity_and_version(self):
        version = (ROOT / "VERSION").read_text().strip()
        plugin = json.loads((ROOT / ".codex-plugin/plugin.json").read_text())
        self.assertEqual(plugin["name"], PLUGIN)
        self.assertEqual(plugin["version"], version)
        self.assertEqual(plugin.get("author"), {"name": "Content Marketing Workflow"})
        self.assertEqual(plugin.get("interface", {}).get("developerName"), "Content Marketing Workflow")
        self.assertIn("name: content-marketing-workflow", (SKILL / "SKILL.md").read_text())

    def test_repository_has_no_runtime_user_state(self):
        for forbidden_root in ("user-data", "articles", "social", "strategy", "work-context"):
            self.assertFalse((ROOT / forbidden_root).exists(), forbidden_root)

    def test_repository_text_privacy_boundary(self):
        errors = []
        for path in text_files(ROOT):
            errors.extend(privacy_errors(str(path.relative_to(ROOT)), path.read_text(errors="ignore")))
        self.assertEqual(errors, [], "\n".join(errors))

    def test_release_build(self):
        fake = "0123456789abcdef0123456789abcdef01234567"
        subprocess.run(
            ["python3", "tools/build-release.py", "--source-sha", fake],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        version = (ROOT / "VERSION").read_text().strip()
        archive = ROOT / "build" / f"{PLUGIN}-{version}.zip"
        self.assertTrue(archive.is_file())
        with zipfile.ZipFile(archive) as zf:
            names = set(zf.namelist())
            prefix = f"{PLUGIN}/"
            self.assertIn(prefix + ".codex-plugin/plugin.json", names)
            self.assertIn(prefix + f"skills/{PLUGIN}/SKILL.md", names)
            self.assertIn(prefix + "SOURCE.json", names)
            for blocked in ("AGENTS.md", "CHANGELOG.md", "MIGRATION.md", "plugin-package-manifest.json", "tests/", "tools/"):
                self.assertFalse(any(n == prefix + blocked or n.startswith(prefix + blocked) for n in names), blocked)
            source = json.loads(zf.read(prefix + "SOURCE.json"))
            self.assertEqual(source["source_commit_sha"], fake)
            self.assertEqual(set(source), {"plugin_name", "version", "source_commit_sha"})
            errors = []
            for name in names:
                try:
                    text = zf.read(name).decode("utf-8")
                except (UnicodeDecodeError, IsADirectoryError):
                    continue
                errors.extend(privacy_errors(name, text))
            self.assertEqual(errors, [], "\n".join(errors))


if __name__ == "__main__":
    unittest.main()
