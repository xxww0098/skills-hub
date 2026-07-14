#!/usr/bin/env python3
"""Preview or create the minimal XXWW repository documentation set."""

from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

from repo_inventory import collect_inventory


TEMPLATE_TARGETS = {
    "CLAUDE.md.tmpl": "CLAUDE.md",
    "AGENTS.md.tmpl": "AGENTS.md",
    "boundaries.md.tmpl": "docs/boundaries.md",
    "architecture.md.tmpl": "docs/architecture.md",
    "errors.md.tmpl": "docs/errors.md",
    "decisions.md.tmpl": "docs/decisions.md",
}

DESCRIPTIONS = {
    ".claude": "仓库内 agent 工作流与项目级 skills",
    ".github": "GitHub 工作流与仓库自动化",
    "AGENTS.md": "唯一完整的 agent 项目规则入口",
    "CLAUDE.md": "Claude 委托入口，仅包含 @AGENTS.md",
    "apps": "可部署应用",
    "crates": "Rust crates",
    "deploy": "部署配置与运维入口",
    "docs": "项目文档",
    "examples": "示例与演示",
    "fixtures": "测试与契约夹具",
    "packages": "共享包",
    "scripts": "构建、生成与维护脚本",
    "services": "可部署服务",
    "src": "主要源代码",
    "tests": "跨模块测试",
}

REQUIRED_TOP_LEVEL = (
    {"name": "AGENTS.md", "kind": "file"},
    {"name": "CLAUDE.md", "kind": "file"},
    {"name": "docs", "kind": "dir"},
)


def _describe(name: str, kind: str) -> str:
    if name in DESCRIPTIONS:
        return DESCRIPTIONS[name]
    if kind == "file":
        return "根级配置或入口文件"
    return "顶层模块；review 时从公开入口确认唯一职责"


def _tree(data: dict) -> str:
    by_name = {item["name"]: dict(item) for item in data["top_level"]}
    for item in REQUIRED_TOP_LEVEL:
        by_name.setdefault(item["name"], dict(item))
    items = sorted(by_name.values(), key=lambda item: item["name"].lower())
    lines = [f"{data['project_name']}/"]
    for index, item in enumerate(items):
        branch = "└──" if index == len(items) - 1 else "├──"
        suffix = "/" if item["kind"] == "dir" else ""
        label = f"{item['name']}{suffix}"
        lines.append(f"{branch} {label:<28} # {_describe(item['name'], item['kind'])}")
    return "\n".join(lines)


def _commands(root: Path, data: dict) -> str:
    commands: list[str] = []
    if (root / "pnpm-lock.yaml").is_file():
        commands.append("pnpm install --frozen-lockfile")
        runner = "pnpm"
    elif (root / "yarn.lock").is_file():
        commands.append("yarn install --frozen-lockfile")
        runner = "yarn"
    elif (root / "package-lock.json").is_file():
        commands.append("npm ci")
        runner = "npm run"
    elif (root / "package.json").is_file():
        commands.append("npm install")
        runner = "npm run"
    else:
        runner = ""

    scripts = data.get("package", {}).get("scripts", {})
    preferred = ("dev", "start", "check", "typecheck", "lint", "test", "build")
    for name in preferred:
        if name not in scripts:
            continue
        command = f"{runner} {name}" if runner else name
        if command not in commands:
            commands.append(command)
    if (root / "Cargo.toml").is_file() and "cargo test" not in commands:
        commands.append("cargo test")
    if (root / "pyproject.toml").is_file() and not any("test" in item for item in commands):
        commands.append("python -m pytest")
    if not commands:
        commands.append("# 未从 manifest 发现稳定命令；review 时基于 CI 和脚本补充")
    return "\n".join(commands)


def _needs_architecture(root: Path, data: dict) -> bool:
    """architecture.md 只在出现多交付面证据时出生；单交付面仓由 boundaries.md 承载运行关系。"""
    if data.get("package", {}).get("workspaces"):
        return True
    manifests = ("package.json", "Cargo.toml", "go.mod", "pyproject.toml")
    if sum(1 for name in manifests if (root / name).is_file()) >= 2:
        return True
    surface_dirs = {"apps", "packages", "services", "crates"}
    top_dirs = {item["name"] for item in data["top_level"] if item["kind"] == "dir"}
    return len(surface_dirs & top_dirs) >= 2


def render_documents(root: Path) -> dict[Path, str]:
    root = root.resolve()
    data = collect_inventory(root)
    replacements = {
        "{{PROJECT_NAME}}": data["project_name"],
        "{{PROJECT_TREE}}": _tree(data),
        "{{COMMANDS}}": _commands(root, data),
        "{{GENERATED_DATE}}": date.today().isoformat(),
    }
    template_dir = Path(__file__).resolve().parent.parent / "assets" / "templates"
    include_architecture = _needs_architecture(root, data)
    rendered: dict[Path, str] = {}
    for template_name, target_name in TEMPLATE_TARGETS.items():
        if target_name == "docs/architecture.md" and not include_architecture:
            continue
        content = (template_dir / template_name).read_text(encoding="utf-8")
        for marker, value in replacements.items():
            content = content.replace(marker, value)
        if not include_architecture:
            content = "".join(
                line for line in content.splitlines(keepends=True) if "architecture.md" not in line
            )
        rendered[root / target_name] = content
    return rendered


def _blocking_files(root: Path, targets: list[Path]) -> list[Path]:
    """待创建目标的中间路径里已存在的非目录条目；命中即无法安全写入。"""
    blockers: set[Path] = set()
    for target in targets:
        current = root
        for part in target.relative_to(root).parts[:-1]:
            current = current / part
            if current.exists() and not current.is_dir():
                blockers.add(current.relative_to(root))
                break
    return sorted(blockers)


def apply_documents(root: Path, apply: bool) -> tuple[list[Path], list[Path]]:
    created: list[Path] = []
    skipped: list[Path] = []
    rendered = render_documents(root)
    if apply:
        # 先整体校验再落盘，避免写到一半才因 docs 是普通文件而崩溃
        blockers = _blocking_files(root.resolve(), [t for t in rendered if not t.exists()])
        if blockers:
            listing = "、".join(str(item) for item in blockers)
            raise SystemExit(f"无法创建文档：{listing} 已存在且不是目录；请先移除或改名后再 --apply（未写入任何文件）")
    for target, content in rendered.items():
        relative = target.relative_to(root.resolve())
        if target.exists():
            skipped.append(relative)
            print(f"SKIP existing: {relative}")
            continue
        if apply:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
            created.append(relative)
            print(f"CREATE: {relative}")
        else:
            print(f"WOULD CREATE: {relative}")
            print(content)
    return created, skipped


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="Repository root")
    parser.add_argument("--apply", action="store_true", help="Create missing files")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    apply_documents(root, args.apply)
    if not args.apply:
        print("Preview only. Re-run with --apply to create missing files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
