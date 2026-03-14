# CrxHub — 浏览器扩展管理器

从 GitHub Releases 下载和版本管理浏览器扩展。使用 Rust 构建，保证速度与可靠性。

## 特性

- 📦 **一键安装** — 下载并解压最新版本的浏览器扩展
- 🤖 **便于自动化** — 使用 `-y/--yes` 选项可自动勾选匹配的首个资产文件
- 🔄 **固定的加载路径** — 维持一个固定的 `current` 目录，方便在浏览器中手动加载
- ♻️ **更新自动替换** — 后续的安装和更新会自动在原地替换本地文件
- 🔍 **批量检查与更新** — 对所有已追踪的扩展运行 `outdate` 或 `update` 命令
- 🗂️ **版本归档** — 下载的版本会被保存在 `~/.crxhub-cli` 目录下
- 🧾 **极简命令** — 支持 `install`, `update`, `outdate`, `uninstall`, `list` 等命令
- ⚡ **执行迅速** — 原生 Rust 二进制文件

## 前置条件

- **Rust**（如需源码编译）或直接下载预编译的二进制文件
- 已完成身份验证的 **GitHub CLI** (`gh`)
```bash
# 安装 GitHub CLI
brew install gh    # macOS
# 或者访问: https://cli.github.com/

# 登录
gh auth login
```

## 安装说明

### 选项 1: 从源码构建

```bash
# 克隆仓库
git clone https://github.com/yourusername/crxhub.git
cd crxhub

# 构建 Release 版本
cargo build --release

# 将二进制文件复制到仓库预期的位置
cp target/release/crx scripts/crx
```

### 选项 2: 添加到环境变量 PATH

```bash
# 复制二进制文件到 PATH
sudo cp target/release/crx /usr/local/bin/

# 或者创建软链接
ln -s $(pwd)/scripts/crx ~/.local/bin/crx
```

### 选项 3: 配置 Shell 别名 (Alias)

```bash
# 添加到 ~/.bashrc, ~/.zshrc 或 ~/.bash_profile
alias crx='/path/to/crxhub/scripts/crx'

# 然后重新加载配置
source ~/.zshrc
```

## 快速入门

### 安装扩展

```bash
crx owner/repo
crx https://github.com/owner/repo
crx install owner/repo
```

如果某个 Release 有多个适用于浏览器的资产文件，CrxHub 会尝试自动为你选择最佳的 Chrome/Edge 版本。如果需要，你依然可以手动覆盖它的选择规则：

```bash
crx install owner/repo "*chrome*.zip"
crx install owner/repo my-extension.crx
crx install -y owner/repo "*chrome*.zip"
```

在 CI、脚本或任何非交互式 Shell 环境中使用 `-y/--yes`，CrxHub 会自动选取匹配的首个资产文件，而不再弹出提示让你选择。

安装完毕后，CrxHub 会输出一个固定路径的目录，例如：

```text
~/.crxhub-cli/extensions/owner/repo/current
```

只需在浏览器的扩展管理页面加载一次该目录即可。以后不管是重新安装还是更新，CrxHub 都会在同一个目录下自动替换文件。

### 更新扩展

```bash
crx update owner/repo
crx update owner/repo 1.5.6
crx update owner/repo latest

# 更新所有已被追踪的扩展
crx update
```

如果固定的 `current` 文件夹丢失，但缓存的该版本仍然存在，`update` 命令也会就地修复浏览器的加载路径。

### 检查过期扩展

```bash
crx outdate
crx outdate owner/repo
```

`outdate` 命令只读不写。它将比对已安装的版本和 GitHub Releases 上的版本，报告哪些仓库需要更新。

## 所有命令列表

| 命令 | 用法 | 描述 |
|---------|-------|-------------|
| `install` | `crx install owner/repo [资产名]` | 下载最新的 release 并刷新 `current` 目录 |
| `update` | `crx update [owner/repo] [latest\|tag]` | 更新某个仓库、切换到指定版本，或者更新所有已安装的仓库 |
| `outdate` | `crx outdate [owner/repo]` | 检查单个或所有已安装的扩展是否需要更新 |
| `uninstall` | `crx uninstall owner/repo` | 移除本地文件以及在注册表中的记录 |
| `list` | `crx list` | 列出所有已安装的扩展及其固定的加载路径 |
| `help` | `crx help [命令]` | 显示帮助信息 |

全局选项:

```bash
crx -y ...
crx --yes ...
```

该选项会自动选中首个匹配的资产文件，跳过交互式的选择提示。

## 它的工作原理

- **文件存储**: `~/.crxhub-cli/extensions/{owner}/{repo}/{tag}/`
- **固定的加载路径**: `~/.crxhub-cli/extensions/{owner}/{repo}/current`
- **注册表**: `~/.crxhub-cli/registry.json`
- **浏览器工作流**: 用户只需在浏览器中手动加载一次 `current` 目录，之后 CrxHub 会就地更新该目录

## 从源码构建

```bash
# 如果尚未安装 Rust
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# 克隆并构建
git clone https://github.com/yourusername/crxhub.git
cd crxhub
cargo build --release

# 二进制文件路径: target/release/crx
# 仓库本地 CLI 生成路径: scripts/crx
```

## 注意事项

- `crx owner/repo` 是 `crx install owner/repo` 的简写方式
- 在预期需要填写仓库名（owner/repo）的任何位置，都可以直接使用 GitHub 的链接（URL）
- 同时支持 `.crx` 和 `.zip` 格式的 Release 压缩资产
- 推荐在自动化流程或无头 Shell (headless shells) 中使用 `-y/--yes` 选项
- 不加具体仓库直接运行 `crx update`，会更新所有的已安装扩展
- 执行 `crx update owner/repo 1.5.6` 会切换到指定的 Release（前提是该 tag 存在）
- 执行 `crx update owner/repo latest` 将强制显式地刷新至最新的 Release
- `crx outdate` 命令仅用于版本检查，它不会修改任何本地文件
- `crx list` 将打印出你应该在浏览器中固定加载的目录路径
- 未来无论安装还是更新，发生变动的文件都在 `current` 目录内，浏览器端的加载只需要操作一次
- 若 `current` 丢失但相关版本的缓存仍在，执行 `update` 可重新修复上述的稳定加载路径

## 许可证 (License)

MIT

## 贡献代码

1. Fork 本仓库
2. 创建属于你的 Feature 分支 (`git checkout -b feature/amazing`)
3. 提交你的改动 (`git commit -am '添加一个很棒的功能'`)
4. 推送至分支 (`git push origin feature/amazing`)
5. 发起一个 Pull Request 
