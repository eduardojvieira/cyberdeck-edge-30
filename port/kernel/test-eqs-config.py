#!/usr/bin/env python3
"""Host-only regression checks; never invoke a flasher or access a device."""
from pathlib import Path
import os
import subprocess
import tempfile
import unittest


HERE = Path(__file__).resolve().parent
REQUIRED = """EQS_DTB SCSI_UFS_HID ZRAM_WRITEBACK RICHTAP_FOR_PMIC_ENABLE
DEVTMPFS VT VT_CONSOLE FHANDLE SYSVIPC NAMESPACES UTS_NS IPC_NS PID_NS USER_NS NET_NS
CGROUPS CGROUP_PIDS CGROUP_DEVICE INOTIFY_USER SIGNALFD TIMERFD EPOLL NET UNIX
PROC_FS SYSFS TMPFS BINFMT_ELF BLK_DEV_DM EXT4_FS
PSTORE PSTORE_RAM PSTORE_CONSOLE IKCONFIG IKCONFIG_PROC
MODULES MODVERSIONS CFI_CLANG INPUT_JOYDEV
BT BT_BREDR BT_LE BT_HIDP BT_RFCOMM BT_RFCOMM_TTY BT_HCIVHCI UHID
BT_BNEP BT_BNEP_MC_FILTER BT_BNEP_PROTO_FILTER""".split()


class EqsConfigTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.config = Path(self.tmp.name) / '.config'
        self.values = {f'CONFIG_{name}': 'y' for name in REQUIRED}
        self.values.update(CONFIG_KEYBOARD_GPIO_SWAP='m', CONFIG_LTO_CLANG_THIN='y')

    def check(self, values=None, profile='thinlto'):
        values = self.values if values is None else values
        self.config.write_text(''.join(f'{key}={value}\n' for key, value in values.items()))
        return subprocess.run(['bash', str(HERE / 'resolve-eqs-config.sh'),
                               '--check', str(self.config), profile],
                              capture_output=True, text=True, timeout=60)

    def test_rejects_missing_halium_config(self):
        values = self.values.copy()
        for name in ('DEVTMPFS', 'SYSVIPC', 'IPC_NS', 'PID_NS', 'VT', 'FHANDLE'):
            values.pop(f'CONFIG_{name}')
        result = self.check(values)
        self.assertNotEqual(result.returncode, 0, 'incomplete Android config was accepted')
        self.assertIn('CONFIG_DEVTMPFS=y', result.stderr)

    def test_accepts_complete_profile(self):
        result = self.check()
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_rejects_each_missing_requirement(self):
        for name in REQUIRED:
            with self.subTest(symbol=name):
                values = self.values.copy()
                values.pop(f'CONFIG_{name}')
                result = self.check(values)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(f'CONFIG_{name}=y', result.stderr)

    def test_rejects_modular_early_requirement(self):
        self.values['CONFIG_DEVTMPFS'] = 'm'
        self.assertNotEqual(self.check().returncode, 0)

    def test_rejects_wrong_lto_profile(self):
        self.values.pop('CONFIG_LTO_CLANG_THIN')
        self.values['CONFIG_LTO_CLANG_FULL'] = 'y'
        self.assertNotEqual(self.check().returncode, 0)
        self.assertEqual(self.check(profile='full').returncode, 0)

    def test_rejects_conflicting_lto(self):
        self.values['CONFIG_LTO_CLANG_FULL'] = 'y'
        self.assertNotEqual(self.check().returncode, 0)

    def test_rejects_unknown_profile(self):
        self.assertNotEqual(self.check(profile='bronco').returncode, 0)

    def test_rejects_duplicate_symbol(self):
        self.check()
        with self.config.open('a') as output:
            output.write('CONFIG_DEVTMPFS=m\n')
        result = subprocess.run(['bash', str(HERE / 'resolve-eqs-config.sh'),
                                 '--check', str(self.config), 'thinlto'],
                                capture_output=True, text=True, timeout=10)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('duplicate configuration: CONFIG_DEVTMPFS', result.stderr)

    def test_package_rejects_old_config_before_docker_or_cleanup(self):
        work = Path(self.tmp.name) / 'kernel work'
        for name in ('dt-images-dev/dtb.img', 'dt-images-dev/dtbo.img',
                     'out/arch/arm64/boot/Image', 'eqs-dev-packages/KEEP'):
            path = work / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('preserved evidence')
        values = self.values.copy()
        values.pop('CONFIG_DEVTMPFS')
        (work / 'out/.config').write_text(''.join(f'{k}={v}\n' for k, v in values.items()))
        fake_bin = Path(self.tmp.name) / 'bin'
        fake_bin.mkdir()
        docker_called = Path(self.tmp.name) / 'docker-called'
        docker = fake_bin / 'docker'
        docker.write_text('#!/bin/sh\nprintf called > "$DOCKER_CALLED"\nexit 97\n')
        docker.chmod(0o755)
        env = dict(os.environ, EQS_KERNEL_WORKDIR=str(work),
                   PATH=f'{fake_bin}:{os.environ["PATH"]}', DOCKER_CALLED=str(docker_called))
        result = subprocess.run(['bash', str(HERE / 'build-dev-packages.sh'), '--reuse-gates'],
                                env=env, capture_output=True, text=True, timeout=10)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('CONFIG_DEVTMPFS=y', result.stderr)
        self.assertFalse(docker_called.exists())
        self.assertEqual((work / 'eqs-dev-packages/KEEP').read_text(), 'preserved evidence')

        # A valid config must not bypass the independent stale-module guard.
        (work / 'out/.config').write_text(''.join(f'{k}={v}\n' for k, v in self.values.items()))
        (work / 'out/modules.order').write_text('current.ko\n')
        (work / 'out/current.ko').write_bytes(b'current')
        (work / 'out/stale.ko').write_bytes(b'stale')
        result = subprocess.run(['bash', str(HERE / 'build-dev-packages.sh'), '--reuse-gates'],
                                env=env, capture_output=True, text=True, timeout=10)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unexpected=['stale.ko']", result.stderr)
        self.assertFalse(docker_called.exists())
        self.assertEqual((work / 'eqs-dev-packages/KEEP').read_text(), 'preserved evidence')


    def test_embedded_container_scripts_parse(self):
        cases = (
            ('build-host-artifacts.sh', "/bin/bash -euc '\n", "\n    ' build-host-artifacts"),
            ('build-dev-packages.sh', "/bin/bash -euo pipefail -c '\n", "\n    ' bash \"$VERSION\""),
        )
        for name, start, end in cases:
            with self.subTest(script=name):
                body = (HERE / name).read_text().split(start, 1)[1].split(end, 1)[0]
                result = subprocess.run(['bash', '-n'], input=body, text=True, capture_output=True)
                self.assertEqual(result.returncode, 0, result.stderr)

    def test_functional_charger_selects_eqs_wireless_layout(self):
        # Direct kernel make bypasses the module Makefile's TARGET_PRODUCT defaults.
        commands = [line for line in (HERE / 'build-host-artifacts.sh').read_text().splitlines()
                    if line.lstrip().startswith('make ') and 'M="$glink_charger"' in line]
        self.assertEqual(len(commands), 1)
        self.assertIn('CONFIG_WIRELESS_CPS4035B=m', commands[0])


if __name__ == '__main__':
    unittest.main()
