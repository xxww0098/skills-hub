# cua-computer-use

Cua Driver CLI skill: inspect and operate local desktop windows in the
background (no cursor steal). Not Anthropic's Computer Use API.

This file is a pointer. Policy lives in one place:

| Who | Read |
|-----|------|
| Agents | [SKILL.md](./SKILL.md) then [references/adversary.md](./references/adversary.md) |
| Toolkit routing | [references/frameworks.md](./references/frameworks.md) (`"$CUA" frameworks`) |
| Schemas | the **installed** `cua-driver` (`guide` / `describe`), never a copied table |

## Resolve

```bash
CUA="$(pwd)/scripts/cua-use"   # or SKILL_DIR after install
chmod +x "$CUA"
"$CUA" ensure && "$CUA" guide
```

```powershell
$CUA = "$(Get-Location)\scripts\cua-use.ps1"
& $CUA ensure
& $CUA guide
```

`ensure` = official install if `cua-driver` is missing → start daemon →
wait on **`status`** → probe `list_windows '{"on_screen_only": true}'`.
Liveness is `status`. Never block on `list_apps` (macOS hung ~90s with
CuaDriver.app already serving).

| Platform | Extra once |
|----------|------------|
| macOS | Daemon **must** come from **CuaDriver.app**. Then `"$CUA" grant` (`permissions grant`, not `grant`) and `"$CUA" permissions status --json`. |
| Linux | `DISPLAY` or Wayland + a `unix:path` session bus (`"$CUA" session-bus`). `list_apps.active` is always false. |
| Windows | Interactive user session (not Session 0). |

Override the binary with `CUA_DRIVER_BIN`. Optional MCP: `"$CUA" connect claude`.
Optional isolated VM: `"$CUA" sandbox-install` (Python 3.12/3.13, not 3.14).

## Lab

Cua Lab fixtures: [fixtures/cua-lab](./fixtures/cua-lab/). Title **Cua Lab**.
Linux replay: `tests/linux-smoke.sh` — needs a desktop session and
`cua-driver`. It does **not** run on `ubuntu-latest` without `DISPLAY`.

Official docs: [Install Cua Driver](https://cua.ai/docs/how-to-guides/driver/install).
