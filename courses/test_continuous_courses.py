import json
import unittest
from pathlib import Path

from courses import build


class ContinuousCourseContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.root = Path(__file__).resolve().parent
        cls.courses = {
            spec["prefix"]: json.loads(
                (cls.root / spec["course_file"]).read_text(encoding="utf-8")
            )
            for spec in build.COURSE_SPECS
        }

    def test_logical_curriculum_is_contiguous_and_dependency_ordered(self) -> None:
        ordered = sorted(
            build.COURSE_SPECS, key=lambda spec: spec["curriculum_order"]
        )
        self.assertEqual(
            [spec["curriculum_order"] for spec in ordered],
            list(range(1, len(ordered) + 1)),
        )
        self.assertEqual(
            [spec["prefix"] for spec in ordered],
            [
                "AG", "GS", "CX", "BR", "CH", "CU",
                "FH", "FS", "FA", "MP", "PT", "DA", "PD",
                "OT", "DO", "PF", "SS", "PR", "TC", "VZ",
                "HF", "IO", "WB", "SI", "SA",
            ],
        )
        phase_bridges = dict(build.CURRICULUM_PHASES)
        self.assertEqual(set(phase_bridges.values()), {
            "B01", "B02", "B03", "B04", "B05", "B06"
        })
        for spec in ordered:
            self.assertEqual(spec["bridge_ref"], phase_bridges[spec["phase"]])

    def test_physical_release_keeps_old_order_and_only_appends(self) -> None:
        self.assertEqual(
            [spec["prefix"] for spec in build.COURSE_SPECS],
            [
                "AG", "CX", "FA", "MP", "PT", "DA", "OT", "HF", "PD",
                "SA", "DO", "PF", "SS", "PR", "TC", "VZ", "IO", "WB",
                "BR", "CH", "CU", "SI", "GS", "FS", "FH",
            ],
        )

    def test_new_course_totals_and_stable_interfaces(self) -> None:
        self.assertEqual(len(build.COURSE_SPECS), 25)
        self.assertEqual(
            sum(spec["lesson_count"] for spec in build.COURSE_SPECS), 228
        )
        self.assertEqual(
            sum(
                len(deck["questions"])
                for course in self.courses.values()
                for deck in course["decks"]
            ),
            1140,
        )
        self.assertEqual(len(self.courses["GS"]["decks"]), 24)
        self.assertEqual(len(self.courses["FS"]["decks"]), 9)
        self.assertEqual(len(self.courses["FH"]["decks"]), 13)

    def test_global_skill_snapshot_covers_user_and_system_skills(self) -> None:
        course = self.courses["GS"]
        combined = json.dumps(course, ensure_ascii=False)
        expected = {
            "academic-research-suite",
            "cataloging-agent-framework-configs",
            "chinese-openai-yaml",
            "chronicle",
            "cli-creator",
            "ec-public-customer-task",
            "fastapi1-email-marketing",
            "fastapi1-skill",
            "fastapi1-wechat-marketing",
            "fastapi1-wxcli",
            "frontend-design-ultimate",
            "graphify",
            "hightech-enterprise-certification",
            "html-a4-print",
            "memory-leak-debugging",
            "stop-slop",
            "teach",
            "imagegen",
            "openai-docs",
            "plugin-creator",
            "review-agent",
            "skill-creator",
            "skill-installer",
        }
        self.assertEqual(len(expected), len(course["decks"]) - 1)
        for name in expected:
            with self.subTest(skill=name):
                self.assertIn(f"${name}", combined)

    def test_harness_research_rows_are_covered_by_the_three_new_courses(self) -> None:
        research = (self.root / "HARNESS_RESEARCH.md").read_text(encoding="utf-8")

        def rows_between(start: str, end: str) -> list[tuple[str, str]]:
            section = research.split(start, 1)[1].split(end, 1)[0]
            rows: list[tuple[str, str]] = []
            for line in section.splitlines():
                if not line.startswith("|") or "---" in line:
                    continue
                cells = [part.strip() for part in line.strip("|").split("|")]
                if len(cells) == 3 and cells[0] not in {"skill", "component"}:
                    rows.append((cells[0], cells[1]))
            return rows

        expected = {
            "GS": rows_between("## GS：", "## FS："),
            "FS": rows_between("## FS：", "## FH："),
            "FH": rows_between("## FH：", "## MCP 与 Hooks"),
        }
        self.assertEqual(len(expected["GS"]), 23)
        self.assertEqual(len(expected["FS"]), 8)
        self.assertEqual(len(expected["FH"]), 13)
        for prefix, rows in expected.items():
            source_text = "\n".join(
                deck["source_text"] for deck in self.courses[prefix]["decks"]
            )
            for _name, relative_path in rows:
                with self.subTest(prefix=prefix, path=relative_path):
                    self.assertIn(relative_path, source_text)

    def test_fastapi_project_skills_and_harness_components_are_separate(self) -> None:
        skills = json.dumps(self.courses["FS"], ensure_ascii=False)
        harness = json.dumps(self.courses["FH"], ensure_ascii=False)
        skill_names = (
            "source-driven-development",
            "frontend-ui-engineering",
            "security-and-hardening",
            "performance-optimization",
            "harness-maintenance",
            "git-branch-pr-merge",
            "windows-vm-operator",
            "remote-server-operator",
        )
        for name in skill_names:
            with self.subTest(skill=name):
                self.assertIn(name, skills)
                self.assertIn(f"${name}", skills)
        for marker in (
            "data_security.toml",
            "docs_researcher.toml",
            "explorer.toml",
            "fastapi_api.toml",
            "reviewer.toml",
            "contract.json",
            "SessionStart",
            "environment.toml",
            "openaiDeveloperDocs",
            "postgresql",
            "redis",
            "sqlite",
            "default.rules",
        ):
            with self.subTest(component=marker):
                self.assertIn(marker, harness)

    def test_new_labs_have_the_fixed_seven_part_unit_contract(self) -> None:
        root = Path(__file__).resolve().parent
        for spec in build.COURSE_SPECS:
            if spec["prefix"] not in {"GS", "FS", "FH", "BR", "CH", "CU", "SI"}:
                continue
            lab = (root / "labs" / spec["lab_file"]).read_text(encoding="utf-8")
            for order in range(1, spec["lesson_count"] + 1):
                code = f"{spec['prefix']}{order:02d}"
                section = lab.split(f"## {code}", 1)[1]
                if order < spec["lesson_count"]:
                    section = section.split(f"## {spec['prefix']}{order + 1:02d}", 1)[0]
                headings = [
                    line.strip()
                    for line in section.splitlines()
                    if line.startswith("### ")
                ]
                self.assertEqual(
                    headings,
                    [
                        "### 1. 用途",
                        "### 2. 适用与不适用场景",
                        "### 3. 输入/输出",
                        "### 4. 最小调用模板",
                        "### 5. 边界与风险",
                        "### 6. 提示词练习",
                        "### 7. 可观察验收清单",
                    ],
                    f"{spec['prefix']}{order:02d} lab headings",
                )

    def test_plugin_hook_stays_with_ponytail_course(self) -> None:
        ponytail = json.dumps(self.courses["PT"]["decks"][0], ensure_ascii=False)
        self.assertIn("hooks/claude-codex-hooks.json", ponytail)
        self.assertIn("携带、信任、启用和实际执行", ponytail)
        self.assertNotIn("hooks/claude-codex-hooks.json", json.dumps(
            self.courses["CX"], ensure_ascii=False
        ))


if __name__ == "__main__":
    unittest.main()
