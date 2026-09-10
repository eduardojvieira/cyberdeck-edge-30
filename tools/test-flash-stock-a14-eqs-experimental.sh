#!/usr/bin/env bash
set -Eeuo pipefail
root=$(cd "$(dirname "$0")/.." && pwd)
script="$root/tools/flash-stock-a14-eqs-experimental.sh"
tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
fw="$tmp/fw"; mkdir -p "$fw" "$tmp/bin"
cat >"$fw/flashfile.xml" <<'XML'
<flashing><header><phone_model model="eqs_g"/><software_version version="eqs_g-user 14 U1SQS34.52-21-1-16 x"/><cid_value value="0x0032"/></header><steps>
XML
files=(vbmeta.img vbmeta_system.img boot.img vendor_boot.img dtbo.img recovery.img)
for n in {0..15}; do files+=("super.img_sparsechunk.$n"); done
parts=(vbmeta vbmeta_system boot vendor_boot dtbo recovery)
for n in {0..15}; do parts+=(super); done
for i in "${!files[@]}"; do : >"$fw/${files[i]}"; md5=$(md5sum "$fw/${files[i]}"|awk '{print $1}'); printf '<step MD5="%s" filename="%s" operation="flash" partition="%s"/>\n' "$md5" "${files[i]}" "${parts[i]}" >>"$fw/flashfile.xml"; done
printf '</steps></flashing>\n' >>"$fw/flashfile.xml"
cat >"$fw/package.info.txt" <<'INFO'
Build Id: U1SQS34.52-21-1-16
Build Fingerprint: motorola/eqs_g/eqs:14/U1SQS34.52-21-1-16/x:user/release-keys
INFO
cat >"$tmp/bin/fake-fastboot" <<'SH'
#!/usr/bin/env bash
echo "$*" >>"$FASTBOOT_LOG"
if [[ $1 == devices ]]; then for ((i=0;i<${FAKE_COUNT:-1};i++)); do echo "serial$i fastboot"; done; exit 0; fi
if [[ $1 == getvar ]]; then
 case $2 in product) echo "product: ${FAKE_PRODUCT:-eqs}";; current-slot) echo "current-slot: ${FAKE_SLOT:-a}";; slot-count) echo "slot-count: ${FAKE_SLOTS:-2}";; securestate) [[ ${FAKE_SECURESTATE+x} ]] && echo "securestate: $FAKE_SECURESTATE";; unlocked) echo "unlocked: ${FAKE_UNLOCKED:-yes}";; ro.carrier) [[ ${FAKE_RO_CARRIER+x} ]] && echo "ro.carrier: $FAKE_RO_CARRIER";; carrier) [[ ${FAKE_CARRIER+x} ]] && echo "carrier: $FAKE_CARRIER";; esac; exit 0
fi
[[ ${FAIL_ON:-} == "$1 $2" ]] && exit 42
exit 0
SH
chmod +x "$tmp/bin/fake-fastboot"
export FASTBOOT_LOG="$tmp/log" FASTBOOT="$tmp/bin/fake-fastboot"
: >"$FASTBOOT_LOG"; "$script" "$fw" >/dev/null; [[ ! -s $FASTBOOT_LOG ]]
for bad in 'FAKE_PRODUCT=wrong' 'FAKE_SLOT=b' 'FAKE_UNLOCKED=no' 'FAKE_COUNT=2' 'FAKE_RO_CARRIER=RETEU' 'FAKE_SECURESTATE=flashing_locked'; do
  : >"$FASTBOOT_LOG"; env $bad FASTBOOT="$FASTBOOT" FASTBOOT_LOG="$FASTBOOT_LOG" "$script" "$fw" --preflight >/dev/null 2>&1 && exit 1
done
: >"$FASTBOOT_LOG"; env FAKE_RO_CARRIER=RETAR FASTBOOT="$FASTBOOT" FASTBOOT_LOG="$FASTBOOT_LOG" "$script" "$fw" --preflight >/dev/null
: >"$FASTBOOT_LOG"; env FAKE_SECURESTATE=flashing_unlocked FAKE_UNLOCKED=no FASTBOOT="$FASTBOOT" FASTBOOT_LOG="$FASTBOOT_LOG" "$script" "$fw" --preflight >/dev/null
: >"$FASTBOOT_LOG"
FASTBOOT="$FASTBOOT" FASTBOOT_LOG="$FASTBOOT_LOG" "$script" "$fw" --execute >/dev/null 2>&1 && exit 1
[[ ! -s $FASTBOOT_LOG ]]
printf 'ok: dry-run avoids fastboot; preflight rejects unsafe state; execute is rejected before fastboot\n'
