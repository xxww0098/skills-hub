#!/usr/bin/env bash
set -euo pipefail

SOURCE_SVG="${1:-public/agenthub-icon.svg}"

run_cmd() {
  if command -v rtk >/dev/null 2>&1; then
    rtk "$@"
  else
    "$@"
  fi
}

if [[ ! -f "$SOURCE_SVG" ]]; then
  echo "Error: SVG not found: $SOURCE_SVG" >&2
  exit 1
fi

if [[ ! -f "package.json" || ! -d "src-tauri" ]]; then
  echo "Error: Run this script from the project root containing package.json and src-tauri/." >&2
  exit 1
fi

echo "[1/3] Generating Tauri icon set from: $SOURCE_SVG"
run_cmd npm run tauri -- icon "$SOURCE_SVG"

echo "[2/3] Syncing favicon in index.html"
if [[ -f "index.html" ]]; then
  if run_cmd rg -q 'href="/agenthub-icon\.svg"' index.html; then
    echo "- favicon already points to /agenthub-icon.svg"
  elif run_cmd rg -q 'rel="icon"' index.html; then
    run_cmd perl -0777 -i -pe 's#<link rel="icon"[^>]*>#<link rel="icon" type="image/svg+xml" href="/agenthub-icon.svg" />#g' index.html
    echo "- favicon link updated"
  else
    run_cmd perl -0777 -i -pe 's#(<meta charset="UTF-8"\s*/?>)#$1\n    <link rel="icon" type="image/svg+xml" href="/agenthub-icon.svg" />#' index.html
    echo "- favicon link inserted"
  fi
else
  echo "- skipped (index.html not found)"
fi

echo "[3/3] Verifying generated icon files"
required=(
  "src-tauri/icons/icon.icns"
  "src-tauri/icons/icon.ico"
  "src-tauri/icons/icon.png"
  "src-tauri/icons/128x128.png"
  "src-tauri/icons/32x32.png"
)

missing=0
for file in "${required[@]}"; do
  if [[ ! -f "$file" ]]; then
    echo "Missing: $file" >&2
    missing=1
  fi
done

if [[ "$missing" -ne 0 ]]; then
  echo "Icon generation completed with missing outputs." >&2
  exit 1
fi

echo "Done. Icon workflow completed successfully."
