import json
import re
import subprocess
import unittest
import zipfile
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = "content-marketing-workflow"
PLUGIN_ROOT = ROOT / "plugins" / PLUGIN
CANONICAL_SKILL = ROOT / "skills" / PLUGIN
PLUGIN_SKILL = PLUGIN_ROOT / "skills" / PLUGIN
MARKETPLACE_PATH = ROOT / ".agents" / "plugins" / "marketplace.json"
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
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def text_files(root: Path):
    for path in root.rglob("*"):
        if not path.is_file() or ".git" in path.parts or "build" in path.parts:
            continue
        if path.suffix.lower() in TEXT_SUFFIXES:
            yield path


def file_map(root: Path):
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file()
    }


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
    def test_identity_version_and_distribution_layout(self):
        version = (ROOT / "VERSION").read_text().strip()
        plugin = json.loads((PLUGIN_ROOT / ".codex-plugin" / "plugin.json").read_text())
        interface = plugin.get("interface", {})

        self.assertEqual(plugin["name"], PLUGIN)
        self.assertEqual(plugin["version"], version)
        self.assertEqual(plugin.get("author"), {"name": "Content Marketing Workflow"})
        self.assertEqual(interface.get("developerName"), "Hervé Kienlen")
        self.assertEqual(interface.get("composerIcon"), "./assets/icon.png")
        self.assertEqual(interface.get("logo"), "./assets/logo.png")

        self.assertTrue((CANONICAL_SKILL / "SKILL.md").is_file())
        self.assertTrue((PLUGIN_SKILL / "SKILL.md").is_file())
        self.assertIn("name: content-marketing-workflow", (CANONICAL_SKILL / "SKILL.md").read_text())
        self.assertEqual((CANONICAL_SKILL / "VERSION").read_text().strip(), version)
        self.assertEqual((PLUGIN_SKILL / "VERSION").read_text().strip(), version)
        self.assertFalse((ROOT / ".codex-plugin").exists(), "plugin manifest must live under plugins/<name>")

        for relative in ("assets/icon.png", "assets/logo.png"):
            asset = PLUGIN_ROOT / relative
            self.assertTrue(asset.is_file(), relative)
            self.assertTrue(asset.read_bytes().startswith(PNG_SIGNATURE), relative)

        repository_icon = ROOT / "assets" / "repository-icon.png"
        self.assertTrue(repository_icon.is_file())
        self.assertTrue(repository_icon.read_bytes().startswith(PNG_SIGNATURE))

    def test_canonical_skill_and_plugin_mirror_are_identical(self):
        self.assertEqual(file_map(CANONICAL_SKILL), file_map(PLUGIN_SKILL))

    def test_marketplace_manifest_resolves_plugin_source(self):
        marketplace = json.loads(MARKETPLACE_PATH.read_text())
        self.assertEqual(marketplace["name"], PLUGIN)
        self.assertEqual(marketplace.get("interface", {}).get("displayName"), "Content Marketing Workflow")
        self.assertEqual(len(marketplace["plugins"]), 1)
        entry = marketplace["plugins"][0]
        self.assertEqual(entry["name"], PLUGIN)
        self.assertEqual(entry["source"], {"source": "local", "path": "./plugins/content-marketing-workflow"})
        self.assertEqual(entry["policy"], {"installation": "AVAILABLE", "authentication": "ON_INSTALL"})
        self.assertEqual(entry["category"], "Productivity")
        resolved = ROOT / entry["source"]["path"].removeprefix("./")
        self.assertEqual(resolved.resolve(), PLUGIN_ROOT.resolve())
        self.assertTrue((resolved / ".codex-plugin" / "plugin.json").is_file())

    def test_package_manifests_match_distribution_layout(self):
        plugin_cfg = json.loads((ROOT / "plugin-package-manifest.json").read_text())
        self.assertEqual(plugin_cfg["schema_version"], 3)
        self.assertEqual(plugin_cfg["plugin_source_root"], "plugins/content-marketing-workflow")
        self.assertEqual(plugin_cfg["marketplace_manifest"], ".agents/plugins/marketplace.json")
        self.assertEqual(plugin_cfg["plugin_manifest"], "plugins/content-marketing-workflow/.codex-plugin/plugin.json")
        self.assertEqual(plugin_cfg["primary_skill_root"], "skills/content-marketing-workflow")
        self.assertEqual(plugin_cfg["plugin_skill_mirror"], "plugins/content-marketing-workflow/skills/content-marketing-workflow")

        skill_cfg = json.loads((ROOT / "skill-package-manifest.json").read_text())
        self.assertEqual(skill_cfg["schema_version"], 1)
        self.assertEqual(skill_cfg["skill_name"], PLUGIN)
        self.assertEqual(skill_cfg["skill_source_root"], "skills/content-marketing-workflow")
        self.assertEqual(skill_cfg["skill_version_file"], "skills/content-marketing-workflow/VERSION")
        self.assertEqual(skill_cfg["plugin_skill_mirror"], "plugins/content-marketing-workflow/skills/content-marketing-workflow")

    def test_repository_has_no_runtime_user_state(self):
        for forbidden_root in ("user-data", "articles", "social", "strategy", "work-context"):
            self.assertFalse((ROOT / forbidden_root).exists(), forbidden_root)

    def test_repository_text_privacy_boundary(self):
        errors = []
        for path in text_files(ROOT):
            errors.extend(privacy_errors(str(path.relative_to(ROOT)), path.read_text(errors="ignore")))
        self.assertEqual(errors, [], "\n".join(errors))

    def test_direct_skill_build(self):
        subprocess.run(
            ["python3", "tools/build-skill.py"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        version = (ROOT / "VERSION").read_text().strip()
        skill_archive = ROOT / "build" / f"{PLUGIN}-{version}.skill"
        zip_archive = ROOT / "build" / f"{PLUGIN}-skill-{version}.zip"
        self.assertTrue(skill_archive.is_file())
        self.assertTrue(zip_archive.is_file())
        self.assertEqual(skill_archive.read_bytes(), zip_archive.read_bytes())

        with zipfile.ZipFile(skill_archive) as zf:
            names = set(zf.namelist())
            prefix = f"{PLUGIN}/"
            self.assertIn(prefix + "SKILL.md", names)
            self.assertIn(prefix + "VERSION", names)
            self.assertIn(prefix + "docs/architecture/chatgpt-skill-runtime.md", names)
            self.assertIn(prefix + "scripts", {n.rstrip("/") for n in names if n.startswith(prefix + "scripts/")} | {prefix + "scripts"})
            self.assertEqual(zf.read(prefix + "VERSION").decode().strip(), version)

            errors = []
            for info in zf.infolist():
                if info.is_dir():
                    continue
                self.assertEqual((info.external_attr >> 16) & 0o777, 0o644, info.filename)
                try:
                    text = zf.read(info.filename).decode("utf-8")
                except UnicodeDecodeError:
                    continue
                errors.extend(privacy_errors(info.filename, text))
            self.assertEqual(errors, [], "\n".join(errors))

    def test_plugin_release_build(self):
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
            self.assertIn(prefix + "assets/icon.png", names)
            self.assertIn(prefix + "assets/logo.png", names)
            self.assertIn(prefix + f"skills/{PLUGIN}/SKILL.md", names)
            self.assertIn(prefix + f"skills/{PLUGIN}/VERSION", names)
            self.assertIn(prefix + "README.md", names)
            self.assertIn(prefix + "VERSION", names)
            self.assertIn(prefix + "SOURCE.json", names)
            for blocked in (".agents/", "plugins/", "AGENTS.md", "CHANGELOG.md", "MIGRATION.md", "plugin-package-manifest.json", "skill-package-manifest.json", "tests/", "tools/"):
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
