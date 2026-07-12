import hashlib
import json
import re
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from contextlib import closing, redirect_stderr
from io import StringIO
from pathlib import Path
from unittest import mock

from courses import build


def sample_course() -> dict:
    return {
        "course": {
            "id": "sample",
            "prefix": "TS",
            "title": "测试课程",
        },
        "source": {
            "kind": "test",
            "ref": "fixture",
            "snapshot": "2026-07-11",
        },
        "decks": [
            {
                "id": "course-ts-01",
                "code": "TS01",
                "title": "TS01 测试",
                "order": 1,
                "lab_ref": "TS01",
                "source_text": "测试来源",
                "questions": [
                    {
                        "id": "course-ts-01-q01",
                        "type": "multiple_choice",
                        "content": "[Test] 哪个选项用于验证数据库生成？",
                        "options": ["运行检查", "跳过检查", "删除源码", "写入密钥"],
                        "answer": "运行检查",
                        "explanation": (
                            "结论：应运行检查。\n"
                            "依据：生成物必须能够从结构化来源重复验证。\n"
                            "错误选项：B：跳过检查会失去验证证据；"
                            "C：删除源码具有破坏性；D：写入密钥会泄露凭证。\n"
                            "实践：构建后重新打开数据库并执行完整性与外键检查。"
                        ),
                    }
                ],
            }
        ],
    }


def supported_questions() -> list[dict]:
    explanation = (
        "结论：答案符合题型契约。\n"
        "依据：结构化字段足以表达并校验答案。\n"
        "实践：写入数据库后重新读取并核对 JSON。"
    )
    return [
        sample_course()["decks"][0]["questions"][0],
        {
            "id": "course-ts-01-q02",
            "type": "fill_blank",
            "content": "[Test] SQLite 的 schema 版本由 ___ 标记。",
            "options": [],
            "answer": "user_version",
            "explanation": explanation,
        },
        {
            "id": "course-ts-01-q03",
            "type": "true_false",
            "content": "[Test] options 应保存为 JSON 文本。",
            "options": ["正确", "错误"],
            "answer": "正确",
            "explanation": explanation,
        },
        {
            "id": "course-ts-01-q04",
            "type": "matching",
            "content": "[Test] 将字段与用途匹配。",
            "options": [],
            "answer": "options-选项|answer-答案",
            "explanation": explanation,
            "match_left": ["options", "answer"],
            "match_right": ["答案", "选项"],
        },
        {
            "id": "course-ts-01-q05",
            "type": "ordering",
            "content": "[Test] 按构建顺序排列。",
            "options": ["复测", "写测试", "实现"],
            "answer": "写测试|实现|复测",
            "explanation": explanation,
        },
    ]


def course_with_question(question: dict) -> dict:
    course = sample_course()
    question = json.loads(json.dumps(question, ensure_ascii=False))
    question["id"] = "course-ts-01-q01"
    course["decks"][0]["questions"] = [question]
    return course


def supported_course() -> dict:
    course = sample_course()
    course["decks"][0]["questions"] = supported_questions()
    return course


def course_for_prefix(prefix: str) -> dict:
    course = sample_course()
    code = f"{prefix}01"
    deck_id = f"course-{prefix.lower()}-01"
    course["course"]["id"] = f"{prefix.lower()}-course"
    course["course"]["prefix"] = prefix
    deck = course["decks"][0]
    deck["id"] = deck_id
    deck["code"] = code
    deck["title"] = f"{code} 测试"
    deck["lab_ref"] = code
    deck["questions"][0]["id"] = f"{deck_id}-q01"
    return course


def multiple_choice_course(answer_positions: list[int]) -> dict:
    course = sample_course()
    questions = []
    for number, answer_position in enumerate(answer_positions, start=1):
        options = [f"题{number}选项{letter}" for letter in "ABCD"]
        answer_letter = "ABCD"[answer_position]
        wrong_letters = [letter for letter in "ABCD" if letter != answer_letter]
        questions.append(
            {
                "id": f"course-ts-01-q{number:02d}",
                "type": "multiple_choice",
                "content": f"[Test] 第 {number} 题的正确选项是什么？",
                "options": options,
                "answer": options[answer_position],
                "explanation": (
                    "结论：选择指定答案。\n"
                    "依据：夹具显式指定正确位置。\n"
                    "错误选项："
                    + "；".join(f"{letter}：不是指定位置" for letter in wrong_letters)
                    + "。\n实践：统计各正确位置出现次数。"
                ),
            }
        )
    course["decks"][0]["questions"] = questions
    return course


SAMPLE_SPEC = {
    "course_file": "sample.json",
    "prefix": "TS",
    "lab_file": "sample.md",
    "lesson_count": 1,
    "ref": "fixture",
    "snapshot": "2026-07-11",
}

ORIGINAL_RELEASE_HASHES = {
    "agent-harness.json": "9ec2ff2141a0feed30054e3246132920670313c0eee41f5b01c3b13a996ad930",
    "codex-harness.json": "b44ce451d4065d63ef14e94ab476036a869c9fee8bd74aaa3352c2600c4a2965",
    "fastapi1-project.json": "0adccbfb4703a8aa6677c31f4a22d6e95b5a227592c00ec333c3d0c3ba0e9277",
    "labs/agent.md": "03bdd506b79c0b3aa72983b56bfb44d927e4f95d91212372c44c90c582945937",
    "labs/codex.md": "15f15ae0d02059ab554cad80b781030f09142c61310370a2be8ee7a563ca5236",
    "labs/fastapi1.md": "285bf96b68079a49b4fcbf7920d2b40ca74e9c71680fd8eb40f437f4693ef2ba",
}


class CourseValidationTest(unittest.TestCase):
    def test_course_specs_are_the_single_ordered_release_source(self) -> None:
        self.assertIsInstance(build.COURSE_SPECS, tuple)
        self.assertEqual(
            build.COURSE_FILES,
            tuple(spec["course_file"] for spec in build.COURSE_SPECS),
        )
        self.assertEqual(
            build.LAB_FILES,
            {spec["prefix"]: spec["lab_file"] for spec in build.COURSE_SPECS},
        )
        self.assertEqual(
            build.EXPECTED_DECKS,
            {spec["prefix"]: spec["lesson_count"] for spec in build.COURSE_SPECS},
        )
        self.assertEqual(
            build.EXPECTED_SOURCES,
            {spec["prefix"]: spec["ref"] for spec in build.COURSE_SPECS},
        )

    def test_release_accepts_dynamic_positive_lesson_count_and_five_questions(self) -> None:
        with mock.patch.object(build, "COURSE_SPECS", (SAMPLE_SPEC,), create=True):
            build.validate_release(
                [supported_course()],
                {"TS": "## TS01 测试"},
            )

    def test_release_rejects_non_positive_lesson_count(self) -> None:
        invalid_spec = {**SAMPLE_SPEC, "lesson_count": 0}

        with (
            mock.patch.object(build, "COURSE_SPECS", (invalid_spec,), create=True),
            self.assertRaisesRegex(build.ValidationError, "positive"),
        ):
            build.validate_release(
                [supported_course()],
                {"TS": "## TS01 测试"},
            )

    def test_release_rejects_malformed_course_spec_with_validation_error(self) -> None:
        invalid_spec = {**SAMPLE_SPEC, "prefix": 1}

        with (
            mock.patch.object(build, "COURSE_SPECS", (invalid_spec,)),
            self.assertRaisesRegex(build.ValidationError, "prefix"),
        ):
            build.validate_release(
                [supported_course()],
                {"TS": "## TS01 测试"},
            )

    def test_release_rejects_unbalanced_multiple_choice_answer_positions(self) -> None:
        with (
            mock.patch.object(build, "COURSE_SPECS", (SAMPLE_SPEC,)),
            self.assertRaisesRegex(build.ValidationError, "differ by at most one"),
        ):
            build.validate_release(
                [multiple_choice_course([0, 0, 0, 0, 0])],
                {"TS": "## TS01 测试"},
            )

    def test_release_rejects_malformed_course_shapes_with_validation_error(self) -> None:
        valid = supported_course()
        malformed = (
            [],
            {**valid, "course": []},
            {**valid, "source": []},
            {**valid, "decks": {}},
        )

        with mock.patch.object(build, "COURSE_SPECS", (SAMPLE_SPEC,)):
            for course in malformed:
                with self.subTest(course=course):
                    with self.assertRaises(build.ValidationError):
                        build.validate_release(
                            [course],
                            {"TS": "## TS01 测试"},
                        )

    def test_main_reports_malformed_release_without_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            stderr = StringIO()
            with (
                mock.patch.object(build, "COURSE_SPECS", (SAMPLE_SPEC,)),
                mock.patch.object(build, "load_release", return_value=([[]], {})),
                redirect_stderr(stderr),
            ):
                result = build.main(
                    ["--check", "--output", str(Path(temp_dir) / "dlg_q.db")]
                )

        self.assertEqual(result, 1)
        self.assertIn("course build failed:", stderr.getvalue())

    def test_load_release_rejects_duplicate_keys_at_any_object_depth(self) -> None:
        duplicate_sources = (
            '{"course": {}, "course": {}}',
            '{"course": {"id": "first", "id": "second"}}',
            '{"decks": [{"id": "first", "id": "second"}]}',
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            course_dir = Path(temp_dir)
            path = course_dir / SAMPLE_SPEC["course_file"]
            (course_dir / "labs").mkdir()
            (course_dir / "labs" / SAMPLE_SPEC["lab_file"]).write_text(
                "## TS01 测试", encoding="utf-8"
            )
            for raw in duplicate_sources:
                path.write_text(raw, encoding="utf-8")
                with self.subTest(raw=raw), mock.patch.object(
                    build, "COURSE_SPECS", (SAMPLE_SPEC,)
                ):
                    with self.assertRaisesRegex(
                        build.ValidationError, "duplicate JSON key"
                    ):
                        build.load_release(course_dir)

    def test_main_reports_duplicate_json_key_without_traceback(self) -> None:
        raw = json.dumps(supported_course(), ensure_ascii=False)
        raw = raw.replace(
            '"answer": "运行检查"',
            '"answer": "运行检查", "answer": "运行检查"',
            1,
        )
        load_release = build.load_release

        with tempfile.TemporaryDirectory() as temp_dir:
            course_dir = Path(temp_dir)
            (course_dir / "labs").mkdir()
            (course_dir / SAMPLE_SPEC["course_file"]).write_text(raw, encoding="utf-8")
            (course_dir / "labs" / SAMPLE_SPEC["lab_file"]).write_text(
                "## TS01 测试", encoding="utf-8"
            )
            stderr = StringIO()
            with (
                mock.patch.object(build, "COURSE_SPECS", (SAMPLE_SPEC,)),
                mock.patch.object(
                    build,
                    "load_release",
                    side_effect=lambda _course_dir: load_release(course_dir),
                ),
                redirect_stderr(stderr),
            ):
                result = build.main(
                    ["--check", "--output", str(course_dir / "missing.db")]
                )

        self.assertEqual(result, 1)
        self.assertIn("duplicate JSON key 'answer'", stderr.getvalue())
        self.assertNotIn("Traceback", stderr.getvalue())

    def test_rejects_non_text_question_type_with_validation_error(self) -> None:
        for invalid_type in ([], {}):
            course = sample_course()
            course["decks"][0]["questions"][0]["type"] = invalid_type
            with self.subTest(question_type=invalid_type):
                with self.assertRaisesRegex(build.ValidationError, "type must be text"):
                    build.validate_course(course, "## TS01 测试")

    def test_question_content_requires_complete_non_nested_tag_and_stem(self) -> None:
        invalid_contents = (
            "[] 题干",
            "[ ] 题干",
            "[AG 未闭合题干",
            "[[CX]] 嵌套标签题干",
            "[FA]   ",
        )

        for content in invalid_contents:
            course = sample_course()
            course["decks"][0]["questions"][0]["content"] = content
            with self.subTest(content=content):
                with self.assertRaisesRegex(
                    build.ValidationError, "course tag.*question"
                ):
                    build.validate_course(course, "## TS01 测试")

    def test_main_reports_non_text_question_type_without_traceback(self) -> None:
        course = supported_course()
        course["decks"][0]["questions"][0]["type"] = []
        with tempfile.TemporaryDirectory() as temp_dir:
            stderr = StringIO()
            with (
                mock.patch.object(build, "COURSE_SPECS", (SAMPLE_SPEC,)),
                mock.patch.object(
                    build,
                    "load_release",
                    return_value=([course], {"TS": "## TS01 测试"}),
                ),
                redirect_stderr(stderr),
            ):
                result = build.main(
                    ["--check", "--output", str(Path(temp_dir) / "dlg_q.db")]
                )

        self.assertEqual(result, 1)
        self.assertIn("type must be text", stderr.getvalue())

    def test_deck_order_must_be_a_non_boolean_integer(self) -> None:
        for invalid_order in (True, 1.0, "1"):
            course = sample_course()
            course["decks"][0]["order"] = invalid_order
            with self.subTest(order=invalid_order):
                with self.assertRaisesRegex(build.ValidationError, "order.*integer"):
                    build.validate_course(course, "## TS01 测试")

    def test_deck_fields_must_match_contract_exactly(self) -> None:
        mutations = (
            ("unexpected", lambda deck: deck.__setitem__("unexpected", True)),
            ("created_at", lambda deck: deck.__setitem__("created_at", 0)),
            ("missing", lambda deck: deck.pop("source_text")),
        )

        for case, mutate in mutations:
            course = sample_course()
            mutate(course["decks"][0])
            with self.subTest(case=case):
                with self.assertRaisesRegex(build.ValidationError, "deck .*fields must be"):
                    build.validate_course(course, "## TS01 测试")

    def test_accepts_all_supported_question_contracts(self) -> None:
        for question in supported_questions():
            with self.subTest(question_type=question["type"]):
                build.validate_course(
                    course_with_question(question),
                    "## TS01 测试",
                    expected_questions_per_deck=1,
                )

    def test_rejects_invalid_fill_blank_and_true_false_contracts(self) -> None:
        fill_blank = supported_questions()[1]
        true_false = supported_questions()[2]
        invalid = []
        invalid_fill_options = {**fill_blank, "options": ["user_version"]}
        invalid.append((invalid_fill_options, "fill_blank options"))
        invalid_fill_content = {**fill_blank, "content": "[Test] ___ 与 ___"}
        invalid.append((invalid_fill_content, "exactly one ___"))
        invalid_true_false = {**true_false, "options": ["错误", "正确"]}
        invalid.append((invalid_true_false, "true_false options"))
        invalid_true_answer = {**true_false, "answer": "不知道"}
        invalid.append((invalid_true_answer, "true_false answer"))

        for question, message in invalid:
            with self.subTest(message=message):
                with self.assertRaisesRegex(build.ValidationError, message):
                    build.validate_course(
                        course_with_question(question),
                        "## TS01 测试",
                        expected_questions_per_deck=1,
                    )

    def test_rejects_invalid_matching_contracts(self) -> None:
        matching = supported_questions()[3]
        invalid = []
        invalid.append(
            ({**matching, "match_right": ["选项"]}, "equal non-empty")
        )
        invalid.append(
            ({**matching, "match_left": ["options", "options"]}, "unique")
        )
        invalid.append(
            (
                {**matching, "answer": "answer-答案|options-选项"},
                "match_left order",
            )
        )
        invalid.append(
            (
                {**matching, "answer": "options-选项|answer-选项"},
                "cover match_right",
            )
        )

        for question, message in invalid:
            with self.subTest(message=message):
                with self.assertRaisesRegex(build.ValidationError, message):
                    build.validate_course(
                        course_with_question(question),
                        "## TS01 测试",
                        expected_questions_per_deck=1,
                    )

    def test_rejects_ambiguous_matching_answer(self) -> None:
        matching = supported_questions()[3]
        matching["match_left"] = ["a", "a-b"]
        matching["match_right"] = ["b-c", "c"]
        matching["answer"] = "a-b-c|a-b-c"

        with self.assertRaisesRegex(build.ValidationError, "unambiguous"):
            build.validate_course(
                course_with_question(matching),
                "## TS01 测试",
                expected_questions_per_deck=1,
            )

    def test_rejects_invalid_ordering_contracts(self) -> None:
        ordering = supported_questions()[4]
        invalid = (
            ({**ordering, "answer": "写测试|实现"}, "complete permutation"),
            (
                {**ordering, "options": ["写测试", "实现", "复测"]},
                "initial order",
            ),
        )

        for question, message in invalid:
            with self.subTest(message=message):
                with self.assertRaisesRegex(build.ValidationError, message):
                    build.validate_course(
                        course_with_question(question),
                        "## TS01 测试",
                        expected_questions_per_deck=1,
                    )

    def test_every_question_type_requires_conclusion_basis_and_practice(self) -> None:
        for question in supported_questions():
            invalid = {**question, "explanation": "结论：有。\n依据：有。"}
            with self.subTest(question_type=question["type"]):
                with self.assertRaisesRegex(build.ValidationError, "结论、依据、实践"):
                    build.validate_course(
                        course_with_question(invalid),
                        "## TS01 测试",
                        expected_questions_per_deck=1,
                    )

    def test_explanation_sections_are_ordered_unique_and_non_empty(self) -> None:
        multiple_choice = supported_questions()[0]
        fill_blank = supported_questions()[1]
        invalid = (
            (
                {
                    **multiple_choice,
                    "explanation": (
                        "依据：先出现。\n"
                        "结论：后出现。\n"
                        "错误选项：B：错；C：错；D：错。\n"
                        "实践：执行。"
                    ),
                },
                "ordered",
            ),
            (
                {
                    **fill_blank,
                    "explanation": (
                        "结论：第一段。\n结论：重复段。\n"
                        "依据：证据。\n实践：执行。"
                    ),
                },
                "exactly once",
            ),
            (
                {
                    **fill_blank,
                    "explanation": "结论：   \n依据：证据。\n实践：执行。",
                },
                "non-empty",
            ),
        )

        for question, message in invalid:
            with self.subTest(message=message):
                with self.assertRaisesRegex(build.ValidationError, message):
                    build.validate_course(
                        course_with_question(question),
                        "## TS01 测试",
                        expected_questions_per_deck=1,
                    )

    def test_wrong_option_section_is_exclusive_to_multiple_choice(self) -> None:
        fill_blank = supported_questions()[1]
        fill_blank["explanation"] = (
            "结论：答案。\n依据：证据。\n错误选项：不适用。\n实践：执行。"
        )

        with self.assertRaisesRegex(build.ValidationError, "must not contain"):
            build.validate_course(
                course_with_question(fill_blank),
                "## TS01 测试",
                expected_questions_per_deck=1,
            )

    def test_multiple_choice_has_exactly_one_wrong_option_section(self) -> None:
        question = supported_questions()[0]
        question["explanation"] = (
            "结论：答案。\n依据：证据。\n"
            "错误选项：B：错；C：错；D：错。\n"
            "错误选项：B：错；C：错；D：错。\n实践：执行。"
        )

        with self.assertRaisesRegex(build.ValidationError, "exactly once"):
            build.validate_course(
                course_with_question(question),
                "## TS01 测试",
                expected_questions_per_deck=1,
            )

    def test_rejects_whitespace_ambiguous_list_items(self) -> None:
        multiple_choice = supported_questions()[0]
        multiple_choice["options"][1] = " 运行检查 "
        matching = supported_questions()[3]
        matching["match_left"] = ["options", " options "]
        matching["answer"] = "options-选项| options -答案"

        for question in (multiple_choice, matching):
            with self.subTest(question_type=question["type"]):
                with self.assertRaisesRegex(
                    build.ValidationError, "surrounding whitespace"
                ):
                    build.validate_course(
                        course_with_question(question),
                        "## TS01 测试",
                        expected_questions_per_deck=1,
                    )

    def test_rejects_answer_outside_options(self) -> None:
        course = sample_course()
        course["decks"][0]["questions"][0]["answer"] = "不存在"

        with self.assertRaisesRegex(build.ValidationError, "answer"):
            build.validate_course(course, "## TS01 测试")

    def test_requires_explanations_for_each_wrong_option(self) -> None:
        course = sample_course()
        course["decks"][0]["questions"][0]["explanation"] = (
            "结论：应运行检查。\n"
            "依据：生成物必须能够从结构化来源重复验证。\n"
            "实践：构建后重新打开数据库并执行完整性与外键检查。"
        )

        with self.assertRaisesRegex(build.ValidationError, "wrong option"):
            build.validate_course(course, "## TS01 测试")

    def test_wrong_option_explanations_must_have_non_empty_bodies(self) -> None:
        course = sample_course()
        course["decks"][0]["questions"][0]["explanation"] = (
            "结论：应运行检查。\n"
            "依据：生成物必须能够从结构化来源重复验证。\n"
            "错误选项：B：   ；C：\t；D：  \n"
            "实践：构建后重新打开数据库并执行完整性与外键检查。"
        )

        with self.assertRaisesRegex(build.ValidationError, "wrong option.*non-empty"):
            build.validate_course(course, "## TS01 测试")

    def test_rejects_realistic_secret_and_absolute_home_path(self) -> None:
        for leaked in (
            "".join(("s", "k-", "1234567890abcdefghijklmnop")),
            "".join(("Bear", "er abcdefghijklmnopqrstuvwxyz123456")),
            "".join(("postgresql://user:", "password@example.com/db")),
            "/Users/jql/.codex/config.toml",
        ):
            with self.subTest(leaked=leaked):
                with self.assertRaises(build.ValidationError):
                    build.scan_sensitive(leaked, "fixture")

    def test_rejects_nul_in_course_text(self) -> None:
        course = sample_course()
        course["decks"][0]["questions"][0]["content"] += "\x00hidden"

        with self.assertRaisesRegex(build.ValidationError, "NUL"):
            build.validate_course(course, "## TS01 测试")

    def test_rejects_nul_in_extra_deck_field_name(self) -> None:
        course = sample_course()
        course["decks"][0]["extra\x00field"] = "value"

        with self.assertRaisesRegex(build.ValidationError, "NUL"):
            build.validate_course(course, "## TS01 测试")

    def test_requires_matching_lab_heading(self) -> None:
        with self.assertRaisesRegex(build.ValidationError, "TS01"):
            build.validate_course(sample_course(), "## TS02 其他实验")

    def test_allows_reused_option_text_across_questions(self) -> None:
        course = sample_course()
        duplicate = json.loads(json.dumps(course["decks"][0]["questions"][0]))
        duplicate["id"] = "course-ts-01-q02"
        duplicate["content"] = "[Test] 哪个选项文本可以跨题复用？"
        course["decks"][0]["questions"].append(duplicate)

        build.validate_course(course, "## TS01 测试")

    def test_codex_course_avoids_unsupported_strict_features_command(self) -> None:
        root = Path(__file__).resolve().parent
        combined = "\n".join(
            (
                (root / "codex-harness.json").read_text(encoding="utf-8"),
                (root / "labs" / "codex.md").read_text(encoding="utf-8"),
            )
        )

        self.assertNotIn("codex --strict-config features", combined)


class FastAPI1CourseContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        root = Path(__file__).resolve().parent
        cls.course = json.loads(
            (root / "fastapi1-project.json").read_text(encoding="utf-8")
        )
        cls.lab = (root / "labs" / "fastapi1.md").read_text(encoding="utf-8")

    def test_exercise_branches_are_pinned_to_snapshot(self) -> None:
        switches = re.findall(
            r"^git switch -c (course/\S+)(?: (\S+))?$", self.lab, re.MULTILINE
        )

        self.assertEqual(len(switches), 12)
        self.assertTrue(all(base == "b21b6e4" for _branch, base in switches))

    def test_every_question_exposes_the_fixed_source_in_app(self) -> None:
        for deck in self.course["decks"]:
            for question in deck["questions"]:
                with self.subTest(question=question["id"]):
                    self.assertTrue(
                        question["content"].startswith("[FastAPI1@b21b6e4]"),
                        question["content"],
                    )

    def test_zsh_path_is_not_used_as_a_loop_variable(self) -> None:
        self.assertNotIn("for path in", self.lab)
        self.assertIn("for file in", self.lab)

    def test_safe_python_avoids_zsh_readonly_status(self) -> None:
        helper = self.lab.split("safe_python() {", 1)[1].split("\n}", 1)[0]

        self.assertNotRegex(helper, r"\blocal\b[^\n]*\bstatus\b")
        self.assertIn("exit_code=$?", helper)

    def test_fa01_commands_prove_each_unfinished_channel(self) -> None:
        expected_commands = (
            "Marketing_Management.html | rg -n '营销后端尚未实现'",
            "Sms_Marketing_Clean.html | rg -n '功能暂未接入后端'",
            "Telemarketing_Marketing_Clean.html | rg -n '功能暂未接入后端'",
        )

        for command in expected_commands:
            with self.subTest(command=command):
                self.assertIn(command, self.lab)

    def test_safe_python_denies_all_network_without_dependencies(self) -> None:
        self.assertIn("macOS 系统沙箱", self.lab)
        self.assertNotIn("Python 标准库拒绝", self.lab)
        match = re.search(
            r"sandbox_profile='(.*?)'\n  \(",
            self.lab,
            re.DOTALL,
        )
        self.assertIsNotNone(match)
        sandbox_profile = match.group(1)
        self.assertNotIn("(allow network*", sandbox_profile)
        self.assertNotIn("(allow network-", sandbox_profile)
        self.assertIn("(deny network*)", sandbox_profile)
        self.assertIn(
            '/usr/bin/sandbox-exec -p "$sandbox_profile"', self.lab
        )

        completed = subprocess.run(
            [
                "/usr/bin/sandbox-exec",
                "-p",
                sandbox_profile,
                sys.executable,
                "-c",
                (
                    "import socket\n"
                    "server = socket.socket()\n"
                    "try:\n"
                    "    server.bind(('127.0.0.1', 0))\n"
                    "except OSError:\n"
                    "    pass\n"
                    "else:\n"
                    "    raise AssertionError('loopback bind was not blocked')\n"
                    "finally:\n"
                    "    server.close()\n"
                    "external = socket.socket()\n"
                    "assert external.connect_ex(('192.0.2.1', 9)) != 0\n"
                    "external.close()\n"
                    "try:\n"
                    "    socket.getaddrinfo('example.com', 443)\n"
                    "except OSError:\n"
                    "    pass\n"
                    "else:\n"
                    "    raise AssertionError('external DNS was not blocked')\n"
                ),
            ],
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)

    def test_safe_python_runs_from_tracked_ephemeral_snapshot(self) -> None:
        helper_and_pytest = self.lab.split("safe_python() {", 1)[1].split(
            "## FA01", 1
        )[0]

        for marker in (
            "ls-files -z",
            "tracked_snapshot",
            "PYTHONDONTWRITEBYTECODE=1",
            "-p no:cacheprovider",
            'rm -rf "$test_root"',
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, helper_and_pytest)
        self.assertNotIn('"$PWD/.venv/bin/python"', helper_and_pytest)

    def test_fa10_dependency_evidence_matches_question(self) -> None:
        deck = next(deck for deck in self.course["decks"] if deck["code"] == "FA10")
        section = self.lab.split("## FA10", 1)[1].split("## FA11", 1)[0]
        expected_paths = (
            "requirements-tools.txt",
            "client/fastapi1_cli/install-local.sh",
            "client/fastapi1_cli/install-local.ps1",
            "client/wxcli/install-windows.ps1",
        )

        for path in expected_paths:
            with self.subTest(path=path):
                self.assertIn(path, deck["source_text"])
                self.assertIn(f"git show b21b6e4:{path}", section)

    def test_fa10_exercise_has_verifiable_artifacts(self) -> None:
        section = self.lab.split("## FA10", 1)[1].split("## FA11", 1)[0]

        self.assertIn("README.md", section)
        self.assertIn("tests/test_documentation_governance.py", section)
        self.assertIn(
            "safe_pytest -q tests/test_documentation_governance.py", section
        )

    def test_fa12_reads_graph_evidence_for_connectivity_claim(self) -> None:
        section = self.lab.split("## FA12", 1)[1]

        self.assertIn(
            "git show b21b6e4:graphify-out/GRAPH_REPORT.md", section
        )
        self.assertIn("God Nodes|most connected", section)


class DatabaseBuildTest(unittest.TestCase):
    def test_rejects_missing_existing_decks_and_preserves_output(self) -> None:
        original_courses = [course_for_prefix("AA"), course_for_prefix("BB")]
        variants = (
            ("trailing removal", [course_for_prefix("AA")]),
            (
                "trailing replacement",
                [course_for_prefix("AA"), course_for_prefix("CC")],
            ),
        )

        for label, changed_courses in variants:
            with self.subTest(change=label), tempfile.TemporaryDirectory() as temp_dir:
                output = Path(temp_dir) / "dlg_q.db"
                build.build_database(original_courses, output)
                original = output.read_bytes()

                with self.assertRaisesRegex(build.ValidationError, "existing deck"):
                    build.build_database(changed_courses, output)

                self.assertEqual(output.read_bytes(), original)

    def test_rejects_existing_deck_created_at_drift_and_preserves_output(self) -> None:
        variants = (
            (
                "reorder",
                [course_for_prefix("AA"), course_for_prefix("BB")],
                [course_for_prefix("BB"), course_for_prefix("AA")],
            ),
            (
                "middle insertion",
                [course_for_prefix("AA"), course_for_prefix("BB")],
                [
                    course_for_prefix("AA"),
                    course_for_prefix("CC"),
                    course_for_prefix("BB"),
                ],
            ),
        )

        for label, original_courses, changed_courses in variants:
            with self.subTest(change=label), tempfile.TemporaryDirectory() as temp_dir:
                output = Path(temp_dir) / "dlg_q.db"
                build.build_database(original_courses, output)
                original = output.read_bytes()

                with self.assertRaisesRegex(build.ValidationError, "created_at"):
                    build.build_database(changed_courses, output)

                self.assertEqual(output.read_bytes(), original)

    def test_appending_course_preserves_existing_deck_created_at(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "dlg_q.db"
            original_courses = [course_for_prefix("AA"), course_for_prefix("BB")]
            build.build_database(original_courses, output)
            with closing(sqlite3.connect(output)) as connection:
                original_timestamps = dict(
                    connection.execute("SELECT id, created_at FROM decks")
                )

            build.build_database(
                original_courses + [course_for_prefix("CC")],
                output,
            )
            with closing(sqlite3.connect(output)) as connection:
                appended_timestamps = dict(
                    connection.execute("SELECT id, created_at FROM decks")
                )

            for deck_id, created_at in original_timestamps.items():
                self.assertEqual(appended_timestamps[deck_id], created_at)
            self.assertIn("course-cc-01", appended_timestamps)

    def test_rebuilds_non_sqlite_and_damaged_schema_outputs(self) -> None:
        for damage in ("non-sqlite", "damaged-schema", "damaged-created-at"):
            with self.subTest(damage=damage), tempfile.TemporaryDirectory() as temp_dir:
                output = Path(temp_dir) / "dlg_q.db"
                if damage == "non-sqlite":
                    output.write_bytes(b"not a sqlite database")
                elif damage == "damaged-schema":
                    with closing(sqlite3.connect(output)) as connection, connection:
                        connection.execute("PRAGMA user_version = 1")
                        connection.execute("CREATE TABLE broken (id TEXT)")

                course = course_for_prefix("AA")
                if damage == "damaged-created-at":
                    build.build_database([course], output)
                    with closing(sqlite3.connect(output)) as connection, connection:
                        connection.execute(
                            "UPDATE decks SET created_at = 'invalid'"
                        )
                build.build_database([course], output)

                self.assertEqual(
                    build.check_database(
                        output,
                        expected_decks=1,
                        expected_questions=1,
                        expected_courses=[course],
                    ),
                    {"decks": 1, "questions": 1},
                )

    def test_builds_all_question_types_with_json_text_list_columns(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "dlg_q.db"
            course = supported_course()
            build.validate_course(
                course,
                "## TS01 测试",
                expected_questions_per_deck=5,
            )
            build.build_database([course], output)

            with closing(sqlite3.connect(output)) as connection:
                rows = connection.execute(
                    "SELECT id, options, match_left, match_right "
                    "FROM questions ORDER BY id"
                ).fetchall()

            by_id = {question["id"]: question for question in supported_questions()}
            for question_id, options, match_left, match_right in rows:
                with self.subTest(question=question_id):
                    self.assertIsInstance(options, str)
                    self.assertIsInstance(match_left, str)
                    self.assertIsInstance(match_right, str)
                    self.assertEqual(json.loads(options), by_id[question_id]["options"])
                    self.assertEqual(
                        json.loads(match_left), by_id[question_id].get("match_left", [])
                    )
                    self.assertEqual(
                        json.loads(match_right), by_id[question_id].get("match_right", [])
                    )

            self.assertEqual(
                build.check_database(output, expected_courses=[course]),
                {"decks": 1, "questions": 5},
            )

    def test_database_check_rejects_non_json_matching_column(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "dlg_q.db"
            course = supported_course()
            build.build_database([course], output)
            with closing(sqlite3.connect(output)) as connection, connection:
                connection.execute(
                    "UPDATE questions SET match_left = ? WHERE type = 'matching'",
                    ("options|answer",),
                )

            with self.assertRaisesRegex(build.ValidationError, "match_left.*JSON"):
                build.check_database(
                    output,
                    expected_decks=1,
                    expected_questions=5,
                )

    def test_original_release_content_hashes_and_counts_remain_fixed(self) -> None:
        root = Path(__file__).resolve().parent
        for relative_path, expected_hash in ORIGINAL_RELEASE_HASHES.items():
            with self.subTest(path=relative_path):
                actual_hash = hashlib.sha256(
                    (root / relative_path).read_bytes()
                ).hexdigest()
                self.assertEqual(actual_hash, expected_hash)

        courses = [
            json.loads((root / filename).read_text(encoding="utf-8"))
            for filename in (
                "agent-harness.json",
                "codex-harness.json",
                "fastapi1-project.json",
            )
        ]

        self.assertEqual(sum(len(course["decks"]) for course in courses), 36)
        self.assertEqual(
            sum(
                len(deck["questions"])
                for course in courses
                for deck in course["decks"]
            ),
            180,
        )

    def test_release_totals_follow_course_specs(self) -> None:
        root = Path(__file__).resolve().parent
        courses, labs = build.load_release(root)

        build.validate_release(courses, labs)

        expected_decks = sum(spec["lesson_count"] for spec in build.COURSE_SPECS)
        self.assertEqual(sum(len(course["decks"]) for course in courses), expected_decks)
        self.assertEqual(
            sum(
                len(deck["questions"])
                for course in courses
                for deck in course["decks"]
            ),
            expected_decks * build.QUESTIONS_PER_DECK,
        )

    def test_builds_schema_v1_with_json_options_and_99_hearts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "dlg_q.db"
            course = sample_course()
            build.validate_course(course, "## TS01 测试")
            build.build_database([course], output)

            with closing(sqlite3.connect(output)) as connection, connection:
                tables = {
                    row[0]
                    for row in connection.execute(
                        "SELECT name FROM sqlite_master WHERE type = 'table'"
                    )
                }
                self.assertEqual(
                    tables,
                    {"decks", "questions", "study_records", "user_stats"},
                )
                self.assertEqual(
                    connection.execute("PRAGMA user_version").fetchone()[0], 1
                )
                self.assertEqual(
                    connection.execute(
                        "SELECT hearts, max_hearts FROM user_stats WHERE id = 1"
                    ).fetchone(),
                    (99, 99),
                )
                options = connection.execute(
                    "SELECT options FROM questions WHERE id = ?",
                    ("course-ts-01-q01",),
                ).fetchone()[0]
                self.assertNotIn("\x00", options)
                self.assertEqual(
                    json.loads(options),
                    course["decks"][0]["questions"][0]["options"],
                )

            self.assertFalse(output.with_name("dlg_q.db-wal").exists())
            self.assertFalse(output.with_name("dlg_q.db-shm").exists())

    def test_database_check_rejects_non_json_options(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "dlg_q.db"
            course = sample_course()
            build.build_database([course], output)
            with closing(sqlite3.connect(output)) as connection, connection:
                connection.execute(
                    "UPDATE questions SET options = ? WHERE id = ?",
                    ("A|B|C|D", "course-ts-01-q01"),
                )

            with self.assertRaisesRegex(build.ValidationError, "JSON"):
                build.check_database(
                    output,
                    expected_decks=1,
                    expected_questions=1,
                )

    def test_database_check_detects_question_count_drift(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "dlg_q.db"
            course = sample_course()
            build.build_database([course], output)
            with closing(sqlite3.connect(output)) as connection, connection:
                connection.execute(
                    "UPDATE decks SET question_count = 2 WHERE id = 'course-ts-01'"
                )

            with self.assertRaisesRegex(build.ValidationError, "question_count"):
                build.check_database(output, expected_decks=1, expected_questions=1)


if __name__ == "__main__":
    unittest.main()
