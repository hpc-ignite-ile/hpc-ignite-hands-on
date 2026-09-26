"""Guard the learner-facing Thai content and the public/private boundary."""
from pathlib import Path
import re
import subprocess
import unittest

ROOT=Path(__file__).resolve().parents[1]

def tracked():
    return subprocess.check_output(['git','ls-files','-z'],cwd=ROOT,text=True).split('\0')

class PublicTutorials(unittest.TestCase):
    def test_no_operational_artifacts_or_private_paths(self):
        for name in filter(None,tracked()):
            self.assertFalse(name.startswith(('docs/lanta-runs/','docs/tutorial-evidence/','docs/images/run-evidence/','benchmarks/real/','slurm/qualification/')),name)
            if name.endswith(('.md','.sbatch','.sh')):
                text=(ROOT/name).read_text()
                for forbidden in ('pv915002','/home/ubuntu/lanta/','/wdiazcar/','performance-rerun:start','resource-learning:start','hpc-ignite-backstage','docs/lanta-runs','tutorial-evidence/'):
                    self.assertNotIn(forbidden,text,(name,forbidden))

    def test_markdown_local_links_exist(self):
        for name in filter(None,tracked()):
            if not name.endswith('.md'): continue
            p=ROOT/name
            text=re.sub(r'```.*?```','',p.read_text(),flags=re.S)
            for link in re.findall(r'\]\(([^)]+)\)',text):
                if link.startswith(('http:','https:','mailto:','#')): continue
                self.assertTrue((p.parent/link.split('#')[0]).exists(),(name,link))

    def test_thai_titles_and_no_english_prose_paragraphs(self):
        for name in filter(None,tracked()):
            if not name.endswith('.md'): continue
            text=(ROOT/name).read_text()
            self.assertRegex(text.splitlines()[0],r'[ก-๙]',name)
            prose=re.sub(r'```.*?```','',text,flags=re.S)
            for line in prose.splitlines():
                # Leave commands, file names and proper names unchanged.
                clean=re.sub(r'`[^`]*`|\([^)]*\)|<[^>]*>','',line)
                if len(re.findall(r'[A-Za-z]+',clean))>=8:
                    self.assertRegex(clean,r'[ก-๙]',(name,line))

    def test_reference_job_is_portable_and_fails_on_missing_environment(self):
        path=ROOT/'slurm/twinb-reference.sbatch'
        subprocess.run(['bash','-n',str(path)],check=True)
        text=path.read_text()
        self.assertIn('${TWINB_VENV:?',text)
        self.assertIn('${ENERGYPLUS_HOME:?',text)
        self.assertNotIn('--account=',text)

if __name__=='__main__': unittest.main()
