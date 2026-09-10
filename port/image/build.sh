#!/usr/bin/env bash
# Compose the known H29 boot set and cumulative userspace fixes. Never flash.
set -euo pipefail
[[ $# == 2 && ( $2 == stock || $2 == replacement ) ]] || {
    echo 'usage: port/image/build.sh NEW_OUTPUT_DIRECTORY stock|replacement' >&2; exit 1;
}
repo=$(git -C "$(dirname -- "$0")" rev-parse --show-toplevel)
out=$(realpath -m -- "$1")
[[ ! -e $out && ! -L $out ]] || { echo 'output must not exist' >&2; exit 1; }
image='quay.io/droidian/rootfs-builder@sha256:749133320ea6d913989005ac8519630059dac465dd91d7be95066255b0ba434e'
docker image inspect "$image" >/dev/null
test -r /proc/sys/fs/binfmt_misc/qemu-aarch64
python3 "$repo/port/image/stage-inputs.py" "$out/inputs"
mkdir "$out/build"
docker run --rm --pull never --network none --privileged \
    --mount "type=bind,src=$repo/port,dst=/source/port,readonly" \
    --mount "type=bind,src=$out/inputs,dst=/inputs,readonly" \
    --mount "type=bind,src=$out/build,dst=/work" \
    --mount type=bind,src=/dev,dst=/host-dev \
    "$image" bash /source/port/image/build-in-container.sh "$2" 2>&1 | tee "$out/build.log"
printf 'Image and integrity: %s/build/eqs-preview-20260910.zip and SHA256SUMS\n' "$out"
