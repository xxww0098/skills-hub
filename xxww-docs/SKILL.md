---
name: xxww-docs
description: 通过 init、refactor、refresh 三个命令初始化、阶段性重构和重新维护代码仓库的 CLAUDE.md、AGENTS.md、docs/、功能文档、局部 README、决策与错误记录，并强制每个项目同时具备根级 CLAUDE.md 与 AGENTS.md。用户提到 /xxww-docs init、空仓库初始化文档、项目开发一段时间后重构文档体系、/xxww-docs refactor、已有文档重新校准、恢复文档维护、/xxww-docs refresh、CLAUDE.md、AGENTS.md 过时、文档与代码不一致、目录边界、架构说明或文档索引时，必须使用本 skill。
---

# XXWW Docs

把代码和配置视为当前实现证据，把文档视为有明确职责、所有者和变化触发器的契约。先研究，再写文档；不要从旧文档互相抄出“事实”。

## 强制双入口

每个项目根目录必须同时存在两个普通文件：

- `AGENTS.md`：唯一完整的 agent 项目规则入口。
- `CLAUDE.md`：Claude 委托入口，内容只能是 `@AGENTS.md`，允许文件末尾一个换行，不得复制规则或添加其他文本。

`init` 必须创建二者；`refactor` 和 `refresh` 的写入模式必须检查并修复二者，`--check` 模式只报告拟修复。所有规则只维护在 `AGENTS.md`，避免双份事实源。

## 三个命令

只提供三个用户入口：

| 命令 | 使用阶段 | 结果 |
|---|---|---|
| `/xxww-docs init` | 仓库刚建立，尚无 `CLAUDE.md`、`AGENTS.md` 和系统文档，代码也可以为空 | 创建最小文档基线，建立以后如何生长的规则 |
| `/xxww-docs refactor` | 项目已开发一段时间，目录、模块和文档自然生长，需要阶段性重构 | 从当前代码重建信息模型，合并重复事实，重排文档结构并修复索引 |
| `/xxww-docs refresh` | 已有一套文档，但长期未维护、接手后想重新维护，或一次大改后需要重新对齐 | 保留合理结构，重新研究当前代码并校准失真内容 |

支持两个通用参数：

- `--check`：只读检查，输出发现和建议，不修改文件；适用于全部三个命令。`init --check` 只运行初始化预览。
- `--scope <path>`：只处理指定子树，同时检查它与根文档的接缝。

用户未写命令时按以下顺序推断并明确说明：缺少核心文档时用 `init`；需要移动、合并或重新分层时用 `refactor`；结构仍合理但内容需要更新时用 `refresh`。不要暴露 `review`、`maintain` 等第四个命令。

### 唯一路由阈值

只有同时满足以下条件才使用 `refresh`：

- 只原地修正文案、事实、命令、链接、状态或索引；
- 不跨目录移动文档，不合并或拆分文档，不新增文档层级；
- 不改变 `AGENTS.md`、`boundaries.md` 与功能索引之间的主责分配；
- 需要冻结或删除的文档不超过 2 篇，且不影响阅读路径。

命中任一条件即使用 `refactor`：跨目录移动；合并或拆分；新增 `features/`、`historical/`、runbook 等层级；改变文档主责；一次冻结/删除至少 3 篇；需要重写完整项目树或多个索引。两者看似都可用时按此阈值给出唯一推荐命令，不同时推荐两个命令。

### `--check` 固定产出

按以下标题完整输出；没有发现也写“无”：

1. `命令路由`：请求命令、唯一推荐命令、触发或未触发的阈值。
2. `作用域与规则`：目标路径、读取到的全部适用 `AGENTS.md`、用户已有脏路径基线。
3. `双入口`：`CLAUDE.md`/`AGENTS.md` 状态；只读模式仅列拟修复。
4. `证据矩阵`：逐行覆盖项目树、架构数据、命令发布、功能状态、约束事故；写证据路径或明确未覆盖原因。
5. `发现`：严重度、文档位置、代码证据、影响、最小修复。
6. `目标文档树`：`refactor --check` 必填；其他命令仅在结构变化时填写。
7. `逐文件迁移表`：`refactor --check` 必填，列当前路径、动作、目标路径、目标主责、证据；动作只能是保留、合并、移动、冻结、删除、新增。
8. `审计结果`：确定性脚本发现与人工证据发现分开。
9. `零写入证明`：比较前后 `git status --porcelain`；必要时比较关键文件哈希。
10. `结论`：唯一下一命令；不得用“分类均已给出”代替实际表格。

`init --check` 还必须列出将创建、将跳过的文件及预览结果；不得执行 `--apply`。

开始前读取仓库根和目标路径作用域内的全部 `AGENTS.md`，并在产出中列出实际读取路径。若仓库已有文档规则，以更具体且不冲突的规则为准。

## 共同流程

1. 定位仓库根，检查 `git status --short`，把开始时的脏路径作为用户变更基线，保护已有修改。
2. 运行仓库清单：

   ```bash
   python3 .claude/skills/xxww-docs/scripts/repo_inventory.py --root . --format markdown
   ```

3. 用 `rg` 研究真实入口、manifest、workspace、路由、schema、迁移、部署和验证命令。不要把文件名本身当作行为证据。
4. 为每条拟写结论记录证据路径；无法确认时标为待确认，不编造职责、版本、端口或命令。
5. 按 [references/documentation-model.md](references/documentation-model.md) 决定信息唯一落点；按 [references/review-rubric.md](references/review-rubric.md) 复核质量。
6. 先更新索引/项目树契约，再新增、移动或删除文档与目录。同步修复所有入链和出链。
7. 写入任务先在修改前保存审计基线，修改后带 `--baseline` 复跑；脚本会把发现分为 new/resolved/pre-existing，只有 `new` 必须修复，`pre-existing` 单独报告：

   ```bash
   python3 .claude/skills/xxww-docs/scripts/docs_audit.py --root . --format json --exit-zero > /tmp/xxww-docs-audit.before.json
   # 完成修改后
   python3 .claude/skills/xxww-docs/scripts/docs_audit.py --root . --baseline /tmp/xxww-docs-audit.before.json
   ```

8. 检查 diff，确认没有覆盖用户修改、重复事实源、遗留占位符或把计划写成现状。

## `/xxww-docs init`：从零建立最小文档基线

永远先预览，不直接覆盖已有文件；`init --check` 在预览后结束：

```bash
python3 .claude/skills/xxww-docs/scripts/init_docs.py --root .
python3 .claude/skills/xxww-docs/scripts/init_docs.py --root . --apply
```

执行规则：

1. 确认用户确实处于初始化阶段。若核心文档已经存在，停止覆盖并按唯一路由阈值选择 `refresh` 或 `refactor`。
2. 只创建缺失的 `CLAUDE.md`、`AGENTS.md`、`docs/boundaries.md`、`docs/errors.md`、`docs/decisions.md`，不覆盖任何已有文件。`docs/architecture.md` 按需出生：仅当仓库呈现多交付面证据（workspaces、多语言根 manifest，或 apps/packages/services/crates 出现两类以上顶层目录）时创建；单交付面仓库把少量运行关系留在 `boundaries.md`，复杂后再分裂（见 [references/documentation-model.md](references/documentation-model.md) §5）。
3. 确认 `CLAUDE.md` 内容只有 `@AGENTS.md`；任何额外说明都移入 `AGENTS.md`。
4. 有代码时立即用代码证据补全目录职责、依赖方向、接缝、命令和红线。删除不适用段落；不要保留空壳。
5. 仓库尚无代码时只写最小治理约定，把未知实现明确标为 `planned`；首次形成真实目录、manifest 或运行入口后执行 `/xxww-docs refresh`，不得提前虚构架构。
6. 保持 `AGENTS.md` 短小，只放项目定位、最高红线、入口命令和文档索引。细则下沉到 `docs/`。
7. 只有复杂度真实出现时再增加 `feature-protocol.md`、`docs/features/<feature>/`、runbook 或局部 `README.md`。
8. 若仓库是 monorepo 或子树需要不同规则，可在子项目放更近的 `AGENTS.md`；避免复制根规则，只写增量约束。

有真实代码或 manifest 时，以下内容是完成门槛：

- `AGENTS.md` 写明真实项目定位、主要交付面、项目特有红线和已验证命令；不能保留通用项目描述，但模板自带的常驻工程红线（如单个代码文件 ≤1000 行）必须保留。
- `boundaries.md` 写明主要目录的唯一职责、反职责、实际依赖方向和已找到的关键接缝。
- `architecture.md`（仅多交付面仓库创建）写明实际运行拓扑、核心数据所有权、实现不变量和从 manifest 验证的技术栈。
- `errors.md`、`decisions.md` 可以暂无记录，但必须存在并保留可执行格式；二者属 `docs_audit.py` 必备集，缺失报 P1。
- `docs_audit.py` 不得出现 `unresolved-scaffold`；只创建模板而未补全时，`init` 未完成。

控制 init 研究范围，避免为了“完整”无限扫描：只读取根 manifest/workspace、每个交付面的一个组合根、IPC/API/持久化等关键契约、CI 和稳定命令。每个完成门槛已有至少一条代码证据后立即写文档，不继续遍历同类文件，不运行全量业务测试。可启动子代理时，把 `AGENTS.md`、`boundaries.md`、`architecture.md`（未创建时为前两篇）分给只修改各自文件的代理，最后由主代理统一审计；不可启动时按这个顺序逐篇完成。

初始化模板位于 `assets/templates/`。修改模板后必须重新运行脚本测试。

## `/xxww-docs refactor`：阶段性重构文档体系

此命令重构的是文档体系，不自动重构产品代码。使用 `--check` 时只输出目标结构与迁移建议。

1. 读取代码、配置、现有文档和相关 git 历史；在产出中列出实际使用的 git 证据，并建立“当前事实 → 当前文档 → 目标主文档”映射。
2. 按「强制双入口」检查并修复根级 `CLAUDE.md` 与 `AGENTS.md`。
3. 识别入口膨胀、事实重复、目录与文档错位、active/historical 混排、**`docs/` 根平铺的非宪章文档**、孤儿文档和过期索引。用户口中的「孤儿/散乱」优先按根级平铺理解，不用入链统计反驳（见 documentation-model §4）。
4. 先给出目标文档树、每篇文档唯一职责、保留/合并/移动/冻结/删除清单，**经用户确认后**再执行写入（`--check` 产出或对话拍板均可；用户已明确给出目标结构时直接执行）。不得自行发明用户未认可的新层级名；未归位与历史文档收进 `docs/others/` 待用户逐篇决策，配 README 决策表。
5. 先更新 `AGENTS.md` 顶层地图和 `docs/boundaries.md` 完整项目树，再移动或新增目录与文档。
6. 合并事实时选择一个主文档，其他位置只留摘要和链接；不要把旧文档整篇复制进新结构。
7. 移动或删除前使用 `rg` 找全引用；完成后修复索引、相对链接、状态和阅读顺序。批量路径替换必须显式排除 `.claude/`（skill 自身）、`node_modules/` 与 lockfile；生成物（openapi/schema）里的路径要连同其源头同源更新，不单改产物。误改 skill 文件后必须回退并复跑其自测。
8. 保留仍有效但无法从代码推断的产品决策，标注来源；把冻结设计稿改为 historical，不重写历史。
9. 只在用户明确要求时修改产品代码；发现代码边界本身不合理时作为独立建议报告。

## `/xxww-docs refresh`：重新研究并恢复维护

先确定输出模式：`--check` 只给出带证据和最小修复建议的发现；默认模式直接同步文档。两种模式都必须完成证据核验。

先建立证据矩阵，再改文件：

| 检查面 | 主要证据 | 需要对齐的文档 |
|---|---|---|
| 项目树与所有权 | 目录、manifest、workspace、公开入口 | `AGENTS.md`、`boundaries.md` |
| 运行架构与数据 | composition root、IPC/API/schema、migration | `architecture.md`、功能边界文档 |
| 命令与发布 | package scripts、CI、Docker、部署脚本 | `AGENTS.md`、README、runbook |
| 功能状态 | 路由、注册表、真实 adapter、测试和 feature flag | 功能文档、计划、历史稿状态 |
| 约束与事故 | 安全边界、失败模式、git 历史、错误记录 | 红线、`errors.md`、`decisions.md` |

按以下顺序刷新：

1. 按「强制双入口」检查并修复根级 `CLAUDE.md` 与 `AGENTS.md`。
2. 删除或改正与代码直接矛盾的事实。
3. 把同一事实合并到一个主文档，其他位置只留链接和一行摘要。
4. 区分 `active`、`historical`、计划和兼容债；冻结稿不得冒充当前实现。
5. 保持现有合理结构；若必须大范围移动、合并或重新分层，停止并切换到 `/xxww-docs refactor`。
6. 缩短明显膨胀的 `AGENTS.md`，但不借 refresh 发起无关文档重构；单个代码文件行数上限等常驻工程红线不得在精简中丢失。
7. 修复链接、索引、状态标记和目录树；删除文件前先用 `rg` 清理引用。
8. 对无法从代码验证的产品决策，保留并标明决策来源；不要擅自改成实现事实。

发现本次工作中的误判或返工时，按仓库规则更新 `docs/errors.md`。只有形成长期约束的选择才写 `decisions.md`，不要把普通改动日志塞进去。

### 变化触发器

先看变更，不要默认“无需文档”：

```bash
git diff --name-status
git diff --cached --name-status
```

使用变化触发器：

- 新增、删除、移动目录或 workspace：先改完整项目树与顶层地图。
- 改公开 API、IPC、schema、migration 或数据所有权：改契约/架构文档和兼容说明。
- 改启动、测试、构建、CI、部署或端口：改所有面向执行者的命令入口。
- 改功能状态、fallback、feature flag 或生产 adapter：改 active/historical/计划表述和验收证据。
- 改安全边界、凭证、权限或副作用策略：改最高红线与相关 runbook。
- 新增同一功能的第二篇以上技术文档，或需要阅读顺序：建立 `docs/features/<feature>/README.md` 索引。

只更新受影响的事实，不顺手重写无关文档。代码与文档必须在同一变更序列中达到一致；日常代码任务需要同步文档时，内部执行本节规则，但用户入口仍是三个命令。

## 持续迭代

每次真实使用后，区分两类问题：

- 仓库特有事实缺失：修仓库文档，不把事实硬编码进 skill。
- 工作流重复失败：精简或加强 `SKILL.md`、审查量表、模板或脚本，并补脚本测试。

修改 skill 后必须运行自带测试（已含 frontmatter 自检，不依赖任何外部运行时）：

```bash
python3 .claude/skills/xxww-docs/scripts/test_docs_tools.py
```

装有 Codex skill-creator 时可额外交叉验证：

```bash
v="${CODEX_HOME:-$HOME/.codex}/skills/.system/skill-creator/scripts/quick_validate.py"
[ -f "$v" ] && python3 "$v" .claude/skills/xxww-docs
```

保持 `SKILL.md` 只承载决策与流程；细则放一层深的 `references/`，可复制产物放 `assets/`，确定性检查放 `scripts/`。不要添加 skill README、安装指南或变更日志。
