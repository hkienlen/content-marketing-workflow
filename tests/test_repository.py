import json, subprocess, unittest, zipfile
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
