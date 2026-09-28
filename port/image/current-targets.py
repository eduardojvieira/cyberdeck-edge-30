#!/usr/bin/env python3
"""Print exact offline APT targets from the frozen current-package inputs."""
import json
from pathlib import Path
import sys
from urllib.parse import unquote

manifest = json.loads(Path(sys.argv[1]).read_text())
versions = dict(line.split('\t', 1) for line in Path(sys.argv[2]).read_text().splitlines())
seen = set()
for filename in sorted(manifest):
    name, encoded_version, architecture = filename.removesuffix('.deb').rsplit('_', 2)
    assert filename.endswith('.deb') and architecture in ('all', 'arm64'), filename
    version = versions[name]
    assert unquote(encoded_version) in (version, version.split(':')[-1]), filename
    assert name not in seen, name
    seen.add(name)
    print(f'{name}={version}')
assert len(seen) == len(manifest)
