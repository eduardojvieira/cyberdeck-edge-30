#!/bin/sh
# eqs H29: bootconfig matches the HAL's public address in this order, not reversed.
# Optional paths permit host-only validation; bluebinder_post invokes without args.
set -eu
fail() { echo "eqs-bt-address: $*" >&2; exit 1; }
[ "$#" -eq 0 ] || [ "$#" -eq 2 ] || fail 'expected no arguments or BOOTCONFIG OUTPUT'
input=${1:-/proc/bootconfig}
output=${2:-/var/lib/bluetooth/board-address}
address=$(LC_ALL=C awk -F= '
    $1 ~ /^[ \t]*androidboot[.]btmacaddr[ \t]*$/ {
        count++; if (NF != 2) invalid=1
        value=$2; gsub(/^[ \t]+|[ \t]+$/, "", value)
        if (value ~ /^".*"$/) value=substr(value, 2, length(value)-2)
    }
    END { if (count != 1 || invalid) exit 1; print toupper(value) }
' "$input") || fail 'missing or ambiguous bootconfig address'
printf '%s\n' "$address" | grep -Eq '^([0-9A-F]{2}:){5}[0-9A-F]{2}$' || fail 'invalid address format'
case "$address" in 00:00:00:00:00:00|FF:FF:FF:FF:FF:FF) fail 'invalid address value' ;; esac
[ ! -L "$output" ] || fail 'refusing symlink output'
if [ -e "$output" ]; then
    [ "$(cat "$output")" = "$address" ] || fail 'existing address differs; preserve it for diagnosis'
    chmod 644 "$output"
    exit 0
fi
directory=$(dirname -- "$output")
mkdir -p -- "$directory"
temporary=$(mktemp "$directory/.board-address.XXXXXX")
trap 'rm -f -- "$temporary"' EXIT
trap 'exit 1' HUP INT TERM
printf '%s\n' "$address" > "$temporary"
chmod 644 "$temporary"
mv -- "$temporary" "$output"
