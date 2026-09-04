#!/usr/bin/env python3
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
