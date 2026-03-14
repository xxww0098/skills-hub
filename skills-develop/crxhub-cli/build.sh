#!/usr/bin/env bash

# Exit immediately if a command exits with a non-zero status
set -e

# Change into the directory of the script
cd "$(dirname "$0")"

echo "Building release binary..."
cargo build --release

echo "Removing old binary..."
rm -f scripts/crx

echo "Copying new binary to scripts/..."
cp target/release/crx scripts/
chmod +x scripts/crx

echo "Build complete! Binary is available in scripts/crx"
