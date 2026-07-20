import json
import re
import unittest
from pathlib import Path

from courses import build


PLUGIN_PREFIXES = {
    "mattpocock-skills": "MP",
    "ponytail": "PT",
    "data-analytics": "DA",
    "openai-templates": "OT",
    "hyperframes": "HF",
    "product-design": "PD",
    "sales": "SA",
    "documents": "DO",
    "pdf": "PF",
    "spreadsheets": "SS",
    "presentations": "PR",
    "template-creator": "TC",
    "visualize": "VZ",
    "build-ios-apps": "IO",
    "build-web-apps": "WB",
    "browser": "BR",
    "chrome": "CH",
    "computer-use": "CU",
    "sites": "SI",
}

def research_rows(path: Path) -> list[dict[str, str]]:
    lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines()]
    table = [line for line in lines if line.startswith("|")]
    header_index = next(
        index
        for index, line in enumerate(table)
        if {
            "skill_slug",
            "display_name",
            "relative_path",
            "sha256",
            "license",
        }.issubset({part.strip() for part in line.split("|")})
    )
    header = [part.strip() for part in table[header_index].strip("|").split("|")]
    rows: list[dict[str, str]] = []
    for line in table[header_index + 1 :]:
        cells = [part.strip() for part in line.strip("|").split("|")]
        if not cells or all(set(cell) <= {"-", ":"} for cell in cells):
            continue
        if len(cells) == len(header):
            rows.append(dict(zip(header, cells)))
    return rows


def manifest_rows(path: Path) -> list[dict[str, str]]:
    lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines()]
    table = [line for line in lines if line.startswith("|")]
    header_index = next(
        index
        for index, line in enumerate(table)
        if "version" in [part.strip() for part in line.split("|")]
        and "skill_slug" not in line
    )
    header = [part.strip() for part in table[header_index].strip("|").split("|")]
    rows: list[dict[str, str]] = []
    for line in table[header_index + 1 :]:
        cells = [part.strip() for part in line.strip("|").split("|")]
        if len(cells) != len(header) or all(set(cell) <= {"-", ":"} for cell in cells):
            if rows and cells and "skill_slug" in cells:
                break
            continue
        rows.append(dict(zip(header, cells)))
    return rows


class PluginCourseCoverageTest(unittest.TestCase):
    def test_all_snapshot_skills_have_one_course_unit(self) -> None:
        root = Path(__file__).resolve().parent
        rows = research_rows(root / "PLUGIN_RESEARCH.md")
        manifests = {row["plugin"]: row for row in manifest_rows(root / "PLUGIN_RESEARCH.md")}
        expected_skill_count = sum(
            spec["lesson_count"] - 1
            for spec in build.COURSE_SPECS
            if spec["prefix"] in PLUGIN_PREFIXES.values()
        )
        self.assertEqual(len(rows), expected_skill_count)
        self.assertEqual(len(manifests), len(PLUGIN_PREFIXES))
        self.assertEqual(set(PLUGIN_PREFIXES), {row["plugin"] for row in rows})
        self.assertEqual(
            len({(row["plugin"], row["skill_slug"]) for row in rows}),
            expected_skill_count,
        )
        self.assertTrue(all(".openclaw" not in row["relative_path"] for row in rows))
        self.assertTrue(all("/Users/" not in row["relative_path"] for row in rows))

        courses = {
            spec["prefix"]: json.loads(
                (root / spec["course_file"]).read_text(encoding="utf-8")
            )
            for spec in build.COURSE_SPECS
            if spec["prefix"] in PLUGIN_PREFIXES.values()
        }
        by_plugin = {name: prefix for name, prefix in PLUGIN_PREFIXES.items()}
        for plugin, prefix in by_plugin.items():
            with self.subTest(plugin=plugin):
                course = courses[prefix]
                self.assertEqual(course["course"]["id"], plugin)
                self.assertEqual(course["course"]["title"], plugin)
                self.assertEqual(
                    course["source"]["ref"],
                    f"{plugin}@{manifests[plugin]['version']}",
                )
                self.assertEqual(course["source"]["kind"], "local-sanitized")
                self.assertEqual(course["source"]["snapshot"], "2026-07-20")
                skill_decks = course["decks"][1:]
                expected = [row for row in rows if row["plugin"] == plugin]
                self.assertEqual(len(skill_decks), len(expected))
                source_text = "\n".join(deck["source_text"] for deck in skill_decks)
                actual_paths = []
                for deck in skill_decks:
                    match = re.search(r"(skills/[^ ;；]+/SKILL\.md)", deck["source_text"])
                    self.assertIsNotNone(match)
                    assert match is not None
                    actual_paths.append(match.group(1))
                self.assertEqual(
                    actual_paths,
                    [row["relative_path"] for row in expected],
                )
                for row in expected:
                    self.assertIn(row["skill_slug"], source_text)
                    self.assertIn(row["display_name"], source_text + "\n" + json.dumps(course, ensure_ascii=False))

                for deck, row in zip(skill_decks, expected):
                    invocation_name = row["invocation_name"]
                    with self.subTest(deck=deck["code"], invocation=invocation_name):
                        self.assertEqual(
                            deck["title"],
                            f"{deck['code']} {row['display_name']}",
                        )
                        self.assertEqual(row["invocation_name"], invocation_name)
                        serialized = json.dumps(deck, ensure_ascii=False)
                        self.assertIn(
                            f"${plugin}:{invocation_name}",
                            serialized,
                        )
                        if invocation_name != row["skill_slug"]:
                            self.assertNotIn(
                                f"${plugin}:{row['skill_slug']}",
                                serialized,
                            )

    def test_boundary_answers_have_no_template_stop_fragment(self) -> None:
        root = Path(__file__).resolve().parent
        for prefix in PLUGIN_PREFIXES.values():
            spec = next(item for item in build.COURSE_SPECS if item["prefix"] == prefix)
            course = json.loads((root / spec["course_file"]).read_text(encoding="utf-8"))
            for deck in course["decks"]:
                for question in deck["questions"]:
                    with self.subTest(question=question["id"]):
                        self.assertNotIn("。时停止当前路由", question["content"])
                        self.assertNotIn("。时停止当前路由", question["answer"])
                        self.assertNotIn("。时停止当前路由", question["explanation"])

    def test_data_analytics_nested_report_converters_follow_build_report(self) -> None:
        rows = research_rows(Path(__file__).resolve().parent / "PLUGIN_RESEARCH.md")
        slugs = [row["skill_slug"] for row in rows if row["plugin"] == "data-analytics"]
        start = slugs.index("build-report")
        self.assertEqual(
            slugs[start : start + 4],
            [
                "build-report",
                "report-to-google-doc",
                "report-to-google-slides",
                "report-to-pdf",
            ],
        )

    def test_synthetic_fixture_and_read_only_contract_are_explicit(self) -> None:
        root = Path(__file__).resolve().parent
        fixture_labs = (
            "product-design.md",
            "sales.md",
            "documents.md",
            "pdf.md",
            "spreadsheets.md",
        )
        read_only_clause = (
            "本手册中的“输出/成品/链接”均指提示词中应列出的预期结构与验收证据，"
            "不实际创建、上传、部署、发送或改变外部状态。"
        )
        for filename in fixture_labs:
            with self.subTest(lab=filename):
                text = (root / "labs" / filename).read_text(encoding="utf-8")
                self.assertIn("<synthetic-fixture>", text)
                self.assertIn("占位符", text)
                self.assertIn(read_only_clause, text)

        expected_phrases = {
            "product-design.json": ("PD06", "实现方案、浏览器验证证据字段"),
            "documents.json": ("DO02", "结构检查和逐页视觉 QA 的执行方案"),
            "pdf.json": ("PF02", "文本/结构检查、逐页 PNG 渲染和视觉验收方案"),
            "spreadsheets.json": ("SS02", "连接门槛、只读检查计划、预期变更 diff"),
        }
        for filename, (code, phrase) in expected_phrases.items():
            course = json.loads((root / filename).read_text(encoding="utf-8"))
            deck = next(deck for deck in course["decks"] if deck["code"] == code)
            with self.subTest(deck=code):
                self.assertIn(phrase, json.dumps(deck, ensure_ascii=False))

    def test_sales_connector_units_only_practice_write_previews(self) -> None:
        root = Path(__file__).resolve().parent
        course = json.loads(
            (root / "sales.json").read_text(encoding="utf-8")
        )
        labs = (root / "labs" / "sales.md").read_text(encoding="utf-8")
        decks = {
            deck["code"]: json.dumps(deck, ensure_ascii=False)
            for deck in course["decks"]
            if deck["code"] in {"SA12", "SA20"}
        }
        self.assertEqual(set(decks), {"SA12", "SA20"})
        for code, text in decks.items():
            with self.subTest(deck=code):
                self.assertIn("变更 diff", text)
                self.assertIn("验证计划", text)
                self.assertIn("不执行写入", text)
                self.assertNotIn("安全处理已批准的记录变更", text)
                self.assertNotIn("执行已批准且可验证的支持写入", text)
        for marker in ("## SA12", "## SA20"):
            section = labs.split(marker, 1)[1]
            if marker == "## SA12":
                section = section.split("## SA13", 1)[0]
            else:
                section = section.split("## SA21", 1)[0]
            with self.subTest(lab=marker):
                self.assertIn("不执行写入", section)
                self.assertIn("变更 diff", section)
                self.assertIn("验证计划", section)
                self.assertNotIn("安全处理已批准的记录变更", section)
                self.assertNotIn("执行已批准且可验证的支持写入", section)


if __name__ == "__main__":
    unittest.main()
