---
name: svg2icon
description: Convert an SVG logo into a complete application icon set and sync branding entry points for Tauri apps. Use this skill whenever the user mentions svg to icon, app icon replacement, tauri icon generation, favicon update, or asks to keep sidebar/logo assets consistent with the app icon.
user-invocable: true
---

This skill creates a repeatable SVG -> icon workflow for the AgentHub/Tauri project.

## When To Use

Use this skill if the user asks to:
- replace app icon from an SVG
- regenerate `src-tauri/icons/*`
- sync web favicon with the same source icon
- make sidebar/brand logo match application icon assets

## Inputs

- Source SVG path (default: `public/agenthub-icon.svg`)
- Optional visual constraints (white background, rounded corners, safe padding)

## Workflow

1. Validate the source SVG exists and is square-friendly for icon export.
2. If requested, edit SVG base shape first (background color, radius, safe padding).
3. Generate icon assets:
   - `npm run tauri -- icon <svg-path>`
4. Ensure web favicon points to the same source icon in `index.html`:
   - `<link rel="icon" type="image/svg+xml" href="/agenthub-icon.svg" />`
5. Ensure sidebar/header branding uses `/agenthub-icon.svg` (not a hard-coded fallback glyph).
6. Verify outputs exist in `src-tauri/icons` (including `icon.icns`, `icon.ico`, `128x128.png`, `32x32.png`).
7. Report changed files and remind to restart dev app to refresh icon cache.

## Command Template

```bash
rtk npm run tauri -- icon public/agenthub-icon.svg
```

## Expected Output

- Updated icon set under `src-tauri/icons/`
- `public/agenthub-icon.svg` as single source of truth
- Favicon and in-app branding synchronized to the same icon asset

## Bundled Script

Use `scripts/generate_tauri_icons.sh` for one-command execution:

```bash
rtk bash .agents/skills/svg2icon/scripts/generate_tauri_icons.sh public/agenthub-icon.svg
```
