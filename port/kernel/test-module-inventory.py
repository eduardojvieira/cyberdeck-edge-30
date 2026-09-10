#!/usr/bin/env python3
"""Host-only checks for the module inventory used by packaging."""
import importlib.util
from pathlib import Path
import tempfile
import sys

sys.dont_write_bytecode = True
import unittest

SCRIPT = Path(__file__).with_name('check-module-inventory.py')


class InventoryTests(unittest.TestCase):
    def test_operational_media_contract(self):
        spec = importlib.util.spec_from_file_location('inventory', SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.assertIn('qcom/opensource/camera-kernel/camera.ko', module.EXTERNAL)
        self.assertIn('qcom/opensource/eva-kernel/msm/msm-eva.ko', module.EXTERNAL)
        self.assertIn('motorola/drivers/regulator/wl2868c/wl2868c.ko', module.EXTERNAL)
        self.assertIn('qcom/opensource/audio-kernel/asoc/machine_dlkm.ko', module.EXTERNAL)
        self.assertIn('qcom/opensource/audio-kernel/dsp/adsp_loader_dlkm.ko', module.EXTERNAL)

    def test_inventory_contract(self):
        self.assertTrue(SCRIPT.exists(), 'packaging has no inventory guard')
        spec = importlib.util.spec_from_file_location('inventory', SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'modules.order').write_text('drivers/current.ko\n')
            (root / 'drivers').mkdir()
            current = root / 'drivers/current.ko'
            current.write_bytes(b'current')
            self.assertEqual(module.check(root, ['drivers/current.ko']), ['drivers/current.ko'])
            stale = root / 'drivers/stale.ko'
            stale.write_bytes(b'stale')
            with self.assertRaisesRegex(ValueError, 'unexpected.*stale'):
                module.check(root, ['drivers/current.ko'])
            stale.unlink()
            current.unlink()
            with self.assertRaisesRegex(ValueError, 'missing.*current'):
                module.check(root, ['drivers/current.ko'])
            current.write_bytes(b'')
            with self.assertRaisesRegex(ValueError, 'empty'):
                module.check(root, ['drivers/current.ko'])
            current.write_bytes(b'current')
            for invalid in ([], ['../outside.ko'], ['/outside.ko'],
                            ['drivers/current.ko', 'drivers/current.ko']):
                with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                    module.check(root, invalid)
            (root / 'other').mkdir()
            (root / 'other/current.ko').write_bytes(b'collision')
            with self.assertRaisesRegex(ValueError, 'basename'):
                module.check(root, ['drivers/current.ko', 'other/current.ko'])
            (root / 'other/current.ko').unlink()
            current.unlink()
            current.symlink_to(root / 'modules.order')
            with self.assertRaisesRegex(ValueError, 'symlink'):
                module.check(root, ['drivers/current.ko'])


if __name__ == '__main__':
    unittest.main()
