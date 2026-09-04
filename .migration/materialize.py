#!/usr/bin/env python3
from __future__ import annotations

import base64
import shutil
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PARTS = sorted((ROOT / ".migration").glob("archive.part*"))
if not PARTS:
    raise SystemExit("no archive parts found")
encoded = "".join(p.read_text(encoding="ascii") for p in PARTS)
raw = base64.b64decode(encoded, validate=True)

with tempfile.TemporaryDirectory() as td_raw:
    td = Path(td_raw)
    archive = td / "canonical-source.zip"
    archive.write_bytes(raw)
    with zipfile.ZipFile(archive) as zf:
        bad = zf.testzip()
        if bad:
            raise SystemExit(f"corrupt source archive member: {bad}")
        zf.extractall(td / "source")
    source = td / "source"
    required = [
        source / ".codex-plugin/plugin.json",
        source / "skills/content-marketing-workflow/SKILL.md",
        source / "AGENTS.md",
        source / "tools/build-release.py",
        source / "tests/test_repository.py",
    ]
    missing = [str(p.relative_to(source)) for p in required if not p.is_file()]
    if missing:
        raise SystemExit(f"source archive missing required files: {missing}")
    for child in source.iterdir():
        target = ROOT / child.name
        if child.name in {".git", "build"}:
            continue
        if child.is_dir():
            shutil.copytree(child, target, dirs_exist_ok=True)
        else:
            shutil.copy2(child, target)

# Bootstrap material is never part of the canonical final tree.
shutil.rmtree(ROOT / ".migration", ignore_errors=True)
(ROOT / ".github/workflows/bootstrap-migration.yml").unlink(missing_ok=True)
