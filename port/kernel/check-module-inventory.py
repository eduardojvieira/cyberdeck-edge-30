#!/usr/bin/env python3
"""Reject stale/missing modules before package cleanup; no hardware access."""
from pathlib import Path, PurePosixPath
import sys

# Explicit outputs of modules-dev-functional; its staging is rebuilt from scratch.
EXTERNAL = """
qcom/opensource/mmrm-driver/driver/msm-mmrm.ko
qcom/opensource/display-drivers/msm/msm_drm.ko
motorola/drivers/mmi_annotate/mmi_annotate.ko
motorola/drivers/mmi_info/mmi_info.ko
motorola/drivers/mmi_relay/mmi_relay.ko
motorola/drivers/sensors/sensors_class.ko
motorola/drivers/input/touchscreen/touchscreen_mmi/touchscreen_mmi.ko
motorola/drivers/input/touchscreen/goodix_berlin_mmi/goodix_brl_mmi.ko
qcom/opensource/wlan/qcacld-3.0/qca_cld3_qca6490.ko
motorola/drivers/power/bm_adsp_ulog/bm_adsp_ulog.ko
motorola/drivers/power/mmi_charger/mmi_charger.ko
motorola/drivers/power/qti_glink_charger/qti_glink_charger.ko
motorola/drivers/power/qpnp_adaptive_charge/qpnp_adaptive_charge.ko
motorola/drivers/misc/utag/utags.ko
motorola/drivers/regulator/wl2868c/wl2868c.ko
qcom/opensource/audio-kernel/asoc/codecs/aw882xx/aw882xx_dlkm.ko
qcom/opensource/audio-kernel/asoc/codecs/fs19xx/fs19xx_dlkm.ko
qcom/opensource/audio-kernel/asoc/codecs/hdmi_dlkm.ko
qcom/opensource/audio-kernel/asoc/codecs/lpass-cdc/lpass_cdc_dlkm.ko
qcom/opensource/audio-kernel/asoc/codecs/lpass-cdc/lpass_cdc_rx_macro_dlkm.ko
qcom/opensource/audio-kernel/asoc/codecs/lpass-cdc/lpass_cdc_tx_macro_dlkm.ko
qcom/opensource/audio-kernel/asoc/codecs/lpass-cdc/lpass_cdc_va_macro_dlkm.ko
qcom/opensource/audio-kernel/asoc/codecs/lpass-cdc/lpass_cdc_wsa2_macro_dlkm.ko
qcom/opensource/audio-kernel/asoc/codecs/lpass-cdc/lpass_cdc_wsa_macro_dlkm.ko
qcom/opensource/audio-kernel/asoc/codecs/mbhc_dlkm.ko
qcom/opensource/audio-kernel/asoc/codecs/stub_dlkm.ko
qcom/opensource/audio-kernel/asoc/codecs/swr_dmic_dlkm.ko
qcom/opensource/audio-kernel/asoc/codecs/swr_haptics_dlkm.ko
qcom/opensource/audio-kernel/asoc/codecs/wcd937x/wcd937x_dlkm.ko
qcom/opensource/audio-kernel/asoc/codecs/wcd937x/wcd937x_slave_dlkm.ko
qcom/opensource/audio-kernel/asoc/codecs/wcd938x/wcd938x_dlkm.ko
qcom/opensource/audio-kernel/asoc/codecs/wcd938x/wcd938x_slave_dlkm.ko
qcom/opensource/audio-kernel/asoc/codecs/wcd9xxx_dlkm.ko
qcom/opensource/audio-kernel/asoc/codecs/wcd_core_dlkm.ko
qcom/opensource/audio-kernel/asoc/codecs/wsa881x_dlkm.ko
qcom/opensource/audio-kernel/asoc/codecs/wsa883x/wsa883x_dlkm.ko
qcom/opensource/audio-kernel/asoc/machine_dlkm.ko
qcom/opensource/audio-kernel/dsp/adsp_loader_dlkm.ko
qcom/opensource/audio-kernel/dsp/audio_prm_dlkm.ko
qcom/opensource/audio-kernel/dsp/audpkt_ion_dlkm.ko
qcom/opensource/audio-kernel/dsp/q6_dlkm.ko
qcom/opensource/audio-kernel/dsp/q6_notifier_dlkm.ko
qcom/opensource/audio-kernel/dsp/q6_pdr_dlkm.ko
qcom/opensource/audio-kernel/dsp/spf_core_dlkm.ko
qcom/opensource/audio-kernel/ipc/audio_pkt_dlkm.ko
qcom/opensource/audio-kernel/ipc/gpr_dlkm.ko
qcom/opensource/audio-kernel/soc/pinctrl_lpi_dlkm.ko
qcom/opensource/audio-kernel/soc/snd_event_dlkm.ko
qcom/opensource/audio-kernel/soc/swr_ctrl_dlkm.ko
qcom/opensource/audio-kernel/soc/swr_dlkm.ko
qcom/opensource/camera-kernel/camera.ko
qcom/opensource/eva-kernel/msm/msm-eva.ko
""".split()


def check(root, expected):
    if not expected or len(expected) != len(set(expected)):
        raise ValueError('empty or duplicate inventory')
    for name in expected:
        path = PurePosixPath(name)
        if path.is_absolute() or '..' in path.parts or str(path) != name or path.suffix != '.ko':
            raise ValueError(f'invalid module path: {name}')
    if len({Path(name).name for name in expected}) != len(expected):
        raise ValueError('module basename collision')
    actual = {str(path.relative_to(root)) for path in root.rglob('*.ko')}
    missing, extra = set(expected) - actual, actual - set(expected)
    if missing or extra:
        raise ValueError(f'missing={sorted(missing)} unexpected={sorted(extra)}')
    for name in expected:
        path = root / name
        if any(parent.is_symlink() for parent in (path, *path.parents)):
            raise ValueError(f'symlink module path: {name}')
        if not path.is_file() or path.stat().st_size == 0:
            raise ValueError(f'empty or non-file module: {name}')
    return sorted(expected)


def inventory(work):
    internal = check(work / 'out', (work / 'out/modules.order').read_text().splitlines())
    external = check(work / 'modules-dev-functional', EXTERNAL)
    names = [Path(name).name for name in internal + external]
    if len(names) != len(set(names)):
        raise ValueError('in-tree/external basename collision')
    return internal, external


if __name__ == '__main__':
    try:
        if len(sys.argv) != 2:
            raise ValueError('usage: check-module-inventory.py KERNEL_WORKDIR')
        internal, external = inventory(Path(sys.argv[1]))
        print(f'inventory OK: {len(internal)} in-tree + {len(external)} external')
    except (ValueError, OSError) as error:
        sys.exit(f'module-inventory: {error}')
