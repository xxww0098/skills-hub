# Real Browser

用真实本地 Chrome（含完整登录状态）执行浏览器自动化。
**默认无头运行**，不关闭用户现有浏览器，通过 `agent-browser --cdp 9851` 控制。

✅ 跨平台：macOS、Linux、WSL、Windows Git Bash

---

## 前置依赖

1. **安装 `agent-browser` skill**（提供完整浏览器操作命令）：
   ```bash
   npx skills add https://github.com/vercel-labs/agent-browser
   ```

2. **安装 `agent-browser` CLI**（如尚未全局安装）：
   ```bash
   npm install -g agent-browser
   ```

## 与 `agent-browser` skill 的关系

| | `real-browser` skill（本 skill） | `agent-browser` skill |
|---|---|---|
| **职责** | 启动带登录态的 Chrome，暴露 CDP 端口 | 提供全部浏览器命令（50+ 命令） |
| **包含** | 启动脚本 + CDP 连接规则 | click、fill、type、scroll、eval 等 |
| **单独使用** | ❌ 只能启动，不能操作 | ✅ 可独立使用（自带 Chromium） |

> 💡 **AI 加载本 skill 后，会被自动引导去加载 `agent-browser` skill 获取完整命令集。**
> 如果发现 AI 只会 `open`、`screenshot` 却不会 `click`、`fill` 等操作，说明它没有成功加载 `agent-browser` skill。

---

## 快速开始

```bash
# 无头模式（默认，推荐，速度最快，高安全网站登录态最稳）
scripts/real_browser.sh

# 有头模式（可见窗口，方便观察 AI 操作）
scripts/real_browser.sh --headed

# 自定义端口
scripts/real_browser.sh --headed 9888
```

> ⚠️ **默认无头（隐形）模式**：AI 在后台操作浏览器，完全不打断你的工作。
> 想亲眼看 AI 操作？在提示词中明确要求，例如：
> *"帮我查 x.com 热榜，**带上界面让我看着**"*

---

## 使用示例

在 AI 对话中这样说：

```text
# 📝 核心策略：不带 --headed 能稳定通过最高级别风控登录（Google / Claude 等）

# 【查询与研究】
use skill(real-browser) 帮我打开 x.com 看看我首页的头条是什么
use skill(real-browser) 去 github.com 看看我的通知列表里有哪些评论
use skill(real-browser) 去 V2EX 看看今天最有争议的帖子是什么，总结一下观点
use skill(real-browser) 搜索下 "bitcoin odds on polymarket"，帮我截个图

# 【自动化与提取】
use skill(real-browser) 帮我打开我的 Google 邮箱，找出最近一封发票邮件，把金额告诉我
use skill(real-browser) 打开掘金 (juejin.cn) 提取前端板块今天点赞最高的 3 篇文章标题
use skill(real-browser) 去 B站 看一下我关注的 UP 主有没有更新 React 视频

# 【交互与工作（推荐后台纯静默模式）】
use skill(real-browser) 打开 claude.ai 帮我开个新对话，输入"帮我写测试代码"，把回答发给我
use skill(real-browser) 在 Notion 里去我的 TodoList 页面添加一条"今晚健身"
use skill(real-browser) 去翻译一下这段文字到 DeepL

# 【有头模式】亲自看着 AI 交互（⚠️ 部分高安全网站会丢失登录态）
use skill(real-browser) 有头模式打开一个小霸王游戏网站，我想看着你怎么玩马里奥
use skill(real-browser) 打开界面帮我填一个在线问卷，我想看着你一道道题选
use skill(real-browser) 请带上界面 (--headed) 打开推特，查看马斯克最新动态
```

---

## 工作原理

```
用户的 Chrome（不受影响）         CDP Chrome（自动化用）
┌──────────────────┐           ┌──────────────────────┐
│ 正常浏览器窗口    │           │ 无头/有头模式          │
│ 默认 profile     │──克隆──→  │ ~/.chrome-cdp-profile │
│ 保持运行         │  (~5MB)   │ CDP :9851             │
└──────────────────┘           └──────────┬───────────┘
                                          │
                               agent-browser --cdp 9851
                                          │
                               ┌──────────┴───────────┐
                               │  agent-browser skill  │
                               │  50+ 命令全覆盖        │
                               │  click/fill/type/...  │
                               └───────────────────────┘
```

- 每次启动**清空旧克隆，重新复制**关键认证文件（Cookies, Login Data, Local Storage 等）
- macOS Keychain 和 DBSC 技术对路径强绑定 → Google/Claude 等高安全网站可能退出登录
- 绝大部分普通网站（X、知乎、GitHub、Reddit 等）保持完美登录态

## 启动策略

| 策略 | 触发条件 | 登录保留 | 耗时 |
|------|----------|----------|------|
| **REUSE** | CDP 已在端口监听 | ✅ 100% | 0s |
| **CLONE** | 其他所有情况 | ✅ ~99% | ~5s |

## 使用约束

| 规则 | 说明 |
|------|------|
| 🔗 `--cdp 9851` | 所有 `agent-browser` 命令**必须**带此参数 |
| 📦 需要 `agent-browser` skill | 完整命令集（click、fill、type 等）来自该 skill |
| 🚫 不混用 `chrome-devtools` | 不能混合控制方式 |
| 📌 端口默认 `9851` | 可通过启动参数更改 |
| ⏳ `open` 后 `wait` | 确保页面加载完成 |
| 🔄 交互前 `snapshot -i` | 获取最新 element refs |
| 👀 无反应时 `tab list` | 检查 CDP target 是否在正确的标签页 |

---

## 故障排除

```bash
# 端口被占用
lsof -iTCP:9851 -sTCP:LISTEN && kill <pid>

# 锁文件残留
rm -f /tmp/.real_browser.lock

# 重启
scripts/real_browser.sh
```
