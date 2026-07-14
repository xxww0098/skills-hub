# 文档信息模型

## 目录

1. 单一职责
2. 分层与变化速率
3. 状态与证据
4. 索引和链接
5. 初始化最小集
6. 外部设计依据

## 1. 单一职责

| 文档 | 只回答什么 | 不承载什么 |
|---|---|---|
| `CLAUDE.md` | 只用 `@AGENTS.md` 委托加载根规则 | 任何独立规则、摘要或第二份事实源 |
| `AGENTS.md` | agent 必须立即知道的定位、红线、命令、索引 | 长篇架构解释、逐文件说明、历史流水账 |
| `README.md` | 人类第一次如何理解、安装和运行 | agent 专属规则、完整目录边界 |
| `docs/boundaries.md` | 能力归谁、文件放哪、依赖朝哪、接缝在哪 | 产品路线、实现教程 |
| `docs/architecture.md` | 运行蓝图、数据所有权、不变量、关键技术选择 | 完整项目树、逐功能操作步骤 |
| `docs/errors.md` | 已发生误判的现象、根因、修复、预防 | 一般 TODO、决策辩论、代码注释替代品 |
| `docs/decisions.md` | 已拍板且长期有效的选择、背景、后果 | 每次提交的变更日志 |
| `plan*.md` | 未完成事项、顺序、验收和状态 | 已实现事实的唯一来源 |
| `docs/features/<feature>/` | 跟该功能代码一起变的边界、范式、契约和 UX | 跨仓稳定宪章 |
| `docs/others/` | 未归位细则、runbook、历史稿的待决策暂存；`README.md` 决策表记录每篇的去留建议（保留/合并/删除） | 宪章与功能活文档的长期居所 |
| 就近 `README.md` | 这一个目录放什么、公开入口是什么 | 整个子系统的通用规则 |
| 冻结 spec/RFC | 当时为何拍板、当时范围 | 当前实现说明 |

同一事实只保留一个权威落点。索引可保留一句摘要，但必须链接主文档。

工程卫生约定（如**单个代码文件 ≤ 1000 行**）属 `AGENTS.md` 的最高红线，不新开文档承载；`init` 模板默认写入，`refactor`/`refresh` 精简 `AGENTS.md` 时必须保留，`docs_audit.py` 以确定性检查 `code-file-too-long` 执法（生成物、vendored、快照及点目录豁免）。

## 2. 分层与变化速率

- `docs/` 根只允许宪章（`boundaries.md`、`errors.md`、`decisions.md`，多交付面仓库加 `architecture.md`）+ `features/` + `others/`；`docs_audit.py` 以 `docs-root-flat` 执法。
- 把随功能实现变化的文档放 `docs/features/<feature>/`；单篇功能文档也直接进文件夹，不平铺根（README 索引在 ≥2 篇时才必须）。
- 把仅解释目录落点的短说明放代码旁。
- 把可生成的 API、schema、CLI 参考放源码旁并自动生成。
- 把冻结设计、切流记录、过期快照和一切未归位文档放 `docs/others/`（历史稿标 historical），禁止和 active 宪章混排；描述对象已被物理删除的设计稿可直接删，git 历史即归档。

## 3. 状态与证据

每篇治理文档在标题后标记 `状态：active` 或 `状态：historical`。计划状态使用明确的 `planned`、`in progress`、`done`，不要用模糊的“基本完成”。

标记为 `historical` 的文档冻结只读：`docs_audit.py` 不对其报告占位符、断链或空壳，只要求状态标记本身存在；不要为了消除审计发现而改写历史稿。

可信度顺序：

1. 实际运行或测试证据；
2. composition root、注册表、公开导出、schema 和 migration；
3. CI、manifest、部署配置；
4. 当前代码注释；
5. active 文档；
6. 历史稿、计划、提交信息。

产品意图不能只靠代码推断。无法验证时写“待确认”并列证据缺口。

## 4. 索引和链接

- 根 `AGENTS.md` 只列必须入口和文档分组，不逐篇复制目录内容。
- 功能目录存在多篇文档时用 `README.md` 给出阅读顺序和“文档 → 代码”映射。
- 新建、移动、删除文档时，用 `rg` 查找路径、标题和旧术语的所有引用。
- 使用相对链接；不要让同一路径在大小写不同的文件系统上表现不同。
- 避免孤儿文档：每篇 active 文档至少从一个稳定索引可达。
- 用户口中的「孤儿/散乱」通常指 `docs/` 根平铺的非宪章文档，而非零入链；重构以根收敛为目标，不要用入链统计反驳用户的观感。

## 5. 初始化最小集与出生规则

默认创建（五者即 `docs_audit.py` 的必备集，缺任一报 P1）：

```text
CLAUDE.md              # 内容只有 @AGENTS.md
AGENTS.md
docs/
├── boundaries.md
├── errors.md
└── decisions.md
```

`errors.md`（做错了什么）与 `decisions.md`（为什么这么选）是一对，缺一不可：只有 errors 没有 decisions，错误册会退化成「又改回去了」的反复横跳。

`architecture.md` 按需出生：仅当仓库呈现多交付面证据（workspaces、多语言根 manifest，或 apps/packages/services/crates 出现两类以上顶层目录）时由 `init` 一并创建；单交付面仓库把少量运行关系留在 `boundaries.md`，等「一张项目树讲不清关系」时再分裂出来，后补出生时用 `refresh` 校准索引。

其余文档按出生规则生长，不预先建空文件：

| 文档 | 出生触发 |
|---|---|
| `README.md` | 出现第二个人类读者（协作者、用户），需要「怎么装、怎么跑」 |
| `plan*.md` | 出现需要排期与验收的多步工作；勾选一项的前提是可重跑的验证命令或真实运行证据 |
| `docs/features/<feature>/` | 第一篇功能技术文档即可建文件夹（不平铺根）；README 索引在 ≥2 篇或需要阅读顺序时必须（audit 以 missing-feature-index 执法） |
| `docs/others/` 与其决策表 | 第一篇未归位/历史文档出现时；每篇配一行去留建议，拍板后同步索引 |
| `conventions.md` / `feature-protocol.md` | 功能形状、DoD、质量门槛需要跨功能统一时（住 `docs/others/` 或升宪章由用户拍板） |
| runbook / 部署文档 | 真实部署面存在后（住 `docs/others/` 或对应 `features/`，不平铺根） |

初始化后必须根据代码删减或补全，不保留空壳。

## 6. 外部设计依据

- [OpenAI Skills skill-creator](https://github.com/openai/skills/blob/main/skills/.system/skill-creator/SKILL.md)：只保留 `name`、`description` frontmatter，采用渐进披露，并以脚本承载确定性流程。
- [AGENTS.md 开放格式](https://agents.md/)：把 AGENTS.md 作为 agent 的专用上手文件；大型 monorepo 可用更近的嵌套 AGENTS.md 提供增量规则。
- [Anthropic Skills](https://github.com/anthropics/skills)：skill 保持自包含，以 `SKILL.md`、`scripts/`、`references/`、`assets/` 组合可复用工作流。
