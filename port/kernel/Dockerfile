FROM quay.io/droidian/build-essential@sha256:692a6c1d280f08a6c021057fbb42c70c6ef9e0ea15a3d74d7310fa42d4887b6a

RUN dpkg --add-architecture arm64 && apt-get update && apt-get install --yes --no-install-recommends flex bison bc libssl-dev libelf-dev cpio binutils-aarch64-linux-gnu clang-android-12.0-r416183b android-platform-prebuilts-python-linux-x86-2.7.5 python3 pkg-config kmod lz4 avbtool linux-initramfs-halium-generic:arm64=2025.04.11.0+git20250411210410.e515727.next.production

RUN printf '%s\n' '#!/bin/sh' 'exec /usr/lib/llvm-android-12.0-r416183b/bin/ld.lld --threads=1 "$@"' > /usr/local/bin/ld.lld-single-thread && chmod 0755 /usr/local/bin/ld.lld-single-thread
