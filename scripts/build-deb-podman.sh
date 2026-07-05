#!/usr/bin/env bash
# Build the sparrow-wifi .deb locally inside a podman container, mirroring the
# CI "package" workflow (fpm + `make deb`). No host toolchain needed beyond
# podman — ruby/fpm/make live in the builder image (packaging/Containerfile),
# which is built once and cached.
#
# Usage:
#   scripts/build-deb-podman.sh              # version from sparrowversion.py
#   scripts/build-deb-podman.sh 2.2.0        # override the package version
#
# Env:
#   SPARROW_BUILD_REBUILD=1   force a rebuild of the cached builder image
#   SPARROW_PODMAN_NETWORK=x  podman --network for the *image build* only
#                             (default: host). The package build uses no network.
#
# Output: dist/sparrow-wifi_<version>-1_all.deb (owned by the invoking user;
# rootless podman maps container root back to you).
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
IMAGE="localhost/sparrow-wifi-deb-builder:latest"
NETWORK="${SPARROW_PODMAN_NETWORK:-host}"
VERSION="${1:-}"

command -v podman >/dev/null 2>&1 || { echo "error: podman not found on PATH" >&2; exit 1; }

# Build (or rebuild) the fpm-equipped builder image on demand.
if [ -n "${SPARROW_BUILD_REBUILD:-}" ] || ! podman image exists "$IMAGE"; then
    echo ">> building builder image $IMAGE (network: $NETWORK)"
    podman build --network "$NETWORK" \
        -t "$IMAGE" \
        -f "$REPO_ROOT/packaging/Containerfile" \
        "$REPO_ROOT"
fi

# Pass VERSION through to the Makefile only when overridden; otherwise the
# Makefile reads it from sparrowversion.py (the single source of truth).
MAKE_ARGS=(deb)
[ -n "$VERSION" ] && MAKE_ARGS+=("VERSION=$VERSION")

echo ">> building .deb: make ${MAKE_ARGS[*]}"
# --network none: the package build needs no network; keep it isolated.
# The repo is mounted rw so build/ and dist/ land back in the working tree.
podman run --rm --network none \
    -v "$REPO_ROOT:/src" \
    -w /src \
    "$IMAGE" \
    make "${MAKE_ARGS[@]}"

echo ">> artifacts in dist/:"
ls -l "$REPO_ROOT/dist/"
