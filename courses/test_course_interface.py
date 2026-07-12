import json
import unittest
from pathlib import Path

from courses import build


class CourseJsonInterfaceTest(unittest.TestCase):
    def test_release_uses_top_level_course_source_and_decks_fields(self) -> None:
        root = Path(__file__).resolve().parent

        for filename in build.COURSE_FILES:
            with self.subTest(filename=filename):
                payload = json.loads((root / filename).read_text(encoding="utf-8"))
                self.assertEqual(set(payload), {"course", "source", "decks"})
                self.assertNotIn("source", payload["course"])
                self.assertEqual(
                    set(payload["source"]),
                    {"kind", "ref", "snapshot"},
                )

    def test_release_snapshot_is_fixed(self) -> None:
        root = Path(__file__).resolve().parent
        courses, labs = build.load_release(root)

        for course, spec in zip(courses, build.COURSE_SPECS):
            source = course.get("source") or course["course"]["source"]
            self.assertEqual(source["snapshot"], spec["snapshot"])
            source["snapshot"] = f"{spec['snapshot']}-changed"
            with self.assertRaisesRegex(build.ValidationError, "snapshot"):
                build.validate_release(courses, labs)
            source["snapshot"] = spec["snapshot"]


if __name__ == "__main__":
    unittest.main()
