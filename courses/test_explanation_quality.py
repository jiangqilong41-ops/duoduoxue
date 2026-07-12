import json
import re
import unittest
from pathlib import Path

from courses import build


class ExplanationQualityTest(unittest.TestCase):
    def test_every_explanation_matches_its_question_type(self) -> None:
        root = Path(__file__).resolve().parent

        for filename in build.COURSE_FILES:
            course = json.loads((root / filename).read_text(encoding="utf-8"))
            for deck in course["decks"]:
                for question in deck["questions"]:
                    with self.subTest(question=question["id"]):
                        explanation = question["explanation"]
                        for marker in ("结论：", "依据：", "实践："):
                            self.assertEqual(explanation.count(marker), 1)

                        if question["type"] == "multiple_choice":
                            self.assertEqual(explanation.count("错误选项："), 1)
                            match = re.fullmatch(
                                r"结论：(.*?)\n依据：(.*?)\n错误选项：(.*?)\n实践：(.*)",
                                explanation,
                                re.DOTALL,
                            )
                            self.assertIsNotNone(match)
                            assert match is not None
                            self.assertTrue(all(section.strip() for section in match.groups()))
                            wrong_section = match.group(3)
                            answer_index = question["options"].index(
                                question["answer"]
                            )
                            for index, letter in enumerate("ABCD"):
                                marker = rf"(?:^|；){letter}："
                                if index == answer_index:
                                    self.assertNotRegex(wrong_section, marker)
                                else:
                                    self.assertRegex(wrong_section, marker)
                            self.assertEqual(
                                len(re.findall(r"(?:^|；)[ABCD]：", wrong_section)),
                                3,
                            )
                        else:
                            self.assertNotIn("错误选项：", explanation)
                            match = re.fullmatch(
                                r"结论：(.*?)\n依据：(.*?)\n实践：(.*)",
                                explanation,
                                re.DOTALL,
                            )
                            self.assertIsNotNone(match)
                            assert match is not None
                            self.assertTrue(all(section.strip() for section in match.groups()))


if __name__ == "__main__":
    unittest.main()
