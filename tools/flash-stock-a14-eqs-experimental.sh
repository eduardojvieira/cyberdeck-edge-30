#!/usr/bin/env bash
# Read-only recovery preparation for exactly XT2241-2 EQS RETAR Android 14.
# It deliberately does not implement Motorola's full signed flashfile.xml.
set -Eeuo pipefail

readonly BUILD='U1SQS34.52-21-1-16'
readonly CID='0x0032'
FASTBOOT="${FASTBOOT:-fastboot}"
MODE=plan FW=

usage() {
  cat <<EOF
Usage: $0 FIRMWARE_DIR [--preflight]

Default mode validates the exact RETAR Android 14 package and prints a plan. It never runs fastboot.
--preflight only reads fastboot state; it never reboots or writes.
--execute is deliberately disabled: the former reduced AP-only sequence bootlooped.
EOF
}
die() { printf 'ERROR: %s\n' "$*" >&2; exit 1; }
warn() { printf 'WARNING: %s\n' "$*" >&2; }

[[ $# -ge 1 ]] || { usage >&2; exit 2; }
FW=$1; shift
while [[ $# -gt 0 ]]; do
  case $1 in
    --preflight) MODE=preflight ;;
    --execute) die '--execute is disabled; use the complete signed flashfile.xml procedure manually' ;;
    --backup-confirmed) die '--backup-confirmed is only meaningful for the disabled --execute path' ;;
    --confirm) die '--confirm is only meaningful for the disabled --execute path' ;;
    -h|--help) usage; exit 0 ;;
    *) die "unknown option: $1" ;;
  esac
  shift
done

readonly -a FILES=(vbmeta.img vbmeta_system.img boot.img vendor_boot.img dtbo.img recovery.img
  super.img_sparsechunk.{0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15})
readonly -a PARTITIONS=(vbmeta vbmeta_system boot vendor_boot dtbo recovery
  super super super super super super super super super super super super super super super super)

step_attr() { # filename attribute; print matching XML step
  grep -F "filename=\"$1\"" "$FW/flashfile.xml" || true
}

validate_firmware() {
  [[ -d $FW && -r $FW/flashfile.xml ]] || die "firmware directory or flashfile.xml missing: $FW"
  grep -Fq '<phone_model model="eqs_g"' "$FW/flashfile.xml" || die 'package is not eqs_g'
  grep -Fq "software_version version=\"eqs_g-user 14 $BUILD " "$FW/flashfile.xml" || die "package is not Android 14 $BUILD"
  grep -Fq "cid_value value=\"$CID\"" "$FW/flashfile.xml" || die "package CID is not $CID (RETAR)"
  local info
  info=$(find "$FW" -maxdepth 1 -type f -name '*.info.txt' -print -quit)
  [[ -n $info ]] || die 'package info file missing'
  grep -Fq "Build Id: $BUILD" "$info" || die 'info file build does not match'
  grep -Fq 'Build Fingerprint: motorola/eqs_g/eqs:14/' "$info" || die 'info file is not eqs_g Android 14'

  local i file partition line expected actual xml_partition
  for i in "${!FILES[@]}"; do
    file=${FILES[i]}; partition=${PARTITIONS[i]}
    [[ -f $FW/$file ]] || die "required file missing: $file"
    line=$(step_attr "$file")
    [[ -n $line ]] || die "no XML MD5 entry for $file"
    xml_partition=$(sed -n 's/.*partition="\([^"]*\)".*/\1/p' <<<"$line")
    [[ $xml_partition == "$partition" ]] || die "unexpected XML partition for $file: $xml_partition"
    expected=$(sed -n 's/.*MD5="\([0-9a-fA-F]*\)".*/\1/p' <<<"$line")
    [[ $expected =~ ^[0-9a-fA-F]{32}$ ]] || die "invalid XML MD5 for $file"
    actual=$(md5sum "$FW/$file" | awk '{print $1}')
    [[ ${actual,,} == ${expected,,} ]] || die "MD5 mismatch: $file"
  done
}

fb() { "$FASTBOOT" "$@"; }
getvar() { fb getvar "$1" 2>&1; }
require_var() {
  local var=$1 regex=$2 got
  got=$(getvar "$var") || die "fastboot getvar $var failed"
  grep -Eqi "$regex" <<<"$got" || die "fastboot $var rejected: $got"
}
get_concrete_var() {
  local variable=$1 raw value
  raw=$(getvar "$variable" || true)
  value=$(grep -Eio "${variable}:[[:space:]]*[[:alnum:]_-]+" <<<"$raw" | head -n1 | sed -E "s/.*:[[:space:]]*//" || true)
  case ${value,,} in ''|unknown|not|none|failed) printf '' ;; *) printf '%s' "$value" ;; esac
}

preflight() {
  command -v "$FASTBOOT" >/dev/null 2>&1 || die "fastboot not found: $FASTBOOT"
  local devices count
  devices=$(fb devices) || die 'fastboot devices failed'
  count=$(awk 'NF { n++ } END { print n+0 }' <<<"$devices")
  [[ $count == 1 ]] || die "expected exactly one fastboot device, got $count"
  require_var product 'product: *(eqs|eqs_g)([[:space:]]|$)'
  require_var current-slot 'current-slot: *a([[:space:]]|$)'
  require_var slot-count 'slot-count: *2([[:space:]]|$)'
  # Motorola's current bootloader reports securestate, while older ones may only expose unlocked.
  local securestate unlocked
  securestate=$(get_concrete_var securestate)
  if [[ -n $securestate ]]; then
    [[ ${securestate,,} == flashing_unlocked ]] || die "fastboot securestate is not flashing_unlocked: $securestate"
  else
    unlocked=$(get_concrete_var unlocked)
    [[ ${unlocked,,} == yes || ${unlocked,,} == true ]] || die 'fastboot does not report an unlocked bootloader'
  fi
  # Motorola commonly exposes ro.carrier; older fastboot implementations use carrier.
  # An unavailable/unknown variable is not a value. Any concrete reported value must be RETAR.
  local variable value
  for variable in ro.carrier carrier; do
    value=$(get_concrete_var "$variable")
    [[ -n $value ]] || continue
    [[ ${value,,} == retar ]] || die "fastboot $variable is not RETAR: $value"
  done
}

print_risks() {
  cat >&2 <<'EOF'

RECOVERY LIMIT:
- This helper is read-only. It validates one signed package and checks Fastboot state.
- The former reduced AP-only write sequence bootlooped and was removed.
- No Android 15 RETAR recovery package is stored locally.
- The HIL-proven stock recovery was a complete manual execution of signed flashfile.xml steps.
EOF
}

plan() {
  printf 'Validated exact package: eqs_g XT2241-2 RETAR Android 14 %s (CID %s)\n' "$BUILD" "$CID"
  printf 'Plan only: no fastboot command was run.\n'
  printf 'No write path is implemented. The reduced AP-only sequence was removed after it bootlooped.\n'
  printf 'Use only the complete signed flashfile.xml procedure after separate review and authorization.\n'
  print_risks
}

validate_firmware
case $MODE in
  plan) plan ;;
  preflight) preflight; printf 'Preflight passed; no writes or reboot were performed.\n'; print_risks ;;
esac
