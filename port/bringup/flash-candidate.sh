#!/usr/bin/env bash
# Explicit slot-A boot iteration only. Never installs or repairs userdata.
set -euo pipefail
fail() { printf 'eqs-candidate: %s\n' "$*" >&2; exit 1; }
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
case "${1:-}" in
    --check) [[ $# == 1 ]] || fail 'usage: --check' ;;
    --flash-a|--rescue-a) [[ $# == 2 && -n "$2" && "$2" != -* ]] || fail 'an explicit Fastboot serial is required' ;;
    *) fail 'usage: --check | --flash-a SERIAL | --rescue-a SERIAL' ;;
esac
[[ -s SHA256SUMS ]] || fail 'missing bundle checksums'
sha256sum --strict -c SHA256SUMS || fail 'bundle verification failed; no device action performed'
for file in candidate/{boot,vendor_boot,dtbo,vbmeta}.img rescue/{boot,vendor_boot,dtbo,vbmeta,recovery}.img; do
    [[ -s "$file" ]] || fail "missing required artifact: $file"
    [[ $(awk -v file="$file" '$2 == file {n++} END {print n+0}' SHA256SUMS) == 1 ]] || fail "missing or duplicate checksum: $file"
done
[[ $1 != --check ]] || { echo 'Bundle integrity OK; no device was accessed.'; exit 0; }
serial=$2
fb() { timeout 120 fastboot -s "$serial" "$@"; }
read_var() {
    local value
    value=$(fb getvar "$1" 2>&1) || fail "cannot read $1: $value"
    printf '%s\n' "$value" | sed -n "s/^\((bootloader) \)\?$1: //p" | tr -d '\r'
}
[[ $(read_var product) == eqs ]] || fail 'product must be eqs'
slot=$(read_var current-slot)
[[ $slot == a || ( $1 == --rescue-a && $slot == b ) ]] || fail 'candidate requires active A; use explicit A rescue after slot fallback'
[[ $(read_var securestate) == flashing_unlocked ]] || fail 'bootloader must be flashing_unlocked'
[[ $(read_var is-userspace) == no ]] || fail 'AP Fastboot required, not fastbootd'
unbootable=$(read_var slot-unbootable:a)
retries=$(read_var slot-retry-count:a)
[[ $unbootable =~ ^(yes|no)$ && $retries =~ ^[0-7]$ ]] || fail 'invalid A boot metadata'
printf 'Before write: active=%s A-unbootable=%s A-retries=%s\n' "$slot" "$unbootable" "$retries"
# Motorola splits this getvar across numbered lines; match the exact known base.
loader=$(fb getvar version-bootloader 2>&1) || fail 'cannot read bootloader version'
loader=$(printf '%s\n' "$loader" | sed -nE 's/^(\(bootloader\) )?version-bootloader\[[01]\]: //p' | tr -d '\r\n')
[[ $loader == MBM-3.0-eqs-c66ed235df0-250323-U1SQS34.52-21-1-16-5b71b0 ]] || fail 'this bundle requires the recorded Android 14 -16 bootloader'
source=candidate
[[ $1 != --rescue-a ]] || source=rescue
# Explicit list: no slot B, partition-table, super, erase, format or userdata writes.
for partition in vbmeta dtbo vendor_boot boot; do
    fb flash "${partition}_a" "$source/$partition.img" || fail "flash failed at $partition; remain in Fastboot and use the rescue procedure"
done
if [[ $source == rescue ]]; then
    fb flash recovery_a rescue/recovery.img || fail 'recovery flash failed'
fi
# Flashing A alone does not reset retries. Select only after the whole set succeeds.
fb set_active a || fail 'could not select A; remain in Fastboot'
[[ $(read_var current-slot) == a ]] || fail 'A selection did not persist'
[[ $(read_var slot-unbootable:a) == no ]] || fail 'A remains unbootable'
[[ $(read_var slot-retry-count:a) =~ ^[1-7]$ ]] || fail 'A retries were not reset'
printf 'Wrote %s boot set to A and reset its boot attempts. No reboot, B partition or userdata write performed.\n' "$source"
