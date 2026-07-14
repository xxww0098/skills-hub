#!/usr/bin/env python3
"""Audit repository documentation for deterministic drift signals."""

from __future__ import annotations

import argparse
import json
import os
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from urllib.parse import unquote

from repo_inventory import IGNORED_DIRS, collect_inventory


# 链接文本允许内嵌完整图片（徽章 [![b](img)](target)），检查的是外层真实目标；纯图片仍被 (?<!!) 豁免
LINK_RE = re.compile(r"(?<!!)\[(?:!\[[^\]]*\]\([^)]*\)|[^\]])+\]\(([^)]+)\)")
STATUS_RE = re.compile(r"状态[：:]\s*(active|historical)\b", re.IGNORECASE)
PLACEHOLDER_RE = re.compile(r"\{\{[A-Z][A-Z0-9_]*\}\}|\[TODO(?::|\])", re.IGNORECASE)
EXCLUDED_PARTS = {"node_modules", "templates"}
# docs/ 根只放宪章；其余进 docs/features/<功能>/ 或 docs/others/（待决策暂存）
ALLOWED_DOCS_ROOT = {"boundaries.md", "errors.md", "decisions.md", "architecture.md"}
IMPLEMENTATION_MANIFESTS = ("package.json", "Cargo.toml", "go.mod", "pyproject.toml")
SCAFFOLD_MARKERS = (
    "基于当前代码清单维护的项目",
    "顶层模块；review 时从公开入口确认唯一职责",
    "请基于 composition root、manifest 和公开入口补充职责与反职责",
    "审查 API、IPC、CLI、数据库、文件系统和外部服务",
    "根据应用入口、部署配置和外部依赖绘制运行蓝图",
    "列出核心数据、唯一事实源、读写方、持久化位置和敏感性边界",
    "记录必须跨实现保持成立的安全、事务、兼容和失败处理规则",
    "只记录 manifest、lockfile 或工具链配置能验证的技术与版本",
)
# 单个代码文件行数上限（AGENTS.md 红线的确定性执法；生成物/vendored/快照豁免）
CODE_FILE_LINE_LIMIT = 1000
CODE_EXTENSIONS = {
    ".c", ".cc", ".cjs", ".cpp", ".cs", ".go", ".java", ".js", ".jsx",
    ".kt", ".mjs", ".py", ".rb", ".rs", ".sh", ".sql", ".svelte",
    ".swift", ".ts", ".tsx", ".vue",
}
# 首部出现任一标记即视为生成物，豁免行数上限（大小写不敏感）
GENERATED_MARKERS = ("@generated", "do not edit", "auto-generated", "自动生成", "由脚本生成")


@dataclass(frozen=True)
class Finding:
    severity: str
    code: str
    path: str
    message: str


def _sort_key(item: Finding) -> tuple[str, str, str, str]:
    return (item.severity, item.path, item.code, item.message)


def _read_utf8(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return None


def _documents(root: Path) -> list[Path]:
    paths: list[Path] = []
    agents = root / "AGENTS.md"
    if agents.is_file():
        paths.append(agents)
    docs = root / "docs"
    if docs.is_dir():
        for path in sorted(docs.rglob("*.md")):
            if EXCLUDED_PARTS.intersection(path.relative_to(docs).parts):
                continue
            paths.append(path)
    return paths


def _link_target(source: Path, raw_target: str, root: Path) -> Path | None:
    raw = raw_target.strip()
    if raw.startswith("<") and ">" in raw:
        # <...> 是 markdown 对含空格目标的合法包裹写法
        target = raw[1 : raw.index(">")].strip()
    else:
        tokens = raw.split(maxsplit=1)
        if not tokens:
            return None
        if len(tokens) == 1 or tokens[1].startswith(('"', "'", "(")):
            target = tokens[0].strip("<>")
        else:
            # 空格后不是带引号的 title：整段都是目标路径，不能只取首 token
            target = raw.strip("<>")
    if not target or target.startswith(("#", "http://", "https://", "mailto:")):
        return None
    target = unquote(target.split("#", 1)[0].split("?", 1)[0])
    if not target or target.startswith("//"):
        return None
    if target.startswith("/"):
        # 仓根绝对路径以 audit root 为基解析，不落到文件系统根
        return (root / target.lstrip("/")).resolve()
    return (source.parent / target).resolve()


def _prose_only(content: str) -> str:
    without_fences = re.sub(r"```.*?```|~~~.*?~~~", "", content, flags=re.DOTALL)
    return re.sub(r"`[^`\n]+`", "", without_fences)


def _is_generated(head: str) -> bool:
    lowered = head.lower()
    return any(marker in lowered for marker in GENERATED_MARKERS)


def _oversized_code_files(root: Path) -> list[Finding]:
    """扫描产品源码，标记超过行数上限的文件；只看 IGNORED_DIRS 之外的点外目录。"""
    findings: list[Finding] = []
    for current, dirs, names in os.walk(root):
        # 剪掉生成/依赖目录与一切点目录（.git/.claude/.github 等工具链不算产品代码）
        dirs[:] = sorted(d for d in dirs if d not in IGNORED_DIRS and not d.startswith("."))
        for name in sorted(names):
            if ".min." in name or Path(name).suffix.lower() not in CODE_EXTENSIONS:
                continue
            path = Path(current) / name
            content = _read_utf8(path)
            if content is None:
                continue
            lines = content.splitlines()
            if _is_generated("\n".join(lines[:40])):
                continue
            if len(lines) > CODE_FILE_LINE_LIMIT:
                relative = path.relative_to(root).as_posix()
                findings.append(
                    Finding(
                        "P2",
                        "code-file-too-long",
                        relative,
                        f"共 {len(lines)} 行，超过 {CODE_FILE_LINE_LIMIT} 行上限；按职责拆分模块",
                    )
                )
    return findings


def audit(root: Path) -> list[Finding]:
    root = root.resolve()
    findings: list[Finding] = []
    has_implementation = any((root / name).is_file() for name in IMPLEMENTATION_MANIFESTS)
    required = ("CLAUDE.md", "AGENTS.md", "docs/boundaries.md", "docs/errors.md", "docs/decisions.md")
    for relative in required:
        if not (root / relative).is_file():
            findings.append(Finding("P1", "missing-core-doc", relative, "缺少最小治理文档"))

    claude = root / "CLAUDE.md"
    if claude.is_file():
        try:
            delegation = claude.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            findings.append(Finding("P1", "invalid-utf8", "CLAUDE.md", "CLAUDE.md 不是 UTF-8"))
        else:
            if delegation not in {"@AGENTS.md", "@AGENTS.md\n"}:
                findings.append(
                    Finding(
                        "P1",
                        "invalid-claude-delegation",
                        "CLAUDE.md",
                        "内容必须只有 @AGENTS.md，可带一个末尾换行",
                    )
                )

    for path in _documents(root):
        relative = path.relative_to(root).as_posix()
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            findings.append(Finding("P1", "invalid-utf8", relative, "Markdown 不是 UTF-8"))
            continue

        if relative.startswith("docs/"):
            header = "\n".join(content.splitlines()[:20])
            status = STATUS_RE.search(header)
            if status is None:
                findings.append(Finding("P2", "missing-status", relative, "前 20 行缺少 active/historical 状态"))
            elif status.group(1).lower() == "historical":
                # 冻结稿只读不照抄：占位符、旧链接与空壳不构成待修复项
                continue
        prose = _prose_only(content)
        if has_implementation:
            markers = [marker for marker in SCAFFOLD_MARKERS if marker in prose]
            if markers:
                findings.append(
                    Finding(
                        "P1",
                        "unresolved-scaffold",
                        relative,
                        f"已有实现但仍保留初始化空壳：{'；'.join(markers)}",
                    )
                )
        if PLACEHOLDER_RE.search(prose):
            findings.append(Finding("P1", "placeholder", relative, "active 文档含未处理占位符"))
        for match in LINK_RE.finditer(prose):
            target = _link_target(path, match.group(1), root)
            if target is not None and not target.exists():
                findings.append(
                    Finding("P1", "broken-link", relative, f"本地链接不存在：{match.group(1)}")
                )

    agents = root / "AGENTS.md"
    agents_content = _read_utf8(agents) if agents.is_file() else None
    if agents_content is not None:
        line_count = len(agents_content.splitlines())
        if line_count > 220:
            findings.append(
                Finding("P2", "agents-too-long", "AGENTS.md", f"共 {line_count} 行；应下沉细则并保留入口信息")
            )

    boundaries = root / "docs" / "boundaries.md"
    content = _read_utf8(boundaries) if boundaries.is_file() else None
    if content is not None:
        inventory = collect_inventory(root)
        for item in inventory["top_level"]:
            if item["kind"] != "dir":
                continue
            name = item["name"]
            # 必须以目录形态 `name/` 被提及，且左侧不粘连路径或英文词（防 latest 覆盖 test/）
            if re.search(rf"(?<![A-Za-z0-9_./-]){re.escape(name)}/", content) is None:
                findings.append(
                    Finding("P2", "tree-missing-top-level", "docs/boundaries.md", f"完整项目树未提及顶层目录 `{name}/`")
                )

    docs_dir = root / "docs"
    if docs_dir.is_dir():
        for path in sorted(docs_dir.glob("*.md")):
            if path.name not in ALLOWED_DOCS_ROOT:
                findings.append(
                    Finding(
                        "P2",
                        "docs-root-flat",
                        f"docs/{path.name}",
                        "docs/ 根只放宪章（boundaries/errors/decisions/architecture）；功能文档进 docs/features/<功能>/，未归位与历史稿进 docs/others/ 待决策",
                    )
                )

    features = root / "docs" / "features"
    if features.is_dir():
        for directory in sorted(path for path in features.iterdir() if path.is_dir()):
            pages = [path for path in directory.glob("*.md") if path.name != "README.md"]
            if len(pages) >= 2 and not (directory / "README.md").is_file():
                relative = directory.relative_to(root).as_posix()
                findings.append(Finding("P2", "missing-feature-index", relative, "多篇功能文档缺少 README.md 索引"))

    findings.extend(_oversized_code_files(root))

    return sorted(findings, key=_sort_key)


def diff_findings(baseline: list[Finding], current: list[Finding]) -> dict[str, list[Finding]]:
    """Split current findings against a baseline run: only `new` must be fixed."""
    baseline_set = set(baseline)
    current_set = set(current)
    return {
        "new": sorted(current_set - baseline_set, key=_sort_key),
        "resolved": sorted(baseline_set - current_set, key=_sort_key),
        "preexisting": sorted(current_set & baseline_set, key=_sort_key),
    }


def _load_baseline(path: Path) -> list[Finding]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return [Finding(**item) for item in data]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="Repository root")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--exit-zero", action="store_true", help="Report findings without a failing exit status")
    parser.add_argument("--baseline", help="Path to a previous --format json report; only new findings fail")
    args = parser.parse_args()
    findings = audit(Path(args.root))
    if args.baseline:
        groups = diff_findings(_load_baseline(Path(args.baseline)), findings)
        failing = groups["new"]
        if args.format == "json":
            print(
                json.dumps(
                    {key: [asdict(item) for item in items] for key, items in groups.items()},
                    ensure_ascii=False,
                    indent=2,
                )
            )
        else:
            for item in groups["new"]:
                print(f"NEW {item.severity} {item.code} {item.path}: {item.message}")
            print(
                f"{len(groups['new'])} new / {len(groups['resolved'])} resolved / "
                f"{len(groups['preexisting'])} pre-existing"
            )
    else:
        failing = findings
        if args.format == "json":
            print(json.dumps([asdict(item) for item in findings], ensure_ascii=False, indent=2))
        elif findings:
            for item in findings:
                print(f"{item.severity} {item.code} {item.path}: {item.message}")
            print(f"\n{len(findings)} finding(s)")
        else:
            print("Documentation audit passed.")
    return 0 if args.exit_zero or not failing else 1


if __name__ == "__main__":
    raise SystemExit(main())
