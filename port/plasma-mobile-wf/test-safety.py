#!/usr/bin/env python3
"""Offline host regression against pinned source, never PAM/phone/flash.

Usage: test-safety.py SOURCE [--upstream] [--case CASE]
Default applies the local patch to a temporary source copy. --upstream proves RED.
"""
import argparse
import hashlib
import os
from pathlib import Path
import re
import resource
import shlex
import shutil
import subprocess
import tempfile

BASE = Path(__file__).resolve().parent
PINS = {
    'sessionlockplugin/sessionlock.cpp': '7aef85df867a48bf2d6f062b511dd1afc4e4b7d0f8211a2df222eb8f645f0c3b',
    'sessionlockplugin/sessionlock.h': 'c334fa8e0dfaa13c9c3ca8057999a1714b0630294609b88d1e07c6b35459c45f',
    'wayfireipcplugin/wayfireipc.cpp': '63624444d96eae2f13dcf97ec4eef91dba1c099621c87bae98ad633d06e27a33',
    'wayfireipcplugin/wayfireipc.h': '94dbf2488ca3ee6c8b4d74927b47d839781de63b65675c553b0d02b52288d0aa',
}
CASES = (
    'pam-success', 'pam-auth-failure', 'pam-start-failure', 'pam-account-failure', 'pam-end-failure',
    'pam-conversation', 'pam-invalid-conversation', 'pam-oom-array', 'pam-oom-response', 'pam-null-input',
    'ipc-complete', 'ipc-fragmented', 'ipc-invalid-length', 'ipc-zero-length', 'ipc-invalid-json',
    'ipc-json-array', 'ipc-eof', 'ipc-batch', 'ipc-ownership', 'ipc-max-length',
    'nav-home', 'nav-close', 'nav-guard', 'nav-overview', 'nav-timeout', 'nav-bad-reply', 'nav-focus-change',
)

NAV_QML = (
    'containments/taskpanel/package/contents/ui/NavigationPanelComponent.qml',
    'components/mobileshell/qml/homescreen/HomeScreen.qml',
    'containments/homescreens/folio/package/contents/ui/main.qml',
    'components/mobileshell/qml/wayfiretweaks/WayfireTweaks.qml',
)


def run(command, **kwargs):
    return subprocess.run(command, check=True, timeout=120, **kwargs)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('--upstream', action='store_true')
    parser.add_argument('--no-navigation', action='store_true', help='test installed eqs1 safety patch without the navigation fix')
    parser.add_argument('--case', choices=CASES)
    args = parser.parse_args()
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    for path, digest in PINS.items():
        assert hashlib.sha256((args.source / 'components' / path).read_bytes()).hexdigest() == digest, path
    with tempfile.TemporaryDirectory(prefix='plasma-test-') as temp:
        work = Path(temp)
        for path in PINS:
            target = work / 'components' / path
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(args.source / 'components' / path, target)
        if not args.upstream:
            patch = ['patch', '-p1', '--batch', '--forward', '--fuzz=0', '-i', str(BASE / 'fix-session-safety.patch')]
            run(patch + ['--dry-run'], cwd=work)
            run(patch, cwd=work)
            if not args.no_navigation:
                for path in NAV_QML:
                    target = work / path
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(args.source / path, target)
                patch = ['patch', '-p1', '--batch', '--forward', '--fuzz=0', '-i', str(BASE / 'fix-navigation.patch')]
                run(patch + ['--dry-run'], cwd=work)
                run(patch, cwd=work)
        source = (work / 'components/sessionlockplugin/sessionlock.cpp').read_text()
        # Compile the exact PAM callbacks/methods, not a reimplementation. The UI
        # methods depend on private Wayland/KDE libraries outside this host test.
        prefix = source.split('SessionLock::SessionLock(', 1)[0]
        prefix = re.sub(r'^#include[^\n]*\n', '', prefix, flags=re.MULTILINE)
        methods = source.split('int SessionLock::authenticate(', 1)[1].split('void SessionLock::screenAdded(', 1)[0]
        (work / 'auth-under-test.inc').write_text(prefix + 'int SessionLock::authenticate(' + methods)
        flags = shlex.split(subprocess.check_output(['pkg-config', '--cflags', '--libs', 'Qt6Qml', 'Qt6Network'], text=True))
        qt = subprocess.check_output(['pkg-config', '--variable=libexecdir', 'Qt6Core'], text=True).strip()
        ipc = work / 'components/wayfireipcplugin'
        run([str(Path(qt) / 'moc'), *[f for f in flags if f.startswith(('-I', '-D'))], str(ipc / 'wayfireipc.h'), '-o', str(work / 'moc.cpp')])
        run(['clang++', '-std=c++17', '-O0', '-g', '-fno-omit-frame-pointer', '-fsanitize=address,undefined',
             '-I' + str(work), '-I' + str(ipc), str(BASE / 'test-safety.cpp'), str(work / 'moc.cpp'),
             *flags, '-o', str(work / 'test-safety')])
        cases = [args.case] if args.case else CASES
        env = {**os.environ, 'EQS_TEST_RUNTIME': str(work), 'ASAN_OPTIONS': 'symbolize=0:detect_leaks=1',
               'UBSAN_OPTIONS': 'halt_on_error=1:print_stacktrace=0'}
        failed = []
        for case in cases:
            result = subprocess.run([str(work / 'test-safety'), case], env=env, timeout=15,
                                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            print(f'{case}: {"PASS" if result.returncode == 0 else "FAIL"} (exit {result.returncode})', flush=True)
            if result.returncode:
                print(result.stdout)
                failed.append(case)
        assert not failed, failed
        print(f'PASS: {len(cases)} host regressions; Qt ' + subprocess.check_output(
            ['pkg-config', '--modversion', 'Qt6Core'], text=True).strip() + '; no ARM64/HIL claim')


if __name__ == '__main__':
    main()
