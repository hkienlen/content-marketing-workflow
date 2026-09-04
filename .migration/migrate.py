#!/usr/bin/env python3
from __future__ import annotations

import runpy
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Execute the already-reviewed full migration script. It consumes the native
# GitHub artifact URL supplied by the existing bootstrap workflow.
runpy.run_path(str(ROOT / ".migration" / "migrate-full.py"), run_name="__main__")

# GitHub's workflow GITHUB_TOKEN can push normal source but is deliberately not
# allowed to add/delete workflow definitions. Restore the tracked bootstrap and
# remove newly generated permanent workflows from this bot commit. They are
# installed afterwards through the connected GitHub admin integration.
subprocess.run(
    ["git", "checkout", "HEAD", "--", ".github/workflows/bootstrap-migration.yml"],
    cwd=ROOT,
    check=True,
)
for rel in (
    ".github/workflows/ci.yml",
    ".github/workflows/release.yml",
):
    (ROOT / rel).unlink(missing_ok=True)
