#!/usr/bin/env python3
"""Read-only Edge APT check. APT_CONFIG may select an isolated status/index copy."""
import os
from pathlib import Path
import re
import shlex
import subprocess


def run(*args):
    return subprocess.check_output(args, text=True, timeout=300,
                                   env={**os.environ, "LC_ALL": "C"})


protected = {
    name for line in Path(__file__).with_name("protected-packages.txt").read_text().splitlines()
    for name in line.partition("#")[0].split()
}
assert protected and all(re.fullmatch(r"[a-z0-9][a-z0-9+.-]+", p) for p in protected)

# Check preferred versions, not the archive-default priority in the index lines.
probes = ("git", "curl", "neovim", "chromium")
policy = run("apt-cache", "policy", *probes)
blocks = re.split(r"(?m)^(\S+):\n", policy)
for name, body in zip(blocks[1::2], blocks[2::2]):
    priorities = []
    priority = None
    for line in body.splitlines():
        header = re.fullmatch(r"\s*(?:\*\*\*\s+)?\S+\s+(-?\d+)\s*", line)
        if header:
            priority = int(header[1])
        if "sid/main arm64 Packages" in line:
            priorities.append(priority)
    assert priorities and all(p == 991 for p in priorities), name + ":\n" + body
assert set(blocks[1::2]) == set(probes), policy

# APT_CONFIG must also govern the hold check; do not consult live dpkg in an
# isolated simulation. Read only the status file selected by APT itself.
setting = shlex.split(run("apt-config", "shell", "STATUS", "Dir::State::status/f"))
assert len(setting) == 1 and setting[0].startswith("STATUS="), setting
status = Path(setting[0].partition("=")[2]).read_text()
held = set()
for block in status.split("\n\n"):
    fields = dict(re.findall(r"^(Package|Status): (.*)$", block, re.M))
    if fields.get("Status") == "hold ok installed":
        held.add(fields["Package"])
assert protected <= held, "Missing installed holds: " + " ".join(sorted(protected - held))
print(f"PASS: Sid preferred for ordinary packages; {len(protected)} port packages held", flush=True)

plan = run("apt-get", "--simulate", "--no-remove", "--no-install-recommends",
           "--with-new-pkgs", "upgrade")
actions = re.findall(r"^(Inst|Remv) (\S+)", plan, re.M)
assert not any(op == "Remv" for op, _ in actions), plan
changed = {name.split(":")[0] for _, name in actions}
assert not protected & changed, "Protected changes: " + " ".join(sorted(protected & changed))
assert not any(p.startswith(("linux-image-", "linux-bootimage-")) for p in changed), plan
for line in plan.splitlines():
    if "upgraded," in line:
        print(line)
print("PASS: upgrade simulation does not remove packages or replace retained port components")
