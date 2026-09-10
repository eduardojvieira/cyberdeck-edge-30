#!/usr/bin/env python3
"""Host-only checks for the eqs bluebinder address hook; no Bluetooth access."""
from pathlib import Path
import subprocess
import tempfile
import unittest


SCRIPT = Path(__file__).parent / 'adaptation-motorola-eqs/usr/bin/droid/droid-get-bt-address.sh'
ADDRESS = 'A0:B1:C2:D3:E4:F5'


class BluetoothAddressTests(unittest.TestCase):
    def test_address_validation_and_preservation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config, output = root / 'bootconfig', root / 'bluetooth/board-address'

            def run(value):
                config.write_text(value)
                return subprocess.run(['sh', str(SCRIPT), str(config), str(output)],
                                      capture_output=True, text=True, timeout=5)

            valid = 'androidboot.btmacaddr = "a0:b1:c2:d3:e4:f5"\n'
            for value in ('', valid + valid, valid + 'androidboot.btmacaddr = "bad"\n',
                          'androidboot.btmacaddr = "00:00:00:00:00:00"\n',
                          'androidboot.btmacaddr = "FF:FF:FF:FF:FF:FF"\n',
                          'androidboot.btmacaddr = "A0:B1:C2:D3:E4:ZZ"\n',
                          'androidboot.btmacaddr = "A0:B1:C2:D3:E4:F5\n'):
                with self.subTest(value=value):
                    result = run(value)
                    self.assertNotEqual(result.returncode, 0)
                    self.assertFalse(output.exists())

            for value in (valid, f' androidboot.btmacaddr = {ADDRESS} \n'):
                result = run(value)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(output.read_text(), ADDRESS + '\n')
                self.assertEqual(output.stat().st_mode & 0o777, 0o644)
                self.assertNotIn(ADDRESS, result.stdout + result.stderr)

            output.write_text('10:20:30:40:50:60\n')
            self.assertNotEqual(run(valid).returncode, 0)
            self.assertEqual(output.read_text(), '10:20:30:40:50:60\n')
            output.unlink()
            victim = root / 'preserved'
            victim.write_text('preserve me')
            output.symlink_to(victim)
            self.assertNotEqual(run(valid).returncode, 0)
            self.assertEqual(victim.read_text(), 'preserve me')


if __name__ == '__main__':
    unittest.main()
