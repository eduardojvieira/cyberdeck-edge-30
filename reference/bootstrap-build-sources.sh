#!/usr/bin/env bash
# Bootstrap only the pinned source repositories used by kernel/adaptation builds.
set -euo pipefail

fail() { printf 'bootstrap-build-sources: %s\n' "$*" >&2; exit 1; }

script_dir=$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
repos="$script_dir/repos"
temporary=

cleanup() {
    [[ -z $temporary ]] || rm -rf -- "$temporary"
}
trap cleanup EXIT HUP INT TERM

ensure_repo() {
    local url=$1 destination=$2 commit=$3 actual

    if [[ -e $destination ]]; then
        [[ -e $destination/.git ]] || fail "unexpected existing path: $destination"
        actual=$(git -C "$destination" rev-parse HEAD 2>/dev/null) || fail "cannot read $destination"
        [[ $actual == "$commit" ]] || fail "$destination commit mismatch: expected $commit, found $actual"
        [[ -z $(git -C "$destination" status --porcelain --untracked-files=all) ]] || fail "$destination must be clean"
        return
    fi

    mkdir -p "${destination%/*}"
    temporary="$destination.tmp.$$"
    [[ ! -e $temporary ]] || fail "temporary path already exists: $temporary"
    git init -q "$temporary"
    git -C "$temporary" remote add origin "$url"
    git -C "$temporary" fetch --depth=1 origin "$commit"
    git -C "$temporary" checkout --detach --quiet FETCH_HEAD
    actual=$(git -C "$temporary" rev-parse HEAD)
    [[ $actual == "$commit" ]] || fail "$destination fetched an unexpected commit"
    [[ -z $(git -C "$temporary" status --porcelain --untracked-files=all) ]] || fail "$destination checkout is not clean"
    mv "$temporary" "$destination"
    temporary=
}

ensure_repo https://github.com/eqs-development/android_device_motorola_eqs "$repos/eqs-development/android_device_motorola_eqs" d2c017af5ae8b1aeda0b3ba5072cb99643cbe8ff
ensure_repo https://github.com/eqs-development/android_device_motorola_sm8475-common "$repos/eqs-development/android_device_motorola_sm8475-common" 9ef36ec870058f5fe4bb1b1d0213dbac7325a168
ensure_repo https://github.com/eqs-development/android_kernel_motorola_sm8475 "$repos/eqs-development/android_kernel_motorola_sm8475" bd42a1bb7281f8f4b974cdaf7f6d5260f9f62582
ensure_repo https://github.com/eqs-development/android_kernel_motorola_sm8475-modules "$repos/eqs-development/android_kernel_motorola_sm8475-modules" 9f8d247d457622c08ff547e5498e6fa453e876ed
ensure_repo https://github.com/eqs-development/android_kernel_motorola_sm8475-devicetrees "$repos/eqs-development/android_kernel_motorola_sm8475-devicetrees" f02ca5e3e17fa9f6f8e3167a687f86040d0a0848
ensure_repo https://github.com/LineageOS/android_vendor_lineage "$repos/LineageOS/android_vendor_lineage" 85fbbf9a6601ca7af759aa0aa06d32f7a9800b36
ensure_repo https://github.com/LineageOS/android_external_dtc "$repos/LineageOS/android_external_dtc" fd8c8a25dac5f2cc083348f6a3916424b688a508
ensure_repo https://android.googlesource.com/platform/system/libufdt "$repos/aosp-mirror/platform_system_libufdt" 4cc0d8f7e5d26ed1f7b98aa8f325f51e5bb1dcbd
