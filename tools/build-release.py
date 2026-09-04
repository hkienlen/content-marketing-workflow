#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "plugin-package-manifest.json"
HEX40 = re.compile(r"^[0-9a-f]{40}$")


def source_sha(arg: str | None) -> str:
    value = (arg or subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()).lower()
    if not HEX40.fullmatch(value):
        raise SystemExit(f"invalid source SHA: {value!r}")
    return value


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-sha")
    args = parser.parse_args()
    sha = source_sha(args.source_sha)

    cfg = json.loads(MANIFEST.read_text(encoding="utf-8"))
    version = (ROOT / cfg["version_file"]).read_text(encoding="utf-8").strip()
    source_root = ROOT / cfg["plugin_source_root"]
    plugin = json.loads((ROOT / cfg["plugin_manifest"]).read_text(encoding="utf-8"))

    if plugin.get("name") != cfg["plugin_name"]:
        raise SystemExit("plugin name mismatch")
    if plugin.get("version") != version:
        raise SystemExit("plugin version != VERSION")
    if not source_root.is_dir():
        raise SystemExit(f"plugin source root missing: {source_root}")

    build = ROOT / "build"
    stage = build / cfg["plugin_name"]
    if build.exists():
        shutil.rmtree(build)
    stage.mkdir(parents=True)

    for rel in cfg["include_roots"]:
        src = source_root / rel
        if not src.exists():
            raise SystemExit(f"plugin include root missing: {src}")
        shutil.copytree(src, stage / rel, dirs_exist_ok=True)

    for rel in cfg["include_files"]:
        src = ROOT / rel
        if not src.is_file():
            raise SystemExit(f"repository include file missing: {src}")
        dst = stage / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)

    source = {
        "plugin_name": cfg["plugin_name"],
        "version": version,
        "source_commit_sha": sha,
    }
    (stage / "SOURCE.json").write_text(json.dumps(source, indent=2) + "\n", encoding="utf-8")

    out = build / f"{cfg['plugin_name']}-{version}.zip"
    epoch = (1980, 1, 1, 0, 0, 0)
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for path in sorted(p for p in stage.rglob("*") if p.is_file()):
            arc = (Path(cfg["plugin_name"]) / path.relative_to(stage)).as_posix()
            info = zipfile.ZipInfo(arc, epoch)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            zf.writestr(info, path.read_bytes())

    print(f"PLUGIN_ROOT={stage}")
    print(f"ZIP={out}")
    print(f"ZIP_SHA256={hashlib.sha256(out.read_bytes()).hexdigest()}")
    print(f"SOURCE_SHA={sha}")


if __name__ == "__main__":
    main()
