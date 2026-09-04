#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import shutil
import tempfile
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
URL = os.environ["SOURCE_ARTIFACT_URL"]


def write(path: str, content: str) -> None:
    p = ROOT / path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


with tempfile.TemporaryDirectory() as td_raw:
    td = Path(td_raw)
    wrapper = td / "artifact.zip"
    urllib.request.urlretrieve(URL, wrapper)
    with zipfile.ZipFile(wrapper) as zf:
        zf.extractall(td / "wrapper")
    inner = next((td / "wrapper").glob("content-marketing-workflow-0.1.0.zip"))
    with zipfile.ZipFile(inner) as zf:
        zf.extractall(td / "plugin")
    source = td / "plugin" / "content-marketing-workflow"
    if not source.is_dir():
        raise SystemExit("missing plugin root in source artifact")
    for child in source.iterdir():
        target = ROOT / child.name
        if child.name == "SOURCE.json":
            continue
        if child.is_dir():
            shutil.copytree(child, target, dirs_exist_ok=True)
        else:
            shutil.copy2(child, target)

write(
    "README.md",
    """# Content Marketing Workflow

**Content Marketing Workflow** is the canonical source repository for the OpenAI plugin `content-marketing-workflow`.

Current version: `0.1.0`

```text
content-marketing-workflow
├── .codex-plugin/plugin.json
└── skills/content-marketing-workflow/SKILL.md
```

The plugin contains one primary skill. SEO, article, visual, WordPress, social, scheduling, publication, verification and notification behaviors remain internal capabilities of that single skill.

## Canonical source

From the migration recorded on 2026-09-04, corrections, evolutions, release preparation and versioning of the generic plugin are performed in this repository.

The former private repository `hkienlen/herve-kienlen-seo` remains a pilot/integration environment only. It is not a source for future generic plugin releases.

## Repository versus release package

The repository contains development/release tooling in addition to the installable plugin payload. `tools/build-release.py` creates the clean release ZIP from an explicit allowlist and generates `SOURCE.json` with the exact canonical commit SHA used for that build.

The installable payload contains:

- `.codex-plugin/plugin.json`;
- `skills/content-marketing-workflow/**`;
- `README.md`;
- `VERSION`;
- generated `SOURCE.json`.

Repository-only files such as tests, CI, migration notes and development instructions are not copied into the installable ZIP.

## Versioning

The plugin follows Semantic Versioning. `VERSION` and `.codex-plugin/plugin.json` must contain the same version. Release notes are maintained in `CHANGELOG.md`.

`SEO Workflow Bridge` is bundled as a WordPress companion resource and keeps its own independent versioning.

## Safety boundary

Generic source and release artifacts must not contain user/project content, pilot identities/configuration, live provider IDs, exact publication authorizations, credentials or user media. Runtime values belong to the active user's durable project state or external credential owner.
""",
)

write(
    "AGENTS.md",
    """# Repository Agent Instructions

## Authority

This repository is the **canonical source of the generic Content Marketing Workflow plugin**.

All generic product corrections, evolutions, packaging changes and versioning must be developed here. Do not use the former pilot repository `hkienlen/herve-kienlen-seo` as a source of generic plugin code. That repository may still be used for real integration validation and user/project state, but product changes discovered there must be ported back here through a normal branch/PR before release.

## Product architecture

- plugin name: `content-marketing-workflow`;
- display name: `Content Marketing Workflow`;
- one primary skill: `skills/content-marketing-workflow`;
- internal capability names are not separate installable skills;
- `SEO Workflow Bridge` is a bundled WordPress companion and retains independent versioning.

## Development workflow

1. Branch from current `main`.
2. Make the smallest coherent product change.
3. Update contracts/docs/tests when behavior changes.
4. Keep `VERSION` and `.codex-plugin/plugin.json` synchronized.
5. Run `python3 tests/test_repository.py`.
6. Run `python3 tools/build-release.py --source-sha <40-hex-sha>` when validating packaging.
7. Open a PR, require green CI, then merge.
8. Build releases from an exact merged `main` SHA only.

Routine GitHub mechanics are implementation plumbing; business/content publication gates defined by the skill remain authoritative.

## Generic-data boundary

Never commit or package:

- user/project strategy, articles, posts or live workflow state;
- site/account/provider IDs tied to one user;
- credentials, tokens, secrets or private keys;
- user media or source-user assets;
- exact publication authorizations or live publication evidence;
- pilot-specific profile names, hostnames, URLs or configuration as generic defaults.

Publisher/developer metadata in `.codex-plugin/plugin.json` is legitimate product metadata and is not user runtime data.

## Release/versioning

Use Semantic Versioning.

- patch: backwards-compatible bug fixes or contract corrections;
- minor: backwards-compatible new capabilities/features;
- major: breaking behavior/schema/package changes.

Update `CHANGELOG.md` for every released version. Do not edit a released artifact in place; create a new version from a new canonical SHA.
""",
)

write(
    "MIGRATION.md",
    """# Migration to the canonical repository

Date: 2026-09-04

`hkienlen/content-marketing-workflow` became the canonical generic product repository starting from **Content Marketing Workflow 0.1.0**.

The initial generic package was generated and validated in the former pilot/development repository from:

```text
hkienlen/herve-kienlen-seo
d89d1de1c2cbb47b68a75d3923003624e027cfc5
```

The verified 0.1.0 installable ZIP produced there had SHA-256:

```text
96b2dcdf797090371619ea8cadbabf071c17f62c5d374ac34883b2799f7da941
```

This provenance is historical only. Future generic release source SHAs belong to this repository.

The former repository remains available for pilot/integration validation and user-owned runtime state, but future product corrections, evolutions and versioning must be committed here.
""",
)

write(
    "CHANGELOG.md",
    """# Changelog

All notable changes to Content Marketing Workflow are documented here. The project follows Semantic Versioning.

## [Unreleased]

- Canonical development moved to `hkienlen/content-marketing-workflow`.
- Added self-contained release build and repository CI.
- Removed a pilot-specific WordPress presentation-profile identifier from generic documentation.

## [0.1.0] - 2026-09-04

- Initial plugin productization.
- One primary `content-marketing-workflow` skill with governed SEO, visual, WordPress and social capabilities.
- Explicit user/project data and credential boundaries.
- Bundled SEO Workflow Bridge companion.
- Initial release provenance: `hkienlen/herve-kienlen-seo@d89d1de1c2cbb47b68a75d3923003624e027cfc5`.
""",
)
write(".gitignore", "build/\n__pycache__/\n*.pyc\n.DS_Store\n")

manifest = {
    "schema_version": 1,
    "plugin_name": "content-marketing-workflow",
    "display_name": "Content Marketing Workflow",
    "version_file": "VERSION",
    "plugin_manifest": ".codex-plugin/plugin.json",
    "primary_skill_root": "skills/content-marketing-workflow",
    "include_roots": [".codex-plugin", "skills/content-marketing-workflow"],
    "include_files": ["README.md", "VERSION"],
    "generated_files": ["SOURCE.json"],
    "repository_only": [
        "AGENTS.md",
        "CHANGELOG.md",
        "MIGRATION.md",
        "plugin-package-manifest.json",
        ".github",
        "tests",
        "tools",
        ".gitignore",
    ],
    "canonical_repository": "https://github.com/hkienlen/content-marketing-workflow",
}
write("plugin-package-manifest.json", json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")

# Canonicalize source-authority contracts without changing product behavior.
replacements = {
    "skills/content-marketing-workflow/docs/architecture/single-skill-scope.md": [
        (
            "The product target is **one installable skill**. The private development repository is a real pilot laboratory, not the future clean distribution repository.",
            "The product is distributed as the **Content Marketing Workflow plugin containing one primary installable skill**. This canonical repository contains only generic product source; user/project state and real pilot validation live outside the distributable source.",
        ),
        (
            "The development pilot's implementation order does not define permanent network scope.",
            "The implementation order used during pilot validation does not define permanent network scope.",
        ),
    ],
    "skills/content-marketing-workflow/docs/architecture/testing-policy.md": [
        (
            "This policy defines how the single installable Content / Marketing skill and its internal capabilities are tested in the real pilot repository and connected external systems.",
            "This policy defines how the Content Marketing Workflow plugin, its single primary skill and its internal capabilities are tested in this canonical repository and, when necessary, in separately owned integration/pilot environments.",
        ),
        (
            "The pilot is not a disposable sandbox. It contains real strategy, content, GitHub history, external-media state, WordPress state and social workflow state.",
            "A real integration/pilot environment is not a disposable sandbox. It may contain real strategy, content, repository history, external-media state, WordPress state and social workflow state; none of that state belongs in this canonical generic repository.",
        ),
    ],
    "skills/content-marketing-workflow/docs/architecture/user-command-productization-checklist.md": [
        (
            "the package is assembled from the explicit allowlist in `skill-package-manifest.json`, never by copying the development repository wholesale;",
            "the primary skill payload follows `skill-package-manifest.json`, while the root release follows `plugin-package-manifest.json`; repository-only CI/tests/tools are excluded;",
        )
    ],
    "skills/content-marketing-workflow/docs/architecture/user-profile-data-contract.md": [
        ("Current development/pilot instance convention:", "A separate integration/pilot repository may use a convention such as:"),
        (
            "The development pilot predates the centralized profile and may already have useful user-specific operational files such as:",
            "A pre-existing integration/pilot project may already have useful user-specific operational files such as:",
        ),
        (
            "Historical pilot documents may remain in the development repository for traceability, but the packaging manifest/checklist must classify and exclude them from the installable skill.",
            "Historical pilot documents remain outside this canonical repository for traceability; the release boundary must never import them into the installable skill.",
        ),
    ],
    "skills/content-marketing-workflow/docs/architecture/wordpress-generic-boundary.md": [
        (
            "Historical direct WP-CLI/Python/shell import/injection scripts may remain in the pilot repository for traceability, diagnostics or explicitly chosen maintenance.",
            "Historical direct WP-CLI/Python/shell import/injection scripts may remain in a separate pilot/integration repository for traceability, diagnostics or explicitly chosen maintenance; they are not canonical generic product source.",
        )
    ],
    "skills/content-marketing-workflow/docs/architecture/business-model-extensibility.md": [
        (
            "For the future clean distribution package, the exact site/business profile schema may be finalized during productization after the current pilot contracts have been validated.",
            "In the canonical distribution source, site/business profile schemas may continue to evolve through versioned contracts as broader business models are validated.",
        )
    ],
    "skills/content-marketing-workflow/docs/architecture/wordpress-adapter-architecture.md": [
        (
            "wordpress/presentation/profiles/herve-kienlen-test/blog-article.json",
            "wordpress/presentation/profiles/<presentation-profile-id>/blog-article.json",
        )
    ],
}
for rel, pairs in replacements.items():
    p = ROOT / rel
    text = p.read_text(encoding="utf-8")
    for old, new in pairs:
        if old not in text:
            raise SystemExit(f"expected migration text missing in {rel}: {old}")
        text = text.replace(old, new)
    p.write_text(text, encoding="utf-8")

# Rewrite package boundary authorities for the canonical repository.
p = ROOT / "skills/content-marketing-workflow/docs/architecture/skill-package-manifest.json"
data = json.loads(p.read_text(encoding="utf-8"))
data["purpose"] = "Explicit generic payload boundary for the single primary content-marketing-workflow skill in the canonical Content Marketing Workflow repository. User/project/pilot data is never part of this repository or release payload."
data["notes"] = [
    "This manifest is relative to skills/content-marketing-workflow/ in the canonical repository.",
    "User/project strategy, content, runtime state, media and publication evidence live outside the canonical generic repository.",
    "Capability contracts may refer to user-owned runtime authorities; those references do not make user data part of the release payload.",
    "Raw social credentials, Telegram bot tokens and other credentials remain in external credential owners and are never committed.",
    "User-provided image originals and concrete visual preferences/provenance are runtime user/project data; only generic contracts, schemas and resolver code are packaged.",
]
p.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

p = ROOT / "skills/content-marketing-workflow/docs/architecture/skill-package-boundary.md"
t = p.read_text(encoding="utf-8")
idx = t.index("## Generic package content")
head = """# Skill package boundary

Date: 2026-09-04
Status: normative architecture contract

## Purpose

The canonical repository contains the generic Content Marketing Workflow product source. The primary skill payload is rooted at:

```text
skills/content-marketing-workflow/
```

The relative allowlist is:

```text
skills/content-marketing-workflow/docs/architecture/skill-package-manifest.json
```

User/project runtime state, live pilot evidence and credentials must remain outside this canonical repository and outside every release artifact.

## Primary invariant

```text
generic product source + explicit release allowlist
!=
user/project runtime state or pilot environment
```

The release contains models, schemas, generic capability behavior, reusable runtime code and the WordPress companion source.

"""
t = head + t[idx:]
t = t.replace(
    "These paths may remain in the private development/pilot repository. Their presence in the repository is not permission to package them.",
    "These paths are runtime/project authorities and must not exist as concrete user data in the canonical generic repository or release package.",
)
t = t.replace(
    "Historical pilot documents, dated UI observations, live-validation evidence and conversation handoffs are valuable development history. They are user/project evidence rather than product payload and remain excluded unless deliberately rewritten into a generic contract.",
    "Historical pilot documents, dated UI observations, live-validation evidence and conversation handoffs are user/project evidence rather than product payload. Keep them in the separate pilot/integration environment unless deliberately rewritten into a generic contract.",
)
t = t.replace("`tests/test_skill_package_user_data_boundary.py` validates:", "`tests/test_repository.py` in the canonical repository validates the release boundary, including:")
t = t.replace(
    "5. the pilot user profile contains no raw secret fields;\n6. the package does not include the pilot profile instance.",
    "5. repository-only development files are excluded from the release;\n6. known pilot identity/configuration markers are rejected from generic payload files.",
)
t = t.replace(
    "The skill/user-data separation is considered enforced only when the package manifest and CI boundary/pre-productization tests pass on the integration branch and on `main` after merge.",
    "The skill/user-data separation is considered enforced only when canonical repository CI and release-build validation pass on the change branch and on `main` after merge.",
)
t = t.replace(
    "Any package-relevant contract change after a recorded generation freeze invalidates that prior generation SHA for the next build. The resulting `main` must be revalidated and its exact new SHA recorded before skill generation.",
    "Any package-relevant change requires a new canonical `main` SHA for the next build. Release artifacts must record that exact source SHA in generated `SOURCE.json`.",
)
p.write_text(t, encoding="utf-8")

write(
    "skills/content-marketing-workflow/docs/architecture/skill-productization-freeze.md",
    """# Productization and release freeze

Date: 2026-09-04
Status: normative release contract

## Initial provenance

Content Marketing Workflow 0.1.0 was first generated and validated from the historical pilot/development source commit:

```text
hkienlen/herve-kienlen-seo@d89d1de1c2cbb47b68a75d3923003624e027cfc5
```

That SHA is historical provenance for 0.1.0 only. It is **not** the source for future generic releases.

## Canonical release sequence

```text
hkienlen/content-marketing-workflow main
-> dedicated change branch
-> update code/contracts/docs/tests/version as required
-> green canonical CI
-> merge
-> green CI on resulting main SHA
-> build clean ZIP from that exact SHA
-> generated SOURCE.json records that canonical SHA
-> publish/version artifact
```

## Freeze invariants

- future generic releases are sourced only from `hkienlen/content-marketing-workflow`;
- user/project state and pilot evidence remain outside the canonical repository;
- raw credentials remain in external credential owners;
- one plugin contains one primary skill with multiple internal capabilities;
- release assembly follows the root `plugin-package-manifest.json`;
- the primary-skill payload remains governed by `docs/architecture/skill-package-manifest.json`;
- a released artifact is immutable; a later correction requires a new Semantic Version and a new canonical source SHA.

## Acceptance

A release freeze is accepted only when:

1. branch/PR CI is green;
2. the change is merged;
3. CI on the resulting `main` SHA is green;
4. `tools/build-release.py` builds successfully from that exact SHA;
5. the ZIP passes integrity and repository-boundary tests;
6. generated `SOURCE.json.source_commit_sha` equals the exact canonical `main` SHA.
""",
)

write(
    "tools/build-release.py",
    r'''#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, re, shutil, subprocess, zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
MANIFEST=ROOT/'plugin-package-manifest.json'
HEX40=re.compile(r'^[0-9a-f]{40}$')
def source_sha(arg):
    value=(arg or subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()).lower()
    if not HEX40.fullmatch(value): raise SystemExit(f'invalid source SHA: {value!r}')
    return value
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--source-sha'); args=ap.parse_args(); sha=source_sha(args.source_sha)
    cfg=json.loads(MANIFEST.read_text()); version=(ROOT/'VERSION').read_text().strip(); plugin=json.loads((ROOT/cfg['plugin_manifest']).read_text())
    if plugin.get('name')!=cfg['plugin_name']: raise SystemExit('plugin name mismatch')
    if plugin.get('version')!=version: raise SystemExit('plugin version != VERSION')
    build=ROOT/'build'; stage=build/cfg['plugin_name']
    if build.exists(): shutil.rmtree(build)
    stage.mkdir(parents=True)
    for rel in cfg['include_roots']:
        shutil.copytree(ROOT/rel,stage/rel,dirs_exist_ok=True)
    for rel in cfg['include_files']:
        dst=stage/rel; dst.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(ROOT/rel,dst)
    source={'plugin_name':cfg['plugin_name'],'version':version,'canonical_repository':cfg['canonical_repository'],'source_commit_sha':sha,'initial_migration_provenance':{'repository':'hkienlen/herve-kienlen-seo','source_commit_sha':'d89d1de1c2cbb47b68a75d3923003624e027cfc5'}}
    (stage/'SOURCE.json').write_text(json.dumps(source,indent=2)+'\n')
    out=build/f"{cfg['plugin_name']}-{version}.zip"; epoch=(1980,1,1,0,0,0)
    with zipfile.ZipFile(out,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as zf:
        for path in sorted(p for p in stage.rglob('*') if p.is_file()):
            arc=(Path(cfg['plugin_name'])/path.relative_to(stage)).as_posix(); info=zipfile.ZipInfo(arc,epoch); info.compress_type=zipfile.ZIP_DEFLATED; info.external_attr=0o100644<<16; zf.writestr(info,path.read_bytes())
    print(f'PLUGIN_ROOT={stage}'); print(f'ZIP={out}'); print(f'ZIP_SHA256={hashlib.sha256(out.read_bytes()).hexdigest()}'); print(f'SOURCE_SHA={sha}')
if __name__=='__main__': main()
''',
)

write(
    "tests/test_repository.py",
    r'''import json, subprocess, unittest, zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; PLUGIN='content-marketing-workflow'; SKILL=ROOT/'skills'/PLUGIN
FORBIDDEN=('herve-kienlen.fr','test.herve-kienlen.fr','herve-kienlen-test','1295856430281172','1393894106025540','1001161786328866','KrWafn7y3E')
TEXT={'.md','.json','.yaml','.yml','.py','.php','.txt','.sh','.bash'}
class RepositoryTests(unittest.TestCase):
    def test_identity_and_version(self):
        v=(ROOT/'VERSION').read_text().strip(); p=json.loads((ROOT/'.codex-plugin/plugin.json').read_text()); self.assertEqual(p['name'],PLUGIN); self.assertEqual(p['version'],v); self.assertIn('name: content-marketing-workflow',(SKILL/'SKILL.md').read_text())
    def test_canonical_authority(self):
        self.assertIn('canonical source repository',(ROOT/'README.md').read_text()); self.assertIn('canonical source of the generic Content Marketing Workflow plugin',(ROOT/'AGENTS.md').read_text())
    def test_no_known_pilot_identity_in_generic_payload(self):
        bad=[]
        for root in (ROOT/'.codex-plugin',SKILL):
            for path in root.rglob('*'):
                if path.is_file() and path.suffix.lower() in TEXT:
                    text=path.read_text(errors='ignore')
                    for marker in FORBIDDEN:
                        if marker in text: bad.append(f'{path.relative_to(ROOT)} contains {marker}')
        self.assertEqual(bad,[],'\n'.join(bad))
    def test_release_build(self):
        fake='0123456789abcdef0123456789abcdef01234567'; subprocess.run(['python3','tools/build-release.py','--source-sha',fake],cwd=ROOT,check=True,capture_output=True,text=True); v=(ROOT/'VERSION').read_text().strip(); z=ROOT/'build'/f'{PLUGIN}-{v}.zip'; self.assertTrue(z.is_file())
        with zipfile.ZipFile(z) as zf:
            names=set(zf.namelist()); prefix=f'{PLUGIN}/'; self.assertIn(prefix+'.codex-plugin/plugin.json',names); self.assertIn(prefix+f'skills/{PLUGIN}/SKILL.md',names); self.assertIn(prefix+'SOURCE.json',names)
            for blocked in ('AGENTS.md','CHANGELOG.md','MIGRATION.md','plugin-package-manifest.json','tests/','tools/'):
                self.assertFalse(any(n==prefix+blocked or n.startswith(prefix+blocked) for n in names),blocked)
            source=json.loads(zf.read(prefix+'SOURCE.json')); self.assertEqual(source['source_commit_sha'],fake); self.assertEqual(source['canonical_repository'],'https://github.com/hkienlen/content-marketing-workflow')
if __name__=='__main__': unittest.main()
''',
)

write(
    ".github/workflows/ci.yml",
    """name: Test Content Marketing Workflow

on:
  pull_request:
  push:
    branches: [main]

permissions:
  contents: read

jobs:
  test-and-build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - name: Validate canonical repository
        run: python3 tests/test_repository.py
      - name: Build exact plugin artifact
        run: python3 tools/build-release.py --source-sha "$GITHUB_SHA"
      - name: Verify ZIP integrity
        run: unzip -t "build/content-marketing-workflow-$(cat VERSION).zip"
      - name: Emit SHA-256
        run: sha256sum "build/content-marketing-workflow-$(cat VERSION).zip"
      - name: Upload installable plugin artifact
        uses: actions/upload-artifact@v4
        with:
          name: content-marketing-workflow-${{ github.sha }}
          path: build/content-marketing-workflow-*.zip
          if-no-files-found: error
          retention-days: 30
""",
)

write(
    ".github/workflows/release.yml",
    """name: Build tagged release

on:
  push:
    tags:
      - 'v*'

permissions:
  contents: write

jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - name: Validate tag equals VERSION
        run: |
          test "${GITHUB_REF_NAME}" = "v$(cat VERSION)"
          python3 tests/test_repository.py
      - name: Build exact release
        run: python3 tools/build-release.py --source-sha "$GITHUB_SHA"
      - name: Publish GitHub release
        env:
          GH_TOKEN: ${{ github.token }}
        run: |
          sha256sum "build/content-marketing-workflow-$(cat VERSION).zip" > "build/content-marketing-workflow-$(cat VERSION).zip.sha256"
          gh release create "$GITHUB_REF_NAME" \
            "build/content-marketing-workflow-$(cat VERSION).zip" \
            "build/content-marketing-workflow-$(cat VERSION).zip.sha256" \
            --title "Content Marketing Workflow $(cat VERSION)" \
            --generate-notes
""",
)

# One-shot bootstrap removes itself before committing final source.
(ROOT / ".migration/migrate.py").unlink()
(ROOT / ".github/workflows/bootstrap-migration.yml").unlink(missing_ok=True)
try:
    (ROOT / ".migration").rmdir()
except OSError:
    pass
