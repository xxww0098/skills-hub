---
name: cua-computer-use
description: >-
  Drive native desktop apps via Cua Computer Use 2.0. Default is Cua Driver
  through this skill's CLI (`scripts/cua-use`): background click/type/screenshot
  on the host without stealing focus. Also covers MCP wiring and isolated
  `pip install cua` sandboxes. Use when the user mentions Cua, cua-driver,
  Computer Use 2.0, computer-use, 本机操控, 后台点窗口, Claude Code/Cursor/Codex
  操作桌面, or wants an agent to operate Calculator and other GUI apps.
argument-hint: <command> [args...]
---

# Cua Computer Use 2.0 — skill + CLI

Computer Use 2.0 不是独立软件包，而是 [Cua](https://cua.ai) 的能力。
**不是** Anthropic 官方 Claude Computer Use API。

本 skill 默认走 **CLI 模式**：包装官方 `cua-driver`（本机后台操控）。可选再走 MCP 或隔离 Sandbox。

> **Always combine setup + command in ONE shell call.** 先 `ensure`，再 `call`。

## How to Run

Replace `<SKILL_DIR>` with this SKILL.md's directory.

**macOS / Linux：**

```bash
CUA="<SKILL_DIR>/scripts/cua-use" && chmod +x "$CUA" && "$CUA" ensure
```

**Windows（PowerShell）：**

```powershell
$CUA = "<SKILL_DIR>\scripts\cua-use.ps1"
& $CUA ensure
```

`ensure` 会：没有 `cua-driver` 就跑官方安装脚本 → 拉起 daemon → `call list_apps`。列出正在跑的应用即成功。

macOS 第一次还要授权（交互，不能跳过）：

```bash
"$CUA" grant
# 系统设置里把 CuaDriver 的 辅助功能 / 屏幕录制 打开，再:
"$CUA" status
"$CUA" ensure
```

## Quick Workflows

用最少命令。不要先 exploratory 一圈，除非用户要。

| User intent | Command |
|---|---|
| 装好并能看到桌面 | `"$CUA" ensure` |
| 列出应用 | `"$CUA" call list_apps` |
| 打开计算器算 6×7 | 见下方 [Drive loop](#drive-loop) |
| 接到 Claude Code / Cursor / Codex | `"$CUA" connect claude`（或 `cursor` / `codex`） |
| 只要 CLI、不要 MCP | `ensure` 后直接 `call`（本 skill 默认） |
| 隔离环境、不碰本机 | `"$CUA" sandbox-install` 然后 `sandbox-smoke` |
| 更新 Driver | `"$CUA" update` |
| 关遥测 | `"$CUA" telemetry-disable` |

未知子命令会当成 tool 名：`"$CUA" list_apps` ≡ `"$CUA" call list_apps`。

---

## 先选一条路

| 目标 | 走法 |
|------|------|
| Claude Code / Cursor / Codex **操作当前这台电脑** | **CLI（默认）**；可选再 MCP |
| 隔离 Linux/Windows/macOS，不碰本机文件/账号 | `"$CUA" sandbox-install` |

未指定 → CLI + Cua Driver。

---

## CLI 命令

```bash
"$CUA" ensure                         # install + daemon + list_apps
"$CUA" install                        # 官方安装（一般无需管理员）
"$CUA" bin                            # cua-driver 路径
"$CUA" doctor                         # 环境报告
"$CUA" status                         # macOS TCC
"$CUA" grant                          # macOS 授权提示（必做一次）
"$CUA" serve                          # 只拉起 daemon
"$CUA" call <tool> [json]             # 驱动桌面
"$CUA" list-tools
"$CUA" describe <tool>
"$CUA" connect [claude|cursor|codex]  # skills install + 打印 MCP 配置
"$CUA" skills install
"$CUA" mcp-config --client claude
"$CUA" update
"$CUA" telemetry-disable
"$CUA" sandbox-install
"$CUA" sandbox-smoke
"$CUA" -- <raw cua-driver args>
```

Windows 把 `"$CUA"` 换成 `& $CUA`。覆盖二进制：`export CUA_DRIVER_BIN=/path/to/cua-driver`。

官方安装器（`ensure` / `install` 会调用）：

```bash
# macOS / Linux
/bin/bash -c "$(curl -fsSL https://cua.ai/driver/install.sh)"

# Windows PowerShell
irm https://cua.ai/driver/install.ps1 | iex
```

macOS 14+（Sonoma）。找不到命令就新开终端，或 `source ~/.zshrc`（`~/.local/bin`）。

---

## Drive loop

工具名 `snake_case`。CLI 是真入口：`cua-driver call <tool> [json]`（本包装器同名）。`call` 需要 **daemon 已在跑** → 所以先 `ensure`。

```text
inspect → act → verify
1. list_apps / list_windows
2. launch_app（未在跑时）
3. get_window_state        AX 树 + 截图
4. click / type_text / press_key / scroll / hotkey
5. 再 get_window_state     读到结果再停
```

```bash
"$CUA" ensure
"$CUA" call list_apps
"$CUA" call list_windows '{"on_screen_only": true}'
"$CUA" call launch_app '{"name":"Calculator"}'
# macOS:
"$CUA" call launch_app '{"bundle_id":"com.apple.calculator"}'
"$CUA" call get_window_state '{"pid":PID,"window_id":WID}'
"$CUA" call click '{"pid":PID,"window_id":WID,"element_index":N}'
"$CUA" call type_text '{"text":"hello","pid":PID}'
"$CUA" call press_key '{"key":"return","pid":PID}'
"$CUA" call hotkey '{"keys":["cmd","c"],"pid":PID}'
"$CUA" call screenshot '{}' --screenshot-out-file /tmp/cua.png
```

冒烟提示（用户侧自然语言即可，Agent 用上面的 loop 落地）：

> 用 cua-driver 打开计算器，算 6×7，告诉我结果。

应在后台点窗口，**不抢鼠标焦点**。Linux 用系统计算器。X11 / XWayland 比纯 Wayland 稳。

规则：

1. 先 `ensure`，再任何 `call`。
2. 先 `list_apps` / `list_windows`，不要盲点坐标。优先 `element_index`。
3. **保持后台**：不要 `bring_to_front`，除非用户要前台。
4. 每步后重新 `get_window_state`。
5. 登录态 / 密码 / 支付 / 公司内网窗口：**先问用户**。
6. 不要 `kill_app`，除非明确要求。
7. 不要点用户正在用的前台编辑器。

---

## CLI vs Skill vs MCP

三种都能驱动同一套 `cua-driver` 工具。本仓库 skill **默认 CLI**。

| 模式 | 机制 | 何时 |
|------|------|------|
| **CLI（默认）** | `"$CUA" call …` | Claude Code / Cursor / Codex / 任何能跑 shell 的 Agent |
| **Cua 官方 skill pack** | `"$CUA" skills install` | 给 Agent 补「怎么选工具、怎么验证」 |
| **MCP** | `"$CUA" connect <client>` 后重启客户端 | 客户端更吃 MCP 工具而不是 shell |

`connect` 会 `skills install` 并 **打印** 注册命令，不擅自改用户配置。需要 MCP 时再执行打印出来的命令，例如：

```bash
claude mcp add --transport stdio cua-driver -- cua-driver mcp
# 或
cua-driver mcp-config --client claude
```

Cursor：把 JSON 写入 `~/.cursor/mcp.json`。改完重启客户端。

这仍是 Cua Driver over CLI/MCP，不是 Anthropic 原生 Computer Use。

---

## macOS 权限

必须用 **CuaDriver.app** 拉起 daemon，TCC 才记在正确身份上：

```bash
"$CUA" grant
"$CUA" status
# Accessibility: granted
# Screen Recording: granted
```

点「打开系统设置」**不会授权**，列表里要手动打开。缺一个就再 `grant` 一次。daemon 没回来：`"$CUA" serve`。未启动 daemon 时 `status` 可能是 `unknown`。

权限模式在 daemon 启动时锁定，改模式必须重启：

| 模式 | 命令 |
|------|------|
| `standard`（默认） | `"$CUA" serve` |
| `bounded` | `"$CUA" -- serve bounded --capability-manifest /abs/path.yaml --approve-capability-manifest` |
| `unrestricted` | `"$CUA" -- serve --dangerously-bypass-approvals`（仅可丢弃机器） |

macOS bounded 仍应用 `open -n -g -a CuaDriver --args …`，manifest 必须绝对路径。

---

## Path B — 隔离 Sandbox

Python **3.12 或 3.13，不要 3.14**。本地需要 Docker。

```bash
"$CUA" sandbox-install
"$CUA" sandbox-smoke
```

等价：

```bash
pip install cua   # 包 cua-sandbox，import cua
```

```python
import asyncio
from cua import Sandbox, Image

async def main():
    async with Sandbox.ephemeral(Image.linux(), local=True) as sb:
        print(await sb.shell.run("echo hello"))
        await sb.screenshot()

asyncio.run(main())
```

云端：https://cua.ai 注册 API Key，或：

```bash
curl -LsSf https://cua.ai/cli/install.sh | sh   # Windows: irm https://cua.ai/cli/install.ps1 | iex
cua auth login
cua sb create --os linux
```

---

## 使用前注意

1. Driver 能看屏幕、点窗口、打字。权限给完 = 把本机 GUI 交给 Agent。先用不重要的应用试。
2. 含登录态、密码、支付、公司内网的窗口，不要默认交给它。
3. Linux：纯 Wayland 有限制，X11 / XWayland 更稳。
4. Windows：必须在用户交互会话里跑，Session 0（服务）看不到窗口。
5. 与 Anthropic Claude Computer Use API **不是同一套安装包**。

## 排错

| 症状 | 处理 |
|------|------|
| `command not found` | `"$CUA" install`；新开终端；`source ~/.zshrc` |
| macOS status unknown/denied | `"$CUA" grant`，系统设置里手动打开 |
| `list_apps` 失败 | `"$CUA" serve` 然后 `"$CUA" doctor` |
| MCP 连不上 | `connect` 打印的绝对路径；重启客户端 |
| Linux 点不到 | X11 / XWayland；查 AT-SPI |
| Windows 空窗口列表 | 不要当服务跑 |
| Python 3.14 | 换 3.12 / 3.13 |
| sandbox 起不来 | Docker 在跑；`local=True` |

文档：

- https://cua.ai/docs/how-to-guides/driver/install
- https://cua.ai/docs/how-to-guides/driver/connect-your-agent
- https://cua.ai/docs/tutorials/drive-your-first-app
- https://cua.ai/docs/reference/cua-driver/cli-reference
- https://cua.ai/docs/reference/cua-driver/mcp-tools
- https://cua.ai/docs/reference/sandbox-sdk
