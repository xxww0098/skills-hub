# cua-computer-use

让 Claude Code / Cursor / Codex 等 Agent **后台操控本机桌面应用**（点窗口、打字、截图），不抢鼠标焦点。

Computer Use 2.0 不是一个独立软件包，而是 [Cua](https://cua.ai) 的能力。
**不是** Anthropic 官方 Claude「Computer Use」API。

Agent 说明看 [SKILL.md](./SKILL.md)。本 README 给人读。

---

## CuaDriver 是不是 App？

**macOS 上是。Windows / Linux 上不是那种双击打开的 GUI App。**

| 平台 | CuaDriver 是什么 | 你日常怎么用 |
|------|------------------|--------------|
| **macOS** | 真正的 App：`/Applications/CuaDriver.app` | 系统设置里授权给这个 App；daemon 必须从它启动，辅助功能 / 屏幕录制才会记在正确身份上 |
| **Windows / Linux** | 后台 CLI + daemon，没有给人点的窗口 | 命令行跑 `cua-driver`，或用本仓库的包装脚本 |

macOS 装完会同时有两件东西，不要混：

```
CuaDriver.app          ← App（权限 + 后台服务）
~/.local/bin/cua-driver ← CLI（人和 Agent 敲的命令，指向上面那个 App）
```

你不会像用计算器那样打开 CuaDriver 去点界面。**App 负责权限和守护进程，真正点窗口走 CLI。**

---

## 这套东西里有几层

```
你 / Agent
    │
    ├─ 本仓库 skill（cua-computer-use）
    │     SKILL.md          ← 教 Agent 怎么选命令
    │     scripts/cua-use   ← 包装 CLI（macOS / Linux）
    │     scripts/cua-use.ps1
    │              │
    │              ▼
    ├─ cua-driver CLI      ← 官方命令：call / doctor / mcp / skills
    │              │
    │              ▼
    └─ CuaDriver daemon
          macOS = CuaDriver.app 里的服务
          Win/Linux = `cua-driver serve` 后台进程
                │
                ▼
          本机正在跑的 App（计算器、浏览器、IDE…）
```

| 名字 | 是 App 吗 | 职责 |
|------|-----------|------|
| **CuaDriver.app** | ✅ 仅 macOS | 系统身份、TCC 权限、守护进程 |
| **`cua-driver`** | ❌ CLI | `call list_apps`、`call click`、MCP stdio |
| **本 skill `cua-use`** | ❌ 包装脚本 | 一条命令完成安装 / 拉起 daemon / 调用工具 |
| **MCP** | ❌ 协议 | 可选。客户端更吃 MCP 时再接 |
| **Sandbox（`pip install cua`）** | ❌ 隔离虚拟机 | 不想碰本机文件/账号时走这条 |

三种驱动方式走同一套工具，本 skill **默认 CLI**：

| 模式 | 怎么调 | 何时用 |
|------|--------|--------|
| **CLI（默认）** | `scripts/cua-use call …` | 任何能跑 shell 的 Agent |
| **官方 skill pack** | `cua-use connect claude` | 给 Agent 补「怎么选工具、怎么验证」 |
| **MCP** | `connect` 打印注册命令，再贴进客户端 | Claude / Cursor / Codex 要 MCP 工具时 |

---

## 先选一条路

| 你想做什么 | 装什么 |
|------------|--------|
| Agent **直接操作当前这台电脑** | Cua Driver（默认）。macOS 上就是那个 App + CLI |
| Agent 只在隔离虚拟机里跑，不碰本机 | `pip install cua` + Sandbox |

---

## 安装

一般 **不需要管理员权限**。macOS 要求 14+（Sonoma）。

本 skill 包装器（推荐）：

```bash
# macOS / Linux
CUA="$(pwd)/scripts/cua-use"   # 或 skill 安装后的 SKILL_DIR
chmod +x "$CUA"
"$CUA" ensure
```

```powershell
# Windows
$CUA = "$(Get-Location)\scripts\cua-use.ps1"
& $CUA ensure
```

`ensure` = 没有 `cua-driver` 就跑官方安装 → 拉起 daemon → `call list_apps`。能列出正在运行的应用 = 驱动已经能看到桌面。

官方一键安装（`ensure` 内部会调）：

```bash
# macOS / Linux
/bin/bash -c "$(curl -fsSL https://cua.ai/driver/install.sh)"
```

```powershell
# Windows
irm https://cua.ai/driver/install.ps1 | iex
```

找不到命令：新开一个终端，或 `source ~/.zshrc`（安装脚本通常会把 `~/.local/bin` 加进 PATH）。

### macOS 额外步骤（必做一次）

必须先用 **App** 启动守护进程，再授权。点「打开系统设置」**不会授权**，列表里要把 CuaDriver **手动打开**。

```bash
"$CUA" grant
# 系统设置 → 隐私与安全性
#   辅助功能（Accessibility）        → CuaDriver 打开
#   屏幕录制（Screen Recording）     → CuaDriver 打开
"$CUA" status
# Accessibility: granted
# Screen Recording: granted
```

缺一个就再跑一遍 `grant`。授权后若提示退出重开，接受；daemon 没回来就 `"$CUA" serve`。

---

## 快速开始

```bash
"$CUA" ensure
"$CUA" call list_apps
"$CUA" call launch_app '{"name":"Calculator"}'
```

对 Agent 说：

> 用 cua-driver 打开计算器，算 6×7，告诉我结果。

应在后台点窗口，**不抢走你的鼠标**。Linux 用系统计算器；纯 Wayland 不如 X11 / XWayland 稳。

接到 Claude Code / Cursor / Codex（可选 MCP）：

```bash
"$CUA" connect claude    # 或 cursor / codex
# 按打印出来的命令注册 MCP，然后重启客户端
```

---

## 本 skill 的 CLI

`scripts/cua-use`（Windows 用 `cua-use.ps1`）包一层官方 `cua-driver`。先 `ensure`，再 `call`。

```bash
"$CUA" ensure                         # 安装 + daemon + list_apps
"$CUA" install                        # 只跑官方安装
"$CUA" bin                            # cua-driver 路径
"$CUA" doctor                         # 环境报告
"$CUA" status                         # macOS 权限
"$CUA" grant                          # macOS 授权提示
"$CUA" serve                          # 只拉起 daemon
"$CUA" call <tool> [json]             # 驱动桌面
"$CUA" list-tools
"$CUA" describe <tool>
"$CUA" connect [claude|cursor|codex]  # 官方 skill pack + 打印 MCP 配置
"$CUA" update
"$CUA" telemetry-disable
"$CUA" sandbox-install                # pip install cua（Python 3.12/3.13）
"$CUA" sandbox-smoke
"$CUA" -- <raw cua-driver args>       # 透传
```

未知子命令当成 tool 名：`"$CUA" list_apps` ≡ `"$CUA" call list_apps`。

覆盖二进制：`export CUA_DRIVER_BIN=/path/to/cua-driver`。

Agent 驱动循环（inspect → act → verify）：

```bash
"$CUA" call list_windows '{"on_screen_only": true}'
"$CUA" call get_window_state '{"pid":PID,"window_id":WID}'
"$CUA" call click '{"pid":PID,"window_id":WID,"element_index":N}'
"$CUA" call type_text '{"text":"hello","pid":PID}'
"$CUA" call press_key '{"key":"return","pid":PID}'
```

规则：先列窗口，再点；优先 `element_index`，不要盲点坐标；默认不 `bring_to_front`；密码 / 支付 / 公司内网窗口先问用户。

---

## 隔离沙箱（可选）

不想让 Agent 碰本机文件/账号。需要 **Python 3.12 或 3.13（不要 3.14）** + Docker。

```bash
"$CUA" sandbox-install
"$CUA" sandbox-smoke
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

云端：到 [cua.ai](https://cua.ai) 注册 API Key。

```bash
curl -LsSf https://cua.ai/cli/install.sh | sh
cua auth login
cua sb create --os linux
```

---

## 使用前注意

1. Driver 能看屏幕、点窗口、打字。macOS 授权给 CuaDriver.app 之后，等于把本机 GUI 交给 Agent。先用不重要的应用试。
2. 含登录态、密码、支付、公司内网的窗口，不要默认交给它。
3. Linux：纯 Wayland 有限制，X11 / XWayland 更稳。
4. Windows：必须在用户交互会话里跑，当服务（Session 0）看不到窗口。
5. 这和 Anthropic Claude Computer Use **不是同一套安装包**。

---

## 排错

| 症状 | 处理 |
|------|------|
| `cua-driver: command not found` | `"$CUA" install`；新开终端；`source ~/.zshrc` |
| macOS `status` 为 unknown / denied | `"$CUA" grant`，系统设置里手动打开 CuaDriver |
| `list_apps` 为空或失败 | `"$CUA" serve`，再 `"$CUA" doctor` |
| Agent 连不上 MCP | 用 `connect` 打印的绝对路径；重启客户端 |
| Linux 点不到窗口 | 改用 X11 / XWayland；检查 AT-SPI |
| Windows 窗口列表是空的 | 不要当服务跑 |
| Python 3.14 装 cua 失败 | 换 3.12 / 3.13 |
| 本地 sandbox 起不来 | Docker 是否在跑；需要 `local=True` |

官方文档：

- [Install Cua Driver](https://cua.ai/docs/how-to-guides/driver/install)
- [Connect your agent](https://cua.ai/docs/how-to-guides/driver/connect-your-agent)
- [Drive your first app](https://cua.ai/docs/tutorials/drive-your-first-app)
- [CLI reference](https://cua.ai/docs/reference/cua-driver/cli-reference)
- [MCP tools](https://cua.ai/docs/reference/cua-driver/mcp-tools)
- [Sandbox SDK](https://cua.ai/docs/reference/sandbox-sdk)
