#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

TARGETS=(
    "aarch64-apple-darwin:crx-darwin-arm64"
    "x86_64-apple-darwin:crx-darwin-x86_64"
    "x86_64-unknown-linux-musl:crx-linux-x86_64"
    "x86_64-pc-windows-gnu:crx-windows-x86_64.exe"
)

mkdir -p scripts

echo "Building release binaries for all platforms..."
echo ""

for entry in "${TARGETS[@]}"; do
    target="${entry%%:*}"
    output="${entry##*:}"

    echo "==> $target ($output)"

    # Use cargo-zigbuild for cross-compilation (Linux musl + macOS cross-arch)
    cargo zigbuild --release --target "$target"

    # Windows builds produce .exe
    if [[ "$target" == *windows* ]]; then
        src="target/$target/release/crx.exe"
    else
        src="target/$target/release/crx"
    fi
    dst="scripts/$output"

    cp "$src" "$dst"
    chmod +x "$dst"
    size=$(du -sh "$dst" | cut -f1)
    echo "    ✓ scripts/$output ($size)"
    echo ""
done

echo "Build complete! Binaries in scripts/:"
ls -lh scripts/crx-*
