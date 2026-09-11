#!/usr/bin/env python3
"""Host-only rejection checks: test-build-package.py PINNED_SOURCE_TAR_GZ."""
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

base = Path(__file__).resolve().parent
if len(sys.argv) != 2:
    raise SystemExit(__doc__)
archive = Path(sys.argv[1]).resolve()


def rejected(script, source, output, error):
    result = subprocess.run(['bash', str(script), str(source), str(output)],
                            capture_output=True, text=True, timeout=15)
    assert result.returncode != 0, result
    assert error in result.stderr, result.stderr


with tempfile.TemporaryDirectory(prefix='eqs-package-guards-') as temp:
    work = Path(temp)
    script = base / 'build-package.sh'
    output = work / 'output'
    bad = work / 'bad.tar.gz'
    bad.write_bytes(b'not the pinned source')
    rejected(script, bad, output, 'source archive hash differs')
    assert not output.exists()
    output.mkdir()
    sentinel = output / 'preserve'
    sentinel.write_text('previous result')
    rejected(script, archive, output, 'output must not already exist')
    assert sentinel.read_text() == 'previous result'
    dangling = work / 'dangling'
    dangling.symlink_to(work / 'absent')
    rejected(script, archive, dangling, 'output must not already exist')
    assert dangling.is_symlink() and not (work / 'absent').exists()
    shutil.copyfile(script, work / script.name)
    (work / 'fix-session-safety.patch').write_text('unreviewed patch')
    rejected(work / script.name, archive, work / 'new-output', 'reviewed patch hash differs')
    assert not (work / 'new-output').exists()
    shutil.copyfile(base / 'fix-session-safety.patch', work / 'fix-session-safety.patch')
    (work / 'fix-navigation.patch').write_text('unreviewed navigation patch')
    rejected(work / script.name, archive, work / 'new-output', 'reviewed navigation patch hash differs')
    assert not (work / 'new-output').exists()
    shutil.copyfile(base / 'fix-navigation.patch', work / 'fix-navigation.patch')
    (work / 'fix-rotation.patch').write_text('unreviewed rotation patch')
    rejected(work / script.name, archive, work / 'new-output', 'reviewed rotation patch hash differs')
    assert not (work / 'new-output').exists()
    shutil.copyfile(base / 'fix-rotation.patch', work / 'fix-rotation.patch')
    (work / 'fix-locale.patch').write_text('unreviewed locale patch')
    rejected(work / script.name, archive, work / 'new-output', 'reviewed locale patch hash differs')
    assert not (work / 'new-output').exists()
    print('PASS: 7 host rejection checks; no compiler, package install or phone access')
