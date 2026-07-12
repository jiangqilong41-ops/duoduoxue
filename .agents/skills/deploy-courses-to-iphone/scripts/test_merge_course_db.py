import json
import os
import sqlite3
import stat
import subprocess
import sys
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from urllib.parse import unquote, urlparse
from unittest import mock

import merge_course_db as merge


SCRIPT = Path(__file__).with_name("merge_course_db.py")

SCHEMA = """
CREATE TABLE decks (
  id TEXT PRIMARY KEY,
  title TEXT NOT NULL,
  source_text TEXT,
  source_image TEXT,
  question_count INTEGER DEFAULT 0,
  mastery_level INTEGER DEFAULT 0,
  created_at INTEGER NOT NULL,
  updated_at INTEGER NOT NULL
);
CREATE TABLE questions (
  id TEXT PRIMARY KEY,
  deck_id TEXT NOT NULL,
  type TEXT NOT NULL,
  content TEXT NOT NULL,
  options TEXT,
  answer TEXT NOT NULL,
  explanation TEXT,
  match_left TEXT,
  match_right TEXT,
  FOREIGN KEY (deck_id) REFERENCES decks(id) ON DELETE CASCADE
);
CREATE TABLE study_records (
  id TEXT PRIMARY KEY,
  deck_id TEXT NOT NULL,
  correct_count INTEGER DEFAULT 0,
  total_count INTEGER DEFAULT 0,
  last_studied_at INTEGER NOT NULL,
  FOREIGN KEY (deck_id) REFERENCES decks(id) ON DELETE CASCADE
);
CREATE TABLE user_stats (
  id INTEGER PRIMARY KEY DEFAULT 1,
  xp INTEGER DEFAULT 0,
  streak INTEGER DEFAULT 0,
  hearts INTEGER DEFAULT 5,
  max_hearts INTEGER DEFAULT 5,
  last_study_date INTEGER NOT NULL,
  daily_goal INTEGER DEFAULT 50,
  today_xp INTEGER DEFAULT 0
);
"""


def deck(
    deck_id: str,
    *,
    title: str | None = None,
    question_count: int = 1,
    mastery_level: int = 0,
    created_at: int = 100,
    updated_at: int = 100,
) -> tuple[object, ...]:
    return (
        deck_id,
        title or deck_id,
        f"source:{deck_id}",
        None,
        question_count,
        mastery_level,
        created_at,
        updated_at,
    )


def question(
    question_id: str,
    deck_id: str,
    *,
    content: str | None = None,
) -> tuple[object, ...]:
    return (
        question_id,
        deck_id,
        "multiple_choice",
        content or f"content:{question_id}",
        '["A","B","C","D"]',
        "A",
        "explanation",
        None,
        None,
    )


def create_database(
    path: Path,
    *,
    decks: tuple[tuple[object, ...], ...],
    questions: tuple[tuple[object, ...], ...],
    stats: tuple[object, ...] = (1, 0, 0, 99, 99, 100, 50, 0),
    records: tuple[tuple[object, ...], ...] = (),
    schema: str = SCHEMA,
) -> None:
    with closing(sqlite3.connect(path)) as connection, connection:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA journal_mode = DELETE")
        connection.executescript(schema)
        connection.executemany(
            """
            INSERT INTO decks
              (id, title, source_text, source_image, question_count,
               mastery_level, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            decks,
        )
        connection.executemany(
            """
            INSERT INTO questions
              (id, deck_id, type, content, options, answer, explanation,
               match_left, match_right)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            questions,
        )
        connection.executemany(
            "INSERT INTO study_records VALUES (?, ?, ?, ?, ?)", records
        )
        connection.execute(
            "INSERT INTO user_stats VALUES (?, ?, ?, ?, ?, ?, ?, ?)", stats
        )
        connection.execute("PRAGMA user_version = 1")


class MergeCourseDatabaseTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.device = self.root / "device.db"
        self.seed = self.root / "seed.db"
        self.output = self.root / "merged.db"

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def run_merge(self) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--device-db",
                str(self.device),
                "--seed-db",
                str(self.seed),
                "--output",
                str(self.output),
            ],
            capture_output=True,
            text=True,
            check=False,
        )

    def assert_success(
        self,
        result: subprocess.CompletedProcess[str],
        *,
        decks: int,
        questions: int,
    ) -> dict[str, object]:
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(len(result.stdout.strip().splitlines()), 1)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["ok"], True)
        self.assertEqual(payload["added_decks"], decks)
        self.assertEqual(payload["added_questions"], questions)
        self.assertEqual(payload["changed"], bool(decks or questions))
        return payload

    def assert_failure(self, result: subprocess.CompletedProcess[str]) -> None:
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertEqual(len(result.stderr.strip().splitlines()), 1)
        self.assertEqual(json.loads(result.stderr)["ok"], False)

    def test_adds_missing_deck_and_question_without_modifying_inputs(self) -> None:
        base = deck("course-aa-01", question_count=2, mastery_level=7, updated_at=999)
        seed_base = deck("course-aa-01", question_count=2)
        new = deck("course-bb-01", created_at=90, updated_at=90)
        first = question("course-aa-01-q01", "course-aa-01")
        second = question("course-aa-01-q02", "course-aa-01")
        third = question("course-bb-01-q01", "course-bb-01")
        create_database(self.device, decks=(base,), questions=(first,))
        create_database(
            self.seed,
            decks=(seed_base, new),
            questions=(first, second, third),
        )
        before_device = self.device.read_bytes()
        before_seed = self.seed.read_bytes()

        result = self.run_merge()

        self.assert_success(result, decks=1, questions=2)
        self.assertEqual(self.device.read_bytes(), before_device)
        self.assertEqual(self.seed.read_bytes(), before_seed)
        with closing(sqlite3.connect(self.output)) as connection:
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM decks").fetchone()[0], 2)
            self.assertEqual(
                connection.execute("SELECT COUNT(*) FROM questions").fetchone()[0], 3
            )
            self.assertEqual(connection.execute("PRAGMA journal_mode").fetchone()[0], "delete")
            self.assertEqual(connection.execute("PRAGMA integrity_check").fetchone(), ("ok",))
            self.assertEqual(connection.execute("PRAGMA foreign_key_check").fetchall(), [])
        for suffix in ("-wal", "-shm", "-journal"):
            self.assertFalse(Path(str(self.output) + suffix).exists())

    def test_preserves_progress_stats_and_existing_deck_state(self) -> None:
        base = deck("course-aa-01", mastery_level=81, updated_at=9_999)
        seed_base = deck("course-aa-01", mastery_level=0, updated_at=100)
        new = deck("course-bb-01")
        first = question("course-aa-01-q01", "course-aa-01")
        second = question("course-bb-01-q01", "course-bb-01")
        stats = (1, 4321, 17, 63, 99, 888, 75, 44)
        record = ("record-1", "course-aa-01", 4, 5, 777)
        create_database(
            self.device,
            decks=(base,),
            questions=(first,),
            stats=stats,
            records=(record,),
        )
        create_database(
            self.seed,
            decks=(seed_base, new),
            questions=(first, second),
        )

        result = self.run_merge()

        self.assert_success(result, decks=1, questions=1)
        with closing(sqlite3.connect(self.output)) as connection:
            self.assertEqual(connection.execute("SELECT * FROM user_stats").fetchone(), stats)
            self.assertEqual(connection.execute("SELECT * FROM study_records").fetchone(), record)
            self.assertEqual(
                connection.execute(
                    "SELECT mastery_level, updated_at FROM decks WHERE id = 'course-aa-01'"
                ).fetchone(),
                (81, 9_999),
            )

    def test_preserves_user_deck_and_question(self) -> None:
        base = deck("course-aa-01")
        custom = deck("user-custom", title="我的题包")
        first = question("course-aa-01-q01", "course-aa-01")
        custom_question = question("user-custom-q01", "user-custom")
        new = deck("course-bb-01")
        create_database(
            self.device,
            decks=(base, custom),
            questions=(first, custom_question),
        )
        create_database(
            self.seed,
            decks=(base, new),
            questions=(first, question("course-bb-01-q01", "course-bb-01")),
        )

        result = self.run_merge()

        self.assert_success(result, decks=1, questions=1)
        with closing(sqlite3.connect(self.output)) as connection:
            self.assertEqual(
                connection.execute(
                    "SELECT title, mastery_level FROM decks WHERE id = 'user-custom'"
                ).fetchone(),
                ("我的题包", 0),
            )
            self.assertEqual(
                connection.execute(
                    "SELECT content FROM questions WHERE id = 'user-custom-q01'"
                ).fetchone(),
                ("content:user-custom-q01",),
            )

    def test_no_op_output_is_byte_identical_to_device(self) -> None:
        base = deck("course-aa-01", mastery_level=8, updated_at=999)
        seed_base = deck("course-aa-01")
        first = question("course-aa-01-q01", "course-aa-01")
        create_database(self.device, decks=(base,), questions=(first,))
        create_database(self.seed, decks=(seed_base,), questions=(first,))

        result = self.run_merge()

        self.assert_success(result, decks=0, questions=0)
        self.assertEqual(self.output.read_bytes(), self.device.read_bytes())

    def test_copies_each_input_once_before_using_private_snapshots(self) -> None:
        base = deck("course-aa-01")
        first = question("course-aa-01-q01", "course-aa-01")
        create_database(self.device, decks=(base,), questions=(first,))
        create_database(self.seed, decks=(base,), questions=(first,))
        copied_inputs: list[str] = []
        real_copyfile = merge.shutil.copyfile

        def record_copy(source: object, destination: object, *args: object, **kwargs: object) -> object:
            source_path = Path(source)
            if source_path.exists() and os.path.samefile(source_path, self.device):
                copied_inputs.append("device")
            if source_path.exists() and os.path.samefile(source_path, self.seed):
                copied_inputs.append("seed")
            return real_copyfile(source, destination, *args, **kwargs)

        with mock.patch.object(merge.shutil, "copyfile", side_effect=record_copy):
            merge.merge_databases(self.device, self.seed, self.output)

        self.assertEqual(copied_inputs.count("device"), 1)
        self.assertEqual(copied_inputs.count("seed"), 1)

    def test_staging_failure_preserves_output_and_cleans_private_directory(self) -> None:
        base = deck("course-aa-01")
        first = question("course-aa-01-q01", "course-aa-01")
        create_database(self.device, decks=(base,), questions=(first,))
        create_database(self.seed, decks=(base,), questions=(first,))
        original = b"previous-output"
        self.output.write_bytes(original)
        staging_observations: list[tuple[str, int, Path]] = []

        def fail_in_staging(path: Path, label: str) -> object:
            staging_observations.append(
                (
                    path.parent.name,
                    stat.S_IMODE(path.parent.stat().st_mode),
                    path,
                )
            )
            raise merge.MergeError("forced staging failure")

        with (
            mock.patch.object(merge, "_load_rows", side_effect=fail_in_staging),
            self.assertRaisesRegex(merge.MergeError, "forced staging failure"),
        ):
            merge.merge_databases(self.device, self.seed, self.output)

        self.assertEqual(len(staging_observations), 1)
        stage_name, stage_mode, validated_path = staging_observations[0]
        self.assertTrue(stage_name.startswith(".merge-course-db-"))
        self.assertEqual(stage_mode, 0o700)
        self.assertNotEqual(validated_path, self.device)
        self.assertEqual(self.output.read_bytes(), original)
        self.assertEqual(list(self.root.glob(".merge-course-db-*")), [])

    def test_rejects_input_replaced_while_snapshot_is_copied(self) -> None:
        base = deck("course-aa-01")
        first = question("course-aa-01-q01", "course-aa-01")
        create_database(self.device, decks=(base,), questions=(first,))
        create_database(self.seed, decks=(base,), questions=(first,))
        replacement = self.root / "replacement.db"
        create_database(replacement, decks=(base,), questions=(first,))
        original_output = b"previous-output"
        self.output.write_bytes(original_output)
        real_copyfile = merge.shutil.copyfile

        def replace_source_after_copy(
            source: object,
            destination: object,
            *args: object,
            **kwargs: object,
        ) -> object:
            result = real_copyfile(source, destination, *args, **kwargs)
            if Path(source) == self.device:
                os.replace(replacement, self.device)
            return result

        with (
            mock.patch.object(
                merge.shutil,
                "copyfile",
                side_effect=replace_source_after_copy,
            ),
            self.assertRaisesRegex(merge.MergeError, "changed while being copied"),
        ):
            merge.merge_databases(self.device, self.seed, self.output)

        self.assertEqual(self.output.read_bytes(), original_output)
        self.assertEqual(list(self.root.glob(".merge-course-db-*")), [])

    def test_no_op_candidate_is_revalidated_before_replacing_output(self) -> None:
        base = deck("course-aa-01")
        first = question("course-aa-01-q01", "course-aa-01")
        create_database(self.device, decks=(base,), questions=(first,))
        create_database(self.seed, decks=(base,), questions=(first,))
        original = b"previous-output"
        self.output.write_bytes(original)
        labels: list[str] = []
        real_load_rows = merge._load_rows

        def fail_candidate(path: Path, label: str) -> object:
            labels.append(label)
            if label == "merged database":
                raise merge.MergeError("forced candidate validation failure")
            return real_load_rows(path, label)

        with (
            mock.patch.object(merge, "_load_rows", side_effect=fail_candidate),
            self.assertRaisesRegex(merge.MergeError, "candidate validation failure"),
        ):
            merge.merge_databases(self.device, self.seed, self.output)

        self.assertIn("merged database", labels)
        self.assertEqual(self.output.read_bytes(), original)
        self.assertEqual(list(self.root.glob(".merge-course-db-*")), [])

    def test_post_replace_sidecar_preserves_current_file_set_and_backup(self) -> None:
        base = deck("course-aa-01")
        first = question("course-aa-01-q01", "course-aa-01")
        create_database(self.device, decks=(base,), questions=(first,))
        create_database(self.seed, decks=(base,), questions=(first,))
        original = b"previous-output"
        self.output.write_bytes(original)
        sidecar = Path(str(self.output) + "-wal")
        real_replace = merge.os.replace

        def create_sidecar_after_replace(source: object, destination: object) -> None:
            real_replace(source, destination)
            if Path(source).name == "merged.db" and Path(destination) == self.output:
                sidecar.write_bytes(b"late wal")

        with (
            mock.patch.object(merge.os, "replace", side_effect=create_sidecar_after_replace),
            self.assertRaisesRegex(merge.RecoveryError, "current file set preserved"),
        ):
            merge.merge_databases(self.device, self.seed, self.output)

        self.assertTrue(self.output.read_bytes().startswith(b"SQLite format 3"))
        self.assertEqual(sidecar.read_bytes(), b"late wal")
        staging = list(self.root.glob(".merge-course-db-*"))
        self.assertEqual(len(staging), 1)
        self.assertEqual(stat.S_IMODE(staging[0].stat().st_mode), 0o700)
        self.assertEqual((staging[0] / "previous-output").read_bytes(), original)

    def test_rollback_failure_keeps_private_recovery_backup(self) -> None:
        base = deck("course-aa-01")
        first = question("course-aa-01-q01", "course-aa-01")
        create_database(self.device, decks=(base,), questions=(first,))
        create_database(self.seed, decks=(base,), questions=(first,))
        original = b"previous-output"
        self.output.write_bytes(original)
        real_reject_sidecars = merge._reject_sidecars
        real_replace = merge.os.replace

        def fail_after_replace(path: Path, label: str) -> None:
            real_reject_sidecars(path, label)
            if path == self.output and path.read_bytes().startswith(b"SQLite format 3"):
                raise merge.MergeError("forced post-replace failure")

        def fail_rollback(source: object, destination: object) -> None:
            if Path(source).name == "previous-output":
                raise OSError("forced rollback failure")
            real_replace(source, destination)

        with (
            mock.patch.object(
                merge,
                "_reject_sidecars",
                side_effect=fail_after_replace,
            ),
            mock.patch.object(merge.os, "replace", side_effect=fail_rollback),
            self.assertRaisesRegex(merge.MergeError, "rollback failed"),
        ):
            merge.merge_databases(self.device, self.seed, self.output)

        staging = list(self.root.glob(".merge-course-db-*"))
        self.assertEqual(len(staging), 1)
        self.assertEqual(stat.S_IMODE(staging[0].stat().st_mode), 0o700)
        self.assertEqual((staging[0] / "previous-output").read_bytes(), original)

    def test_rejects_conflicting_existing_deck(self) -> None:
        base = deck("course-aa-01", title="device title")
        changed = deck("course-aa-01", title="seed title")
        first = question("course-aa-01-q01", "course-aa-01")
        create_database(self.device, decks=(base,), questions=(first,))
        create_database(self.seed, decks=(changed,), questions=(first,))

        result = self.run_merge()

        self.assert_failure(result)
        self.assertFalse(self.output.exists())

    def test_rejects_conflicting_existing_question(self) -> None:
        base = deck("course-aa-01")
        device_question = question("course-aa-01-q01", "course-aa-01")
        seed_question = question(
            "course-aa-01-q01", "course-aa-01", content="changed"
        )
        create_database(self.device, decks=(base,), questions=(device_question,))
        create_database(self.seed, decks=(base,), questions=(seed_question,))

        result = self.run_merge()

        self.assert_failure(result)
        self.assertFalse(self.output.exists())

    def test_rejects_bad_schema(self) -> None:
        base = deck("course-aa-01")
        first = question("course-aa-01-q01", "course-aa-01")
        create_database(self.device, decks=(base,), questions=(first,))
        create_database(self.seed, decks=(base,), questions=(first,))
        with closing(sqlite3.connect(self.seed)) as connection, connection:
            connection.execute("ALTER TABLE decks ADD COLUMN unexpected TEXT")

        result = self.run_merge()

        self.assert_failure(result)
        self.assertFalse(self.output.exists())

    def test_rejects_hidden_schema_semantics(self) -> None:
        base = deck("course-aa-01")
        first = question("course-aa-01-q01", "course-aa-01")
        create_database(self.device, decks=(base,), questions=(first,))
        variants = {
            "check": SCHEMA.replace(
                "question_count INTEGER DEFAULT 0,",
                "question_count INTEGER DEFAULT 0 CHECK (question_count >= 0),",
                1,
            ),
            "collate": SCHEMA.replace(
                "title TEXT NOT NULL,",
                "title TEXT COLLATE NOCASE NOT NULL,",
                1,
            ),
            "deferrable": SCHEMA.replace(
                "ON DELETE CASCADE",
                "ON DELETE CASCADE DEFERRABLE INITIALLY DEFERRED",
                1,
            ),
            "unique": SCHEMA.replace(
                "updated_at INTEGER NOT NULL\n);",
                "updated_at INTEGER NOT NULL,\n  UNIQUE(title)\n);",
                1,
            ),
            "generated": SCHEMA.replace(
                "updated_at INTEGER NOT NULL\n);",
                "updated_at INTEGER NOT NULL,\n"
                "  generated_title TEXT GENERATED ALWAYS AS (title) VIRTUAL\n);",
                1,
            ),
        }
        for label, schema in variants.items():
            with self.subTest(label=label):
                self.seed.unlink(missing_ok=True)
                self.output.unlink(missing_ok=True)
                create_database(
                    self.seed,
                    decks=(base,),
                    questions=(first,),
                    schema=schema,
                )

                result = self.run_merge()

                self.assert_failure(result)
                self.assertFalse(self.output.exists())

    def test_rejects_missing_foreign_key_definition(self) -> None:
        base = deck("course-aa-01")
        first = question("course-aa-01-q01", "course-aa-01")
        create_database(self.device, decks=(base,), questions=(first,))
        schema_without_question_fk = SCHEMA.replace(
            ",\n  FOREIGN KEY (deck_id) REFERENCES decks(id) ON DELETE CASCADE\n);",
            "\n);",
            1,
        )
        create_database(
            self.seed,
            decks=(base,),
            questions=(first,),
            schema=schema_without_question_fk,
        )

        result = self.run_merge()

        self.assert_failure(result)
        self.assertFalse(self.output.exists())

    def test_rejects_extra_internal_schema_objects(self) -> None:
        base = deck("course-aa-01")
        first = question("course-aa-01-q01", "course-aa-01")
        create_database(self.device, decks=(base,), questions=(first,))
        mutations = {
            "sqlite_sequence": (
                "CREATE TABLE transient_auto "
                "(id INTEGER PRIMARY KEY AUTOINCREMENT); "
                "DROP TABLE transient_auto;"
            ),
            "sqlite_stat1": "ANALYZE;",
        }
        for internal_table, sql in mutations.items():
            with self.subTest(internal_table=internal_table):
                self.seed.unlink(missing_ok=True)
                self.output.unlink(missing_ok=True)
                create_database(self.seed, decks=(base,), questions=(first,))
                with closing(sqlite3.connect(self.seed)) as connection, connection:
                    connection.executescript(sql)
                    self.assertIsNotNone(
                        connection.execute(
                            "SELECT 1 FROM sqlite_schema WHERE name = ?",
                            (internal_table,),
                        ).fetchone()
                    )

                result = self.run_merge()

                self.assert_failure(result)
                self.assertFalse(self.output.exists())

    def test_rejects_foreign_key_error(self) -> None:
        base = deck("course-aa-01")
        first = question("course-aa-01-q01", "course-aa-01")
        create_database(self.device, decks=(base,), questions=(first,))
        create_database(self.seed, decks=(base,), questions=(first,))
        with closing(sqlite3.connect(self.seed)) as connection, connection:
            connection.execute("PRAGMA foreign_keys = OFF")
            connection.execute(
                "INSERT INTO questions VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                question("orphan-q01", "missing-deck"),
            )

        result = self.run_merge()

        self.assert_failure(result)
        self.assertFalse(self.output.exists())

    def test_rejects_every_sidecar_for_each_path(self) -> None:
        base = deck("course-aa-01")
        first = question("course-aa-01-q01", "course-aa-01")
        for label in ("device", "seed", "output"):
            for suffix in ("-wal", "-shm", "-journal"):
                with self.subTest(label=label, suffix=suffix):
                    self.device.unlink(missing_ok=True)
                    self.seed.unlink(missing_ok=True)
                    self.output.unlink(missing_ok=True)
                    for path in self.root.glob("*.db-*"):
                        path.unlink()
                    create_database(self.device, decks=(base,), questions=(first,))
                    create_database(self.seed, decks=(base,), questions=(first,))
                    target = getattr(self, label)
                    if label == "output":
                        self.output.write_bytes(b"original-output")
                    Path(str(target) + suffix).write_bytes(b"sidecar")
                    original = self.output.read_bytes() if self.output.exists() else None

                    result = self.run_merge()

                    self.assert_failure(result)
                    if original is None:
                        self.assertFalse(self.output.exists())
                    else:
                        self.assertEqual(self.output.read_bytes(), original)

    def test_rejects_dangling_sidecar_symlink(self) -> None:
        base = deck("course-aa-01")
        first = question("course-aa-01-q01", "course-aa-01")
        create_database(self.device, decks=(base,), questions=(first,))
        create_database(self.seed, decks=(base,), questions=(first,))
        sidecar = Path(str(self.device) + "-wal")
        sidecar.symlink_to(self.root / "missing-sidecar-target")
        self.assertTrue(os.path.lexists(sidecar))
        self.assertFalse(sidecar.exists())

        result = self.run_merge()

        self.assert_failure(result)
        self.assertFalse(self.output.exists())

    def test_rejects_sidecar_created_while_inputs_are_copied(self) -> None:
        base = deck("course-aa-01")
        first = question("course-aa-01-q01", "course-aa-01")
        create_database(self.device, decks=(base,), questions=(first,))
        create_database(self.seed, decks=(base,), questions=(first,))
        real_copyfile = merge.shutil.copyfile

        def create_sidecar_after_copy(
            source: object,
            destination: object,
            *args: object,
            **kwargs: object,
        ) -> object:
            result = real_copyfile(source, destination, *args, **kwargs)
            if Path(source) == self.seed:
                Path(str(self.device) + "-journal").write_bytes(b"late sidecar")
            return result

        with mock.patch.object(
            merge.shutil,
            "copyfile",
            side_effect=create_sidecar_after_copy,
        ):
            with self.assertRaisesRegex(merge.MergeError, "sidecar"):
                merge.merge_databases(self.device, self.seed, self.output)

        self.assertFalse(self.output.exists())
        self.assertEqual(list(self.root.glob(".merge-course-db-*")), [])

    def test_all_sqlite_connections_stay_in_private_staging(self) -> None:
        base = deck("course-aa-01")
        new = deck("course-bb-01")
        first = question("course-aa-01-q01", "course-aa-01")
        second = question("course-bb-01-q01", "course-bb-01")
        create_database(self.device, decks=(base,), questions=(first,))
        create_database(
            self.seed,
            decks=(base, new),
            questions=(first, second),
        )
        observations: list[tuple[str, int]] = []
        real_connect = merge.sqlite3.connect

        def record_connect(
            database: object,
            *args: object,
            **kwargs: object,
        ) -> sqlite3.Connection:
            raw = os.fspath(database)
            path = (
                Path(unquote(urlparse(raw).path))
                if kwargs.get("uri")
                else Path(raw)
            )
            observations.append(
                (path.parent.name, stat.S_IMODE(path.parent.stat().st_mode))
            )
            return real_connect(database, *args, **kwargs)

        with mock.patch.object(merge.sqlite3, "connect", side_effect=record_connect):
            merge.merge_databases(self.device, self.seed, self.output)

        self.assertGreaterEqual(len(observations), 3)
        for stage_name, stage_mode in observations:
            self.assertTrue(stage_name.startswith(".merge-course-db-"))
            self.assertEqual(stage_mode, 0o700)

    def test_success_reports_warning_when_private_staging_cannot_be_removed(self) -> None:
        base = deck("course-aa-01")
        first = question("course-aa-01-q01", "course-aa-01")
        create_database(self.device, decks=(base,), questions=(first,))
        create_database(self.seed, decks=(base,), questions=(first,))

        with mock.patch.object(
            merge.shutil,
            "rmtree",
            side_effect=OSError("forced cleanup failure"),
        ):
            result = merge.merge_databases(self.device, self.seed, self.output)

        warnings = result.get("warnings")
        self.assertIsInstance(warnings, list)
        self.assertEqual(len(warnings), 1)
        staging = list(self.root.glob(".merge-course-db-*"))
        self.assertEqual(len(staging), 1)
        self.assertIn(str(staging[0]), warnings[0])
        self.assertEqual(stat.S_IMODE(staging[0].stat().st_mode), 0o700)

    def test_rejects_null_study_record_id(self) -> None:
        base = deck("course-aa-01")
        first = question("course-aa-01-q01", "course-aa-01")
        record = (None, "course-aa-01", 1, 1, 100)
        create_database(
            self.device,
            decks=(base,),
            questions=(first,),
            records=(record,),
        )
        create_database(self.seed, decks=(base,), questions=(first,))

        result = self.run_merge()

        self.assert_failure(result)
        self.assertFalse(self.output.exists())

    def test_rejects_dangling_output_path_alias(self) -> None:
        base = deck("course-aa-01")
        first = question("course-aa-01-q01", "course-aa-01")
        create_database(self.device, decks=(base,), questions=(first,))
        create_database(self.seed, decks=(base,), questions=(first,))
        alias_target = self.root / "future-output.db"
        self.output.symlink_to(alias_target)
        self.assertTrue(os.path.lexists(self.output))
        self.assertFalse(self.output.exists())

        result = self.run_merge()

        self.assert_failure(result)
        self.assertTrue(self.output.is_symlink())
        self.assertFalse(alias_target.exists())

    def test_rejects_null_primary_keys_in_course_tables(self) -> None:
        null_deck = (
            None,
            "null deck",
            "source:null",
            None,
            0,
            0,
            100,
            100,
        )
        base = deck("course-aa-01")
        null_question = (
            None,
            "course-aa-01",
            "multiple_choice",
            "null id",
            '[]',
            "answer",
            "explanation",
            None,
            None,
        )
        cases = (
            ((null_deck,), (), (), ()),
            ((base,), (null_question,), (base,), ()),
        )
        for index, (device_decks, device_questions, seed_decks, seed_questions) in enumerate(cases):
            with self.subTest(table=("decks", "questions")[index]):
                self.device.unlink(missing_ok=True)
                self.seed.unlink(missing_ok=True)
                self.output.unlink(missing_ok=True)
                create_database(
                    self.device,
                    decks=device_decks,
                    questions=device_questions,
                )
                create_database(
                    self.seed,
                    decks=seed_decks,
                    questions=seed_questions,
                )

                result = self.run_merge()

                self.assert_failure(result)
                self.assertFalse(self.output.exists())

    def test_failure_does_not_overwrite_existing_output(self) -> None:
        base = deck("course-aa-01", title="device title")
        changed = deck("course-aa-01", title="seed title")
        first = question("course-aa-01-q01", "course-aa-01")
        create_database(self.device, decks=(base,), questions=(first,))
        create_database(self.seed, decks=(changed,), questions=(first,))
        original = b"previous-valid-output"
        self.output.write_bytes(original)

        result = self.run_merge()

        self.assert_failure(result)
        self.assertEqual(self.output.read_bytes(), original)
        self.assertEqual(list(self.root.glob(".merged.db.*.tmp")), [])


if __name__ == "__main__":
    unittest.main()
