---
name: svg2icon
description: >
  Turn an SVG logo into a full Tauri icon set and sync favicon plus in-app
  branding to the same source. Use when the user mentions svg to icon, app
  icon, tauri icon, src-tauri/icons, favicon, sidebar or logo branding,
  icon.icns, icon.ico, or keeping web and desktop icons consistent.
---

# svg2icon

One SVG → `src-tauri/icons/*` + favicon/branding. Default source is
`public/agenthub-icon.svg` (AgentHub). Run from the app repo root
(`package.json` + `src-tauri/`).

## Workflow

1. Confirm the SVG exists and is square-friendly. Edit fill, radius, or
   padding first if the user asked for a visual change — icons inherit the SVG.
2. Generate the set via the bundled script (prefers `rtk` when present,
   otherwise plain `npm`):

   ```bash
   bash "<SKILL_DIR>/scripts/generate_tauri_icons.sh" public/agenthub-icon.svg
   ```

   Equivalent: `npm run tauri -- icon <svg-path>`.
3. Favicon in `index.html` must be the same SVG:
   `<link rel="icon" type="image/svg+xml" href="/agenthub-icon.svg" />`
   The script updates an existing icon link or inserts one.
4. Sidebar/header must use `/agenthub-icon.svg`, not a fallback glyph.
5. Confirm `src-tauri/icons/{icon.icns,icon.ico,icon.png,128x128.png,32x32.png}`.
6. List changed files. Restart the desktop app — OS icon caches are sticky.

Pass a different SVG path as the first argument when the user names one.
