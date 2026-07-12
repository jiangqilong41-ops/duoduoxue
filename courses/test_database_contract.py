import copy
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from contextlib import closing, redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from unittest import mock

from courses import build


class DatabaseReleaseContractTest(unittest.TestCase):
    def test_build_preserves_existing_output_when_final_validation_fails(self) -> None:
        course_dir = Path(__file__).resolve().parent
        courses, labs = build.load_release(course_dir)
        build.validate_release(courses, labs)

        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "dlg_q.db"
            original = b"previous-validated-release"
            output.write_bytes(original)

            with mock.patch.object(
                build,
                "check_database",
                side_effect=build.ValidationError("forced final validation failure"),
            ):
                with self.assertRaisesRegex(
                    build.ValidationError,
                    "forced final validation failure",
                ):
                    build.build_database(courses, output)

            self.assertEqual(output.read_bytes(), original)
            self.assertEqual(list(output.parent.glob("*.tmp*")), [])

    def test_check_rejects_database_stale_against_valid_course_sources(self) -> None:
        course_dir = Path(__file__).resolve().parent
        courses, labs = build.load_release(course_dir)
        build.validate_release(courses, labs)

        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "dlg_q.db"
            build.build_database(courses, output)

            changed_courses = copy.deepcopy(courses)
            changed_courses[0]["decks"][0]["questions"][0]["explanation"] += (
                "\n实践补充：这条合法更新必须使旧数据库校验失败。"
            )

            with (
                mock.patch.object(
                    build,
                    "load_release",
                    return_value=(changed_courses, labs),
                ),
                redirect_stdout(StringIO()),
                redirect_stderr(StringIO()),
            ):
                result = build.main(["--check", "--output", str(output)])

            self.assertEqual(result, 1)

    def test_check_rejects_wal_header_without_creating_sidecars(self) -> None:
        course_dir = Path(__file__).resolve().parent
        courses, labs = build.load_release(course_dir)
        build.validate_release(courses, labs)

        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "dlg_q.db"
            build.build_database(courses, output)
            with closing(sqlite3.connect(output)) as connection, connection:
                self.assertEqual(
                    connection.execute("PRAGMA journal_mode = WAL").fetchone()[0],
                    "wal",
                )
                connection.execute("PRAGMA wal_checkpoint(TRUNCATE)")

            sidecars = [
                output.with_name(output.name + suffix)
                for suffix in ("-wal", "-shm", "-journal")
            ]
            for path in sidecars:
                path.unlink(missing_ok=True)
            self.assertTrue(all(not path.exists() for path in sidecars))

            with self.assertRaisesRegex(build.ValidationError, "journal_mode"):
                build.check_database(output, expected_courses=courses)

            self.assertTrue(all(not path.exists() for path in sidecars))

    def test_cli_reports_malformed_sqlite_page_without_traceback(self) -> None:
        course_dir = Path(__file__).resolve().parent
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "dlg_q.db"
            damaged = bytearray((course_dir / "dist" / "dlg_q.db").read_bytes())
            header = bytes(damaged[:20])
            damaged[100:200] = b"\0" * 100
            output.write_bytes(damaged)

            self.assertEqual(output.read_bytes()[:20], header)
            result = subprocess.run(
                [
                    sys.executable,
                    str(course_dir / "build.py"),
                    "--check",
                    "--output",
                    str(output),
                ],
                capture_output=True,
                text=True,
                check=False,
            )

        self.assertEqual(result.returncode, 1)
        self.assertIn("course build failed:", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_check_rejects_missing_question_foreign_key_definition(self) -> None:
        course_dir = Path(__file__).resolve().parent
        courses, labs = build.load_release(course_dir)
        build.validate_release(courses, labs)

        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "dlg_q.db"
            build.build_database(courses, output)
            with closing(sqlite3.connect(output)) as connection, connection:
                connection.executescript(
                    """
                    PRAGMA foreign_keys = OFF;
                    CREATE TABLE questions_without_foreign_key (
                      id TEXT PRIMARY KEY,
                      deck_id TEXT NOT NULL,
                      type TEXT NOT NULL,
                      content TEXT NOT NULL,
                      options TEXT,
                      answer TEXT NOT NULL,
                      explanation TEXT,
                      match_left TEXT,
                      match_right TEXT
                    );
                    INSERT INTO questions_without_foreign_key
                      SELECT * FROM questions;
                    DROP TABLE questions;
                    ALTER TABLE questions_without_foreign_key RENAME TO questions;
                    """
                )

            with self.assertRaisesRegex(build.ValidationError, "schema"):
                build.check_database(output, expected_courses=courses)

    def test_check_rejects_orphan_question_and_study_record(self) -> None:
        course_dir = Path(__file__).resolve().parent
        courses, labs = build.load_release(course_dir)
        build.validate_release(courses, labs)

        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "dlg_q.db"
            build.build_database(courses, output)
            with closing(sqlite3.connect(output)) as connection:
                connection.execute("PRAGMA foreign_keys = OFF")
                for table in ("questions", "study_records"):
                    self.assertEqual(
                        [
                            (row[2], row[3], row[4])
                            for row in connection.execute(
                                f"PRAGMA foreign_key_list({table})"
                            )
                        ],
                        [("decks", "deck_id", "id")],
                    )
                with connection:
                    connection.execute(
                        """
                        INSERT INTO questions
                          (id, deck_id, type, content, options, answer,
                           explanation, match_left, match_right)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            "orphan-question",
                            "missing-deck",
                            "true_false",
                            "[Test] 孤儿题目",
                            '["正确","错误"]',
                            "正确",
                            "结论：正确。\n依据：测试。\n实践：检查。",
                            "[]",
                            "[]",
                        ),
                    )
                    connection.execute(
                        """
                        INSERT INTO study_records (id, deck_id, last_studied_at)
                        VALUES (?, ?, ?)
                        """,
                        ("orphan-record", "missing-deck", build.BASE_CREATED_AT),
                    )
                self.assertEqual(
                    {row[0] for row in connection.execute("PRAGMA foreign_key_check")},
                    {"questions", "study_records"},
                )

            with self.assertRaisesRegex(build.ValidationError, "foreign_key_check"):
                build.check_database(output, expected_courses=courses)

    def test_check_rejects_extra_schema_objects(self) -> None:
        course_dir = Path(__file__).resolve().parent
        courses, labs = build.load_release(course_dir)
        build.validate_release(courses, labs)

        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "dlg_q.db"
            build.build_database(courses, output)
            with closing(sqlite3.connect(output)) as connection, connection:
                connection.executescript(
                    """
                    CREATE TRIGGER mutate_stats
                    AFTER INSERT ON study_records
                    BEGIN
                      UPDATE user_stats SET hearts = 0 WHERE id = 1;
                    END;
                    """
                )

            with self.assertRaisesRegex(build.ValidationError, "schema object"):
                build.check_database(output, expected_courses=courses)

    def test_check_rejects_nul_in_any_text_column(self) -> None:
        course_dir = Path(__file__).resolve().parent
        courses, labs = build.load_release(course_dir)
        build.validate_release(courses, labs)

        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "dlg_q.db"
            build.build_database(courses, output)
            with closing(sqlite3.connect(output)) as connection, connection:
                connection.execute(
                    "UPDATE questions SET content = content || char(0) || 'hidden' "
                    "WHERE id = 'course-ag-01-q01'"
                )

            with self.assertRaisesRegex(build.ValidationError, "NUL"):
                build.check_database(output)

    def test_sensitive_scan_covers_common_real_key_and_userinfo_shapes(self) -> None:
        leaked_values = (
            "".join(("gh", "p_", "abcdefghijklmnopqrstuvwxyz1234567890")),
            "".join(("github_", "pat_", "11AAAAAA0abcdefghijklmnopqrstuvwxyz")),
            "".join(("AK", "IA", "IOSFODNN7EXAMPLE")),
            "".join(("xox", "b-", "123456789012-123456789012-abcdefghijklmnop")),
            "".join(("AI", "zaSyA12345678901234567890123456789012")),
            "".join(("mysql://user:", "password@example.test/db")),
            "".join(("mongodb+srv://user:", "password@example.test/db")),
            "".join(("postgresql+asyncpg://user:", "password@example.test/db")),
            "".join(("mysql+pymysql://user:", "password@example.test/db")),
            "".join(("rediss://user:", "password@example.test/0")),
            "".join(("amqp://user:", "password@example.test/vhost")),
            "".join(("https://", "user@example.test/private")),
            "".join(("-----BEGIN ", "PRIVATE KEY-----")),
        )

        for leaked in leaked_values:
            with self.subTest(leaked=leaked):
                with self.assertRaises(build.ValidationError):
                    build.scan_sensitive(leaked, "fixture")


if __name__ == "__main__":
    unittest.main()
