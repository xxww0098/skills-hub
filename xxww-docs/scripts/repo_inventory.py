#!/usr/bin/env python3
"""Collect a compact, evidence-oriented repository inventory."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
from collections import Counter
from pathlib import Path
from typing import Any


IGNORED_DIRS = {
    ".cache",
    ".expo",
    ".git",
    ".gradle",
    ".idea",
    ".mypy_cache",
    ".next",
    ".nuxt",
    ".output",
    ".pytest_cache",
    ".ruff_cache",
    ".svelte-kit",
    ".turbo",
    ".venv",
    "DerivedData",
    "Pods",
    "__pycache__",
    "build",
    "coverage",
    "dist",
    "node_modules",
    "out",
    "release",
    "target",
    "tmp",
    "vendor",
    "worktrees",
}

MANIFEST_NAMES = {
    "Cargo.toml",
    "Dockerfile",
    "Makefile",
    "biome.json",
    "compose.yaml",
    "compose.yml",
    "deno.json",
    "docker-compose.yaml",
    "docker-compose.yml",
    "eslint.config.js",
    "eslint.config.mjs",
    "go.mod",
    "package.json",
    "pnpm-workspace.yaml",
    "pyproject.toml",
    "requirements.txt",
    "rust-toolchain.toml",
    "tsconfig.json",
    "vite.config.ts",
}

EXTENSION_LANGUAGE = {
    ".c": "C",
    ".cpp": "C++",
    ".css": "CSS",
    ".go": "Go",
    ".html": "HTML",
    ".java": "Java",
    ".js": "JavaScript",
    ".jsx": "JavaScript",
    ".kt": "Kotlin",
    ".md": "Markdown",
    ".mjs": "JavaScript",
    ".py": "Python",
    ".rb": "Ruby",
    ".rs": "Rust",
    ".scss": "SCSS",
    ".sh": "Shell",
    ".sql": "SQL",
    ".svelte": "Svelte",
    ".swift": "Swift",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".vue": "Vue",
}


def _walk_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for current, dirs, names in os.walk(root):
        dirs[:] = sorted(d for d in dirs if d not in IGNORED_DIRS)
        current_path = Path(current)
        files.extend(current_path / name for name in sorted(names))
    return files


def _git(root: Path, *args: str) -> str | None:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return result.stdout.strip()


def _package_data(root: Path) -> dict[str, Any]:
    package_file = root / "package.json"
    if not package_file.is_file():
        return {}
    try:
        data = json.loads(package_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"parse_error": True}
    workspaces = data.get("workspaces", [])
    if isinstance(workspaces, dict):
        workspaces = workspaces.get("packages", [])
    return {
        "name": data.get("name"),
        "scripts": data.get("scripts", {}),
        "workspaces": workspaces if isinstance(workspaces, list) else [],
    }


def collect_inventory(root: Path) -> dict[str, Any]:
    root = root.resolve()
    files = _walk_files(root)
    languages: Counter[str] = Counter()
    manifests: list[str] = []
    docs: list[str] = []

    for path in files:
        relative = path.relative_to(root)
        language = EXTENSION_LANGUAGE.get(path.suffix.lower())
        if language:
            languages[language] += 1
        if path.name in MANIFEST_NAMES or path.name.startswith("Dockerfile."):
            manifests.append(relative.as_posix())
        if path.suffix.lower() == ".md" and (
            relative.name == "AGENTS.md" or relative.parts[0] == "docs"
        ):
            docs.append(relative.as_posix())

    top_level = []
    for entry in sorted(root.iterdir(), key=lambda item: item.name.lower()):
        if entry.name in IGNORED_DIRS or entry.name == ".git":
            continue
        if entry.name.startswith(".") and entry.name not in {".claude", ".github"}:
            continue
        top_level.append({"name": entry.name, "kind": "dir" if entry.is_dir() else "file"})

    return {
        "root": str(root),
        "project_name": root.name,
        "git_branch": _git(root, "branch", "--show-current"),
        "git_status": (_git(root, "status", "--short") or "").splitlines(),
        "top_level": top_level,
        "languages": dict(languages.most_common()),
        "manifests": sorted(manifests),
        "documents": sorted(docs),
        "package": _package_data(root),
        "file_count": len(files),
    }


def format_markdown(data: dict[str, Any]) -> str:
    lines = [
        f"# Repository inventory: {data['project_name']}",
        "",
        f"- Root: `{data['root']}`",
        f"- Git branch: `{data.get('git_branch') or 'unknown'}`",
        f"- Files scanned: {data['file_count']}",
        f"- Dirty paths: {len(data['git_status'])}",
        "",
        "## Top level",
        "",
    ]
    lines.extend(f"- `{item['name']}` ({item['kind']})" for item in data["top_level"])
    lines.extend(["", "## Languages by file count", ""])
    lines.extend(f"- {name}: {count}" for name, count in data["languages"].items())
    lines.extend(["", "## Root package scripts", ""])
    scripts = data.get("package", {}).get("scripts", {})
    lines.extend(f"- `npm run {name}` → `{command}`" for name, command in scripts.items())
    if not scripts:
        lines.append("- None discovered")
    lines.extend(["", "## Manifests", ""])
    lines.extend(f"- `{path}`" for path in data["manifests"])
    lines.extend(["", "## Governed documents", ""])
    lines.extend(f"- `{path}`" for path in data["documents"])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="Repository root")
    parser.add_argument("--format", choices=("json", "markdown"), default="markdown")
    args = parser.parse_args()
    data = collect_inventory(Path(args.root))
    if args.format == "json":
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print(format_markdown(data), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
