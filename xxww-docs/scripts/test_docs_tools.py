#!/usr/bin/env python3

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from docs_audit import audit, diff_findings  # noqa: E402
from init_docs import apply_documents, render_documents  # noqa: E402
from repo_inventory import collect_inventory  # noqa: E402


class DocsToolsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name) / "sample-repo"
        root.mkdir()
        self.root = root.resolve()
        (self.root / "src").mkdir()
        (self.root / "src" / "main.ts").write_text("export {};\n", encoding="utf-8")
        (self.root / "package-lock.json").write_text("{}\n", encoding="utf-8")
        # workspaces 使夹具呈现多交付面证据，architecture.md 随 init 出生
        (self.root / "package.json").write_text(
            json.dumps(
                {
                    "name": "sample",
                    "scripts": {"test": "vitest", "build": "tsc"},
                    "workspaces": ["packages/*"],
                }
            ),
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_inventory_collects_scripts_and_language(self) -> None:
        data = collect_inventory(self.root)
        self.assertEqual(data["package"]["scripts"]["test"], "vitest")
        self.assertEqual(data["languages"]["TypeScript"], 1)

    def test_skill_exposes_exactly_three_user_commands(self) -> None:
        skill = (SCRIPT_DIR.parent / "SKILL.md").read_text(encoding="utf-8")
        for command in ("/xxww-docs init", "/xxww-docs refactor", "/xxww-docs refresh"):
            self.assertIn(command, skill)
        self.assertNotIn("## `/xxww-docs review`", skill)
        self.assertNotIn("## `/xxww-docs maintain`", skill)
        self.assertIn("### 唯一路由阈值", skill)
        self.assertIn("### `--check` 固定产出", skill)
        self.assertIn("逐文件迁移表", skill)
        self.assertIn("零写入证明", skill)

    def test_init_creates_only_missing_files(self) -> None:
        rendered = render_documents(self.root)
        self.assertIn(self.root / "AGENTS.md", rendered)
        self.assertIn(self.root / "CLAUDE.md", rendered)
        created, skipped = apply_documents(self.root, True)
        self.assertEqual(len(created), 6)
        self.assertFalse(skipped)
        self.assertEqual((self.root / "CLAUDE.md").read_text(encoding="utf-8"), "@AGENTS.md\n")
        original = (self.root / "AGENTS.md").read_text(encoding="utf-8")
        created_again, skipped_again = apply_documents(self.root, True)
        self.assertFalse(created_again)
        self.assertEqual(len(skipped_again), 6)
        self.assertEqual((self.root / "AGENTS.md").read_text(encoding="utf-8"), original)

    def test_init_supports_a_completely_empty_project(self) -> None:
        empty = (Path(self.temp.name) / "empty-project").resolve()
        empty.mkdir()
        created, skipped = apply_documents(empty, True)
        self.assertEqual(len(created), 5)
        self.assertNotIn(Path("docs/architecture.md"), created)
        self.assertFalse(skipped)
        self.assertTrue((empty / "AGENTS.md").is_file())
        self.assertEqual((empty / "CLAUDE.md").read_text(encoding="utf-8"), "@AGENTS.md\n")
        boundaries = (empty / "docs" / "boundaries.md").read_text(encoding="utf-8")
        self.assertIn("AGENTS.md", boundaries)
        self.assertIn("CLAUDE.md", boundaries)
        unresolved = [item for item in audit(empty) if item.code == "unresolved-scaffold"]
        self.assertFalse(unresolved)

    def test_audit_rejects_scaffolds_in_an_implemented_project(self) -> None:
        apply_documents(self.root, True)
        unresolved = [item for item in audit(self.root) if item.code == "unresolved-scaffold"]
        paths = {item.path for item in unresolved}
        self.assertIn("AGENTS.md", paths)
        self.assertIn("docs/boundaries.md", paths)
        self.assertIn("docs/architecture.md", paths)

    def test_audit_requires_exact_claude_delegation(self) -> None:
        apply_documents(self.root, True)
        claude = self.root / "CLAUDE.md"
        claude.unlink()
        missing = [item for item in audit(self.root) if item.path == "CLAUDE.md"]
        self.assertTrue(any(item.code == "missing-core-doc" for item in missing))
        claude.write_text("# Rules\n@AGENTS.md\n", encoding="utf-8")
        invalid = [item for item in audit(self.root) if item.path == "CLAUDE.md"]
        self.assertTrue(any(item.code == "invalid-claude-delegation" for item in invalid))

    def test_audit_detects_broken_link_and_placeholder(self) -> None:
        apply_documents(self.root, True)
        architecture = self.root / "docs" / "architecture.md"
        architecture.write_text(
            architecture.read_text(encoding="utf-8") + "\n[missing](absent.md)\n{{TODO}}\n",
            encoding="utf-8",
        )
        codes = {item.code for item in audit(self.root)}
        self.assertIn("broken-link", codes)
        self.assertIn("placeholder", codes)

    def test_audit_ignores_template_syntax_in_code_examples(self) -> None:
        apply_documents(self.root, True)
        errors = self.root / "docs" / "errors.md"
        errors.write_text(
            errors.read_text(encoding="utf-8")
            + '\n`{{PROJECT_NAME}}`\n\n```bash\ndocker ps --format "{{.Image}}"\n```\n',
            encoding="utf-8",
        )
        placeholders = [item for item in audit(self.root) if item.code == "placeholder"]
        self.assertFalse(placeholders)

    def test_audit_exempts_historical_docs_from_content_checks(self) -> None:
        apply_documents(self.root, True)
        frozen = self.root / "docs" / "old-spec.md"
        frozen.write_text(
            "# Old spec\n\n> 状态：historical\n\n[gone](missing.md)\n{{TODO}}\n",
            encoding="utf-8",
        )
        # 内容检查（断链/占位符/空壳）豁免；docs-root-flat 是放置检查，不豁免
        content_findings = [
            item
            for item in audit(self.root)
            if item.path == "docs/old-spec.md" and item.code != "docs-root-flat"
        ]
        self.assertFalse(content_findings)

    def test_baseline_diff_reports_only_new_findings(self) -> None:
        apply_documents(self.root, True)
        before = audit(self.root)
        architecture = self.root / "docs" / "architecture.md"
        architecture.write_text(
            architecture.read_text(encoding="utf-8") + "\n[missing](absent.md)\n",
            encoding="utf-8",
        )
        groups = diff_findings(before, audit(self.root))
        self.assertEqual([item.code for item in groups["new"]], ["broken-link"])
        self.assertFalse(groups["resolved"])
        self.assertEqual(len(groups["preexisting"]), len(before))

    def test_skill_frontmatter_is_self_contained(self) -> None:
        text = (SCRIPT_DIR.parent / "SKILL.md").read_text(encoding="utf-8")
        self.assertTrue(text.startswith("---\n"))
        frontmatter = text.split("---", 2)[1]
        fields = dict(
            line.split(":", 1) for line in frontmatter.strip().splitlines() if ":" in line
        )
        self.assertEqual(set(fields), {"name", "description"})
        self.assertEqual(fields["name"].strip(), SCRIPT_DIR.parent.name)
        self.assertLessEqual(len(fields["description"].strip()), 1024)

    def test_audit_requires_status_on_feature_readmes(self) -> None:
        apply_documents(self.root, True)
        feature = self.root / "docs" / "features" / "sample"
        feature.mkdir(parents=True)
        readme = feature / "README.md"
        readme.write_text("# Sample\n", encoding="utf-8")
        missing = [item for item in audit(self.root) if item.path.endswith("README.md")]
        self.assertTrue(any(item.code == "missing-status" for item in missing))
        readme.write_text("# Sample\n\n> 状态：active\n", encoding="utf-8")
        fixed = [item for item in audit(self.root) if item.path.endswith("README.md")]
        self.assertFalse(any(item.code == "missing-status" for item in fixed))

    def test_audit_survives_blank_link_target(self) -> None:
        apply_documents(self.root, True)
        page = self.root / "docs" / "blank-link.md"
        page.write_text("# 空链\n\n> 状态：active\n\n[悬空]( )\n", encoding="utf-8")
        findings = audit(self.root)  # 修复前此处 IndexError 中断整个审计
        self.assertFalse(
            [
                item
                for item in findings
                if item.path == "docs/blank-link.md" and item.code != "docs-root-flat"
            ]
        )

    def test_audit_resolves_repo_root_absolute_links_against_root(self) -> None:
        apply_documents(self.root, True)
        page = self.root / "docs" / "absolute-links.md"
        page.write_text(
            "# 绝对链接\n\n> 状态：active\n\n[仓内](/docs/errors.md)\n[仓外](/etc/hosts)\n",
            encoding="utf-8",
        )
        broken = [
            item.message
            for item in audit(self.root)
            if item.code == "broken-link" and item.path == "docs/absolute-links.md"
        ]
        self.assertEqual(len(broken), 1)
        self.assertIn("/etc/hosts", broken[0])

    def test_audit_checks_outer_target_of_badge_links(self) -> None:
        apply_documents(self.root, True)
        page = self.root / "docs" / "badges.md"
        page.write_text(
            "# 徽章\n\n> 状态：active\n\n"
            "[![好徽章](missing-shield.png)](errors.md)\n"
            "[![坏徽章](missing-shield.png)](missing-target.md)\n",
            encoding="utf-8",
        )
        broken = [
            item.message
            for item in audit(self.root)
            if item.code == "broken-link" and item.path == "docs/badges.md"
        ]
        self.assertEqual(len(broken), 1)
        self.assertIn("missing-target.md", broken[0])
        self.assertNotIn("missing-shield.png", broken[0])

    def test_audit_reports_bare_space_target_despite_decoy_file(self) -> None:
        apply_documents(self.root, True)
        (self.root / "docs" / "my").write_text("诱饵文件\n", encoding="utf-8")
        page = self.root / "docs" / "spaced-link.md"
        page.write_text(
            '# 空格目标\n\n> 状态：active\n\n[坏](my missing-file.md)\n[好](errors.md "标题")\n',
            encoding="utf-8",
        )
        broken = [
            item.message
            for item in audit(self.root)
            if item.code == "broken-link" and item.path == "docs/spaced-link.md"
        ]
        self.assertEqual(len(broken), 1)
        self.assertIn("my missing-file.md", broken[0])

    def test_tree_check_is_not_fooled_by_substring_mentions(self) -> None:
        (self.root / "test").mkdir()
        docs = self.root / "docs"
        docs.mkdir()
        boundaries = docs / "boundaries.md"
        head = "# 边界\n\n> 状态：active\n\ndocs/ 与 src/ 已覆盖；更新走 latest/ 频道\n"
        boundaries.write_text(head, encoding="utf-8")
        missing = [item for item in audit(self.root) if item.code == "tree-missing-top-level"]
        self.assertEqual(len(missing), 1)
        self.assertIn("`test/`", missing[0].message)
        boundaries.write_text(head + "\ntest/ 跨模块测试\n", encoding="utf-8")
        self.assertFalse(
            [item for item in audit(self.root) if item.code == "tree-missing-top-level"]
        )

    def test_audit_reports_unmentioned_top_level_directory(self) -> None:
        docs = self.root / "docs"
        docs.mkdir()
        (docs / "boundaries.md").write_text(
            "# 边界\n\n> 状态：active\n\n只提及 docs/ 自身\n", encoding="utf-8"
        )
        missing = [item for item in audit(self.root) if item.code == "tree-missing-top-level"]
        self.assertEqual(len(missing), 1)
        self.assertIn("`src/`", missing[0].message)

    def test_audit_reports_invalid_utf8_documents(self) -> None:
        apply_documents(self.root, True)
        (self.root / "docs" / "binary.md").write_bytes(b"\xff\xfe\x00 not utf-8")
        (self.root / "CLAUDE.md").write_bytes(b"\xff@AGENTS.md\n")
        findings = {(item.code, item.path) for item in audit(self.root)}
        self.assertIn(("invalid-utf8", "docs/binary.md"), findings)
        self.assertIn(("invalid-utf8", "CLAUDE.md"), findings)

    def test_audit_reports_agents_over_line_budget(self) -> None:
        apply_documents(self.root, True)
        agents = self.root / "AGENTS.md"
        agents.write_text("\n".join(f"规则 {i}" for i in range(221)) + "\n", encoding="utf-8")
        self.assertIn("agents-too-long", {item.code for item in audit(self.root)})
        agents.write_text("\n".join(f"规则 {i}" for i in range(220)) + "\n", encoding="utf-8")
        self.assertNotIn("agents-too-long", {item.code for item in audit(self.root)})

    def test_audit_flags_oversized_code_files(self) -> None:
        apply_documents(self.root, True)
        big = self.root / "src" / "huge.ts"

        def write(line_count: int, prefix: str = "") -> None:
            body = "\n".join(f"const x{i} = {i};" for i in range(line_count))
            big.write_text(prefix + body + "\n", encoding="utf-8")

        write(1001)
        self.assertIn(("code-file-too-long", "src/huge.ts"), {(i.code, i.path) for i in audit(self.root)})
        # 恰好在上限内不报
        write(1000)
        self.assertNotIn("code-file-too-long", {i.code for i in audit(self.root)})
        # 生成物标记豁免
        write(1001, prefix="// @generated\n")
        self.assertNotIn("code-file-too-long", {i.code for i in audit(self.root)})
        # 压缩产物与点目录（.claude 等工具链）不计
        write(1001)
        (self.root / "vendor.min.js").write_text(
            ";".join(f"a{i}={i}" for i in range(2000)) + "\n", encoding="utf-8"
        )
        skill_dir = self.root / ".claude" / "skills" / "demo"
        skill_dir.mkdir(parents=True)
        (skill_dir / "tool.py").write_text(
            "\n".join(f"x{i} = {i}" for i in range(1200)) + "\n", encoding="utf-8"
        )
        flagged = {i.path for i in audit(self.root) if i.code == "code-file-too-long"}
        self.assertEqual(flagged, {"src/huge.ts"})

    def test_audit_requires_feature_index_for_multi_page_features(self) -> None:
        apply_documents(self.root, True)
        feature = self.root / "docs" / "features" / "billing"
        feature.mkdir(parents=True)
        (feature / "overview.md").write_text("# 概览\n\n> 状态：active\n", encoding="utf-8")
        (feature / "limits.md").write_text("# 限额\n\n> 状态：active\n", encoding="utf-8")
        missing = [item for item in audit(self.root) if item.code == "missing-feature-index"]
        self.assertEqual([item.path for item in missing], ["docs/features/billing"])
        (feature / "README.md").write_text("# 索引\n\n> 状态：active\n", encoding="utf-8")
        self.assertFalse(
            [item for item in audit(self.root) if item.code == "missing-feature-index"]
        )

    def test_init_skips_architecture_for_single_surface_repo(self) -> None:
        single = (Path(self.temp.name) / "single-surface").resolve()
        single.mkdir()
        (single / "package.json").write_text(
            json.dumps({"name": "single", "scripts": {"test": "vitest"}}), encoding="utf-8"
        )
        created, _ = apply_documents(single, True)
        self.assertEqual(len(created), 5)
        self.assertFalse((single / "docs" / "architecture.md").exists())
        agents = (single / "AGENTS.md").read_text(encoding="utf-8")
        self.assertNotIn("architecture.md", agents)
        self.assertNotIn("broken-link", {item.code for item in audit(single)})

    def test_init_creates_architecture_when_surfaces_emerge(self) -> None:
        single = (Path(self.temp.name) / "growing").resolve()
        single.mkdir()
        (single / "package.json").write_text(json.dumps({"name": "growing"}), encoding="utf-8")
        first, _ = apply_documents(single, True)
        self.assertNotIn(Path("docs/architecture.md"), first)
        (single / "Cargo.toml").write_text("[package]\nname = \"growing\"\n", encoding="utf-8")
        second, skipped = apply_documents(single, True)
        self.assertEqual(second, [Path("docs/architecture.md")])
        self.assertEqual(len(skipped), 5)

    def test_audit_flags_non_charter_docs_flat_at_docs_root(self) -> None:
        apply_documents(self.root, True)
        clean = [item for item in audit(self.root) if item.code == "docs-root-flat"]
        self.assertFalse(clean)  # boundaries/errors/decisions/architecture 是宪章，不报
        (self.root / "docs" / "deploy.md").write_text(
            "# 部署\n\n> 状态：active\n", encoding="utf-8"
        )
        others = self.root / "docs" / "others"
        others.mkdir()
        (others / "old-plan.md").write_text(
            "# 旧计划\n\n> 状态：historical\n", encoding="utf-8"
        )
        feature = self.root / "docs" / "features" / "deploy"
        feature.mkdir(parents=True)
        (feature / "pipeline.md").write_text("# 流水线\n\n> 状态：active\n", encoding="utf-8")
        flagged = [item for item in audit(self.root) if item.code == "docs-root-flat"]
        self.assertEqual([item.path for item in flagged], ["docs/deploy.md"])

    def test_audit_requires_decisions_doc(self) -> None:
        apply_documents(self.root, True)
        (self.root / "docs" / "decisions.md").unlink()
        findings = {(item.code, item.path) for item in audit(self.root)}
        self.assertIn(("missing-core-doc", "docs/decisions.md"), findings)

    def test_init_apply_fails_cleanly_when_docs_is_a_regular_file(self) -> None:
        project = (Path(self.temp.name) / "docs-as-file").resolve()
        project.mkdir()
        (project / "docs").write_text("我是普通文件\n", encoding="utf-8")
        with self.assertRaises(SystemExit) as ctx:
            apply_documents(project, True)
        self.assertIn("docs", str(ctx.exception))
        self.assertFalse((project / "CLAUDE.md").exists())
        self.assertFalse((project / "AGENTS.md").exists())
        self.assertEqual((project / "docs").read_text(encoding="utf-8"), "我是普通文件\n")


if __name__ == "__main__":
    unittest.main()
