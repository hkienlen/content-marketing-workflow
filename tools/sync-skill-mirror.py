#!/usr/bin/env python3
from __future__ import annotations

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "skills" / "content-marketing-workflow"
MIRROR = ROOT / "plugins" / "content-marketing-workflow" / "skills" / "content-marketing-workflow"


def main() -> None:
    if not (SOURCE / "SKILL.md").is_file():
        raise SystemExit(f"canonical skill missing: {SOURCE}")
    if MIRROR.exists():
        shutil.rmtree(MIRROR)
    MIRROR.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(SOURCE, MIRROR)
    print(f"Synced {SOURCE.relative_to(ROOT)} -> {MIRROR.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
