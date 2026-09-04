#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import shutil
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "skill-package-manifest.json"
EPOCH = (1980, 1, 1, 0, 0, 0)


def write_bundle(source_root: Path, out: Path, skill_name: str) -> None:
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for path in sorted(p for p in source_root.rglob("*") if p.is_file()):
            arc = (Path(skill_name) / path.relative_to(source_root)).as_posix()
            info = zipfile.ZipInfo(arc, EPOCH)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            zf.writestr(info, path.read_bytes())


def main() -> None:
    cfg = json.loads(MANIFEST.read_text(encoding="utf-8"))
    version = (ROOT / cfg["version_file"]).read_text(encoding="utf-8").strip()
    source_root = ROOT / cfg["skill_source_root"]
    skill_version = (ROOT / cfg["skill_version_file"]).read_text(encoding="utf-8").strip()

    if not source_root.is_dir():
        raise SystemExit(f"skill source root missing: {source_root}")
    if not (source_root / "SKILL.md").is_file():
        raise SystemExit("canonical SKILL.md missing")
    if version != skill_version:
        raise SystemExit("canonical skill VERSION != repository VERSION")

    build = ROOT / "build"
    build.mkdir(exist_ok=True)

    skill_name = cfg["skill_name"]
    names = {
        kind: pattern.format(version=version)
        for kind, pattern in cfg["artifacts"].items()
    }
    outputs = {kind: build / name for kind, name in names.items()}

    for out in outputs.values():
        if out.exists():
            out.unlink()

    write_bundle(source_root, outputs["skill"], skill_name)
    shutil.copy2(outputs["skill"], outputs["zip"])

    print(f"SKILL_SOURCE={source_root}")
    for kind, out in outputs.items():
        print(f"{kind.upper()}={out}")
        print(f"{kind.upper()}_SHA256={hashlib.sha256(out.read_bytes()).hexdigest()}")


if __name__ == "__main__":
    main()
