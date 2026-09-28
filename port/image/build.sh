#!/usr/bin/env bash
# Compose the known H29 boot set and cumulative userspace fixes. Never flash.
set -euo pipefail
[[ ( $# == 2 || ( $# == 3 && $3 == current ) ) && ( $2 == stock || $2 == replacement ) ]] || {
    echo 'usage: port/image/build.sh NEW_OUTPUT_DIRECTORY stock|replacement [current]' >&2; exit 1;
}
edition=${3:-preview}
archive=eqs-preview-20260910.zip
[[ $edition != current ]] || archive=eqs-current-20260928.zip
repo=$(git -C "$(dirname -- "$0")" rev-parse --show-toplevel)
out=$(realpath -m -- "$1")
[[ ! -e $out && ! -L $out ]] || { echo 'output must not exist' >&2; exit 1; }
image='quay.io/droidian/rootfs-builder@sha256:749133320ea6d913989005ac8519630059dac465dd91d7be95066255b0ba434e'
docker image inspect "$image" >/dev/null
test -r /proc/sys/fs/binfmt_misc/qemu-aarch64
python3 "$repo/port/image/stage-inputs.py" "$out/inputs"
if [[ $edition == current ]]; then
    python3 "$repo/port/image/stage-inputs.py" "$out/packages" current-packages
fi
mkdir "$out/build"
packages_mount=()
if [[ $edition == current ]]; then
    packages_mount=(--mount "type=bind,src=$out/packages,dst=/packages,readonly")
fi
docker run --rm --pull never --network none --privileged \
    --mount "type=bind,src=$repo/port,dst=/source/port,readonly" \
    --mount "type=bind,src=$out/inputs,dst=/inputs,readonly" \
    --mount "type=bind,src=$out/build,dst=/work" \
    --mount type=bind,src=/dev,dst=/host-dev \
    "${packages_mount[@]}" \
    "$image" bash /source/port/image/build-in-container.sh "$2" "$edition" 2>&1 | tee "$out/build.log"
printf 'Image and integrity: %s/build/%s and SHA256SUMS\n' "$out" "$archive"
