#!/usr/bin/env python3
"""Merge missing seed course rows into a copied iPhone database."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sqlite3
import stat
import sys
import tempfile
from contextlib import closing, contextmanager
from pathlib import Path
from typing import Any, Iterator


SIDECAR_SUFFIXES = ("-wal", "-shm", "-journal")
CREATE_TABLE_SQL = {
    "decks": """
        CREATE TABLE decks (
          id TEXT PRIMARY KEY,
          title TEXT NOT NULL,
          source_text TEXT,
          source_image TEXT,
          question_count INTEGER DEFAULT 0,
          mastery_level INTEGER DEFAULT 0,
          created_at INTEGER NOT NULL,
          updated_at INTEGER NOT NULL
        )
    """,
    "questions": """
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
        )
    """,
    "study_records": """
        CREATE TABLE study_records (
          id TEXT PRIMARY KEY,
          deck_id TEXT NOT NULL,
          correct_count INTEGER DEFAULT 0,
          total_count INTEGER DEFAULT 0,
          last_studied_at INTEGER NOT NULL,
          FOREIGN KEY (deck_id) REFERENCES decks(id) ON DELETE CASCADE
        )
    """,
    "user_stats": """
        CREATE TABLE user_stats (
          id INTEGER PRIMARY KEY DEFAULT 1,
          xp INTEGER DEFAULT 0,
          streak INTEGER DEFAULT 0,
          hearts INTEGER DEFAULT 5,
          max_hearts INTEGER DEFAULT 5,
          last_study_date INTEGER NOT NULL,
          daily_goal INTEGER DEFAULT 50,
          today_xp INTEGER DEFAULT 0
        )
    """,
}
TABLE_COLUMNS = {
    "decks": (
        ("id", "TEXT", 0, None, 1),
        ("title", "TEXT", 1, None, 0),
        ("source_text", "TEXT", 0, None, 0),
        ("source_image", "TEXT", 0, None, 0),
        ("question_count", "INTEGER", 0, "0", 0),
        ("mastery_level", "INTEGER", 0, "0", 0),
        ("created_at", "INTEGER", 1, None, 0),
        ("updated_at", "INTEGER", 1, None, 0),
    ),
    "questions": (
        ("id", "TEXT", 0, None, 1),
        ("deck_id", "TEXT", 1, None, 0),
        ("type", "TEXT", 1, None, 0),
        ("content", "TEXT", 1, None, 0),
        ("options", "TEXT", 0, None, 0),
        ("answer", "TEXT", 1, None, 0),
        ("explanation", "TEXT", 0, None, 0),
        ("match_left", "TEXT", 0, None, 0),
        ("match_right", "TEXT", 0, None, 0),
    ),
    "study_records": (
        ("id", "TEXT", 0, None, 1),
        ("deck_id", "TEXT", 1, None, 0),
        ("correct_count", "INTEGER", 0, "0", 0),
        ("total_count", "INTEGER", 0, "0", 0),
        ("last_studied_at", "INTEGER", 1, None, 0),
    ),
    "user_stats": (
        ("id", "INTEGER", 0, "1", 1),
        ("xp", "INTEGER", 0, "0", 0),
        ("streak", "INTEGER", 0, "0", 0),
        ("hearts", "INTEGER", 0, "5", 0),
        ("max_hearts", "INTEGER", 0, "5", 0),
        ("last_study_date", "INTEGER", 1, None, 0),
        ("daily_goal", "INTEGER", 0, "50", 0),
        ("today_xp", "INTEGER", 0, "0", 0),
    ),
}
FOREIGN_KEYS = {
    "decks": (),
    "questions": (("decks", "deck_id", "id", "NO ACTION", "CASCADE", "NONE"),),
    "study_records": (
        ("decks", "deck_id", "id", "NO ACTION", "CASCADE", "NONE"),
    ),
    "user_stats": (),
}
EXPECTED_INDEXES = {
    "decks": (("sqlite_autoindex_decks_1", 1, "pk", 0),),
    "questions": (("sqlite_autoindex_questions_1", 1, "pk", 0),),
    "study_records": (("sqlite_autoindex_study_records_1", 1, "pk", 0),),
    "user_stats": (),
}
EXPECTED_INDEX_XINFO = {
    "sqlite_autoindex_decks_1": (
        (0, "id", 0, "BINARY", 1),
        (-1, None, 0, "BINARY", 0),
    ),
    "sqlite_autoindex_questions_1": (
        (0, "id", 0, "BINARY", 1),
        (-1, None, 0, "BINARY", 0),
    ),
    "sqlite_autoindex_study_records_1": (
        (0, "id", 0, "BINARY", 1),
        (-1, None, 0, "BINARY", 0),
    ),
}
DECK_COLUMNS = tuple(item[0] for item in TABLE_COLUMNS["decks"])
QUESTION_COLUMNS = tuple(item[0] for item in TABLE_COLUMNS["questions"])
DECK_MUTABLE_COLUMNS = {"mastery_level", "updated_at"}


class MergeError(RuntimeError):
    pass


class RecoveryError(MergeError):
    """Staging and the current output file set contain recovery evidence."""


class _SidecarError(MergeError):
    pass


def _absolute(path: Path) -> Path:
    return Path(os.path.abspath(os.path.expanduser(os.fspath(path))))


def _sidecars(path: Path) -> tuple[Path, ...]:
    return tuple(Path(str(path) + suffix) for suffix in SIDECAR_SUFFIXES)


def _reject_sidecars(path: Path, label: str) -> None:
    for sidecar in _sidecars(path):
        if os.path.lexists(sidecar):
            raise _SidecarError(f"{label} has sidecar: {sidecar.name}")


def _file_fingerprint(path: Path, label: str) -> tuple[int, int, int, int, int]:
    try:
        metadata = path.stat(follow_symlinks=False)
    except OSError as exc:
        raise MergeError(f"cannot stat {label}: {exc}") from exc
    if not stat.S_ISREG(metadata.st_mode):
        raise MergeError(f"{label} must be a regular file")
    return (
        metadata.st_dev,
        metadata.st_ino,
        metadata.st_size,
        metadata.st_mtime_ns,
        metadata.st_ctime_ns,
    )


def _check_header(path: Path, label: str) -> None:
    try:
        with path.open("rb") as database_file:
            header = database_file.read(100)
    except OSError as exc:
        raise MergeError(f"cannot read {label}: {exc}") from exc
    if len(header) < 100 or header[:16] != b"SQLite format 3\x00":
        raise MergeError(f"{label} is not a SQLite 3 database")
    if header[18:20] != b"\x01\x01":
        raise MergeError(f"{label} journal mode is not DELETE")


def _normalized_sql(sql: str | None) -> str:
    if sql is None:
        return ""
    return "".join(sql.casefold().split()).removesuffix(";")


def _read_only_connection(path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(f"{path.as_uri()}?mode=ro&immutable=1", uri=True)
    connection.execute("PRAGMA query_only = ON")
    connection.execute("PRAGMA trusted_schema = OFF")
    return connection


def _check_schema(connection: sqlite3.Connection, label: str) -> None:
    if connection.execute("PRAGMA user_version").fetchone()[0] != 1:
        raise MergeError(f"{label} must use schema version 1")

    objects = {
        (row[0], row[1])
        for row in connection.execute(
            "SELECT type, name FROM sqlite_schema"
        )
    }
    expected_objects = {
        *(("table", table) for table in TABLE_COLUMNS),
        *(("index", index) for index in EXPECTED_INDEX_XINFO),
    }
    if objects != expected_objects:
        raise MergeError(f"{label} schema objects differ from schema v1")

    stored_sql = {
        row[0]: row[1]
        for row in connection.execute(
            "SELECT name, sql FROM sqlite_schema WHERE type = 'table'"
        )
    }
    for table, expected_columns in TABLE_COLUMNS.items():
        if _normalized_sql(stored_sql.get(table)) != _normalized_sql(
            CREATE_TABLE_SQL[table]
        ):
            raise MergeError(f"{label} {table} CREATE TABLE differs from schema v1")

        actual_columns = tuple(
            (row[1], row[2].upper(), row[3], row[4], row[5], row[6])
            for row in connection.execute(f"PRAGMA table_xinfo({table})")
        )
        expected_xinfo = tuple((*column, 0) for column in expected_columns)
        if actual_columns != expected_xinfo:
            raise MergeError(f"{label} {table} columns differ from schema v1")

        actual_foreign_keys = tuple(
            sorted(
                (row[2], row[3], row[4], row[5], row[6], row[7])
                for row in connection.execute(f"PRAGMA foreign_key_list({table})")
            )
        )
        if actual_foreign_keys != FOREIGN_KEYS[table]:
            raise MergeError(f"{label} {table} foreign keys differ from schema v1")

        actual_indexes = tuple(
            (row[1], row[2], row[3], row[4])
            for row in connection.execute(f"PRAGMA index_list({table})")
        )
        if actual_indexes != EXPECTED_INDEXES[table]:
            raise MergeError(f"{label} {table} indexes differ from schema v1")
        for index_name, *_ in actual_indexes:
            index_xinfo = tuple(
                (row[1], row[2], row[3], row[4], row[5])
                for row in connection.execute(f"PRAGMA index_xinfo({index_name})")
            )
            if index_xinfo != EXPECTED_INDEX_XINFO[index_name]:
                raise MergeError(f"{label} {index_name} differs from schema v1")


def _check_integrity(connection: sqlite3.Connection, label: str) -> None:
    integrity = connection.execute("PRAGMA integrity_check").fetchall()
    if integrity != [("ok",)]:
        raise MergeError(f"{label} integrity check failed: {integrity!r}")
    foreign_key_errors = connection.execute("PRAGMA foreign_key_check").fetchall()
    if foreign_key_errors:
        raise MergeError(f"{label} foreign key check failed: {foreign_key_errors!r}")


def _rows_by_id(
    connection: sqlite3.Connection,
    table: str,
    columns: tuple[str, ...],
    label: str,
) -> dict[Any, tuple[Any, ...]]:
    rows = [
        tuple(row)
        for row in connection.execute(
            f"SELECT {', '.join(columns)} FROM {table} ORDER BY id"
        )
    ]
    if any(row[0] is None for row in rows):
        raise MergeError(f"{label} {table} contains a NULL id")
    return {row[0]: row for row in rows}


def _load_rows(path: Path, label: str) -> dict[str, dict[Any, tuple[Any, ...]]]:
    _reject_sidecars(path, label)
    _check_header(path, label)
    try:
        with closing(_read_only_connection(path)) as connection:
            _check_schema(connection, label)
            _check_integrity(connection, label)
            rows = {
                table: _rows_by_id(
                    connection,
                    table,
                    tuple(column[0] for column in columns),
                    label,
                )
                for table, columns in TABLE_COLUMNS.items()
            }
            return {
                "decks": rows["decks"],
                "questions": rows["questions"],
            }
    except MergeError:
        raise
    except sqlite3.Error as exc:
        raise MergeError(f"cannot validate {label}: {exc}") from exc


def _differences(
    columns: tuple[str, ...],
    device_row: tuple[Any, ...],
    seed_row: tuple[Any, ...],
    *,
    ignored: set[str] | None = None,
) -> list[str]:
    ignored = ignored or set()
    return [
        column
        for column, device_value, seed_value in zip(columns, device_row, seed_row)
        if column not in ignored and device_value != seed_value
    ]


def _plan_additions(
    device: dict[str, dict[Any, tuple[Any, ...]]],
    seed: dict[str, dict[Any, tuple[Any, ...]]],
) -> tuple[list[tuple[Any, ...]], list[tuple[Any, ...]]]:
    added_decks: list[tuple[Any, ...]] = []
    for deck_id, seed_row in seed["decks"].items():
        device_row = device["decks"].get(deck_id)
        if device_row is None:
            added_decks.append(seed_row)
            continue
        changed = _differences(
            DECK_COLUMNS,
            device_row,
            seed_row,
            ignored=DECK_MUTABLE_COLUMNS,
        )
        if changed:
            raise MergeError(
                f"deck id conflict {deck_id!r}; differing fields: {', '.join(changed)}"
            )

    added_questions: list[tuple[Any, ...]] = []
    for question_id, seed_row in seed["questions"].items():
        device_row = device["questions"].get(question_id)
        if device_row is None:
            added_questions.append(seed_row)
            continue
        changed = _differences(QUESTION_COLUMNS, device_row, seed_row)
        if changed:
            raise MergeError(
                f"question id conflict {question_id!r}; differing fields: "
                f"{', '.join(changed)}"
            )
    return added_decks, added_questions


def _write_merged_copy(
    device_snapshot: Path,
    candidate: Path,
    added_decks: list[tuple[Any, ...]],
    added_questions: list[tuple[Any, ...]],
) -> None:
    try:
        shutil.copyfile(device_snapshot, candidate, follow_symlinks=False)
        if not added_decks and not added_questions:
            return
        with closing(sqlite3.connect(candidate)) as connection:
            connection.execute("PRAGMA foreign_keys = ON")
            if connection.execute("PRAGMA journal_mode = DELETE").fetchone()[0] != "delete":
                raise MergeError("cannot set merged database journal mode to DELETE")
            connection.execute("BEGIN IMMEDIATE")
            try:
                connection.executemany(
                    f"INSERT INTO decks ({', '.join(DECK_COLUMNS)}) "
                    f"VALUES ({', '.join('?' for _ in DECK_COLUMNS)})",
                    added_decks,
                )
                connection.executemany(
                    f"INSERT INTO questions ({', '.join(QUESTION_COLUMNS)}) "
                    f"VALUES ({', '.join('?' for _ in QUESTION_COLUMNS)})",
                    added_questions,
                )
                _check_integrity(connection, "merged database")
                connection.commit()
            except BaseException:
                if connection.in_transaction:
                    connection.rollback()
                raise
    except MergeError:
        raise
    except (OSError, sqlite3.Error) as exc:
        raise MergeError(f"cannot merge databases: {exc}") from exc


def _validate_paths(
    device_db: Path,
    seed_db: Path,
    output: Path,
) -> tuple[Path, Path, Path]:
    paths = tuple(_absolute(path) for path in (device_db, seed_db, output))
    device_db, seed_db, output = paths
    for path, label in (
        (device_db, "device database"),
        (seed_db, "seed database"),
        (output, "output database"),
    ):
        if path.is_symlink():
            raise MergeError(f"{label} path aliases are not allowed: {path}")
    for path, label in ((device_db, "device database"), (seed_db, "seed database")):
        if not path.is_file():
            raise MergeError(f"{label} does not exist: {path}")
    if os.path.lexists(output) and not output.is_file():
        raise MergeError(f"output database must be a regular file: {output}")
    if not output.parent.is_dir():
        raise MergeError(f"output directory does not exist: {output.parent}")

    existing = [path for path in paths if os.path.lexists(path)]
    identities = [(path.stat().st_dev, path.stat().st_ino) for path in existing]
    if len(set(identities)) != len(identities):
        raise MergeError("device, seed, and output paths must be distinct")
    return device_db, seed_db, output


@contextmanager
def _private_staging(parent: Path, warnings: list[str]) -> Iterator[Path]:
    staging: Path | None = None
    try:
        staging = Path(tempfile.mkdtemp(prefix=".merge-course-db-", dir=parent))
        os.chmod(staging, 0o700)
        if stat.S_IMODE(staging.stat().st_mode) != 0o700:
            raise MergeError("private staging directory mode is not 0700")
        yield staging
    except BaseException as operation_error:
        if isinstance(operation_error, RecoveryError):
            raise
        if staging is not None and os.path.lexists(staging):
            try:
                shutil.rmtree(staging)
            except OSError as cleanup_error:
                raise MergeError(
                    f"{operation_error}; staging cleanup failed: {cleanup_error}"
                ) from operation_error
        raise
    else:
        if staging is not None and os.path.lexists(staging):
            try:
                shutil.rmtree(staging)
            except OSError as cleanup_error:
                try:
                    os.chmod(staging, 0o700)
                except OSError:
                    pass
                warnings.append(
                    "private staging cleanup failed; stop deployment and remove "
                    f"preserved 0700 staging at {staging}: {cleanup_error}"
                )


def _snapshot_inputs(
    device_db: Path,
    seed_db: Path,
    staging: Path,
) -> tuple[Path, Path]:
    device_snapshot = staging / "device.snapshot.db"
    seed_snapshot = staging / "seed.snapshot.db"
    inputs = (
        (device_db, "device database"),
        (seed_db, "seed database"),
    )
    fingerprints: dict[Path, tuple[int, int, int, int, int]] = {}
    for path, label in inputs:
        _reject_sidecars(path, label)
        fingerprints[path] = _file_fingerprint(path, label)
    try:
        shutil.copyfile(device_db, device_snapshot, follow_symlinks=False)
        shutil.copyfile(seed_db, seed_snapshot, follow_symlinks=False)
    except OSError as exc:
        raise MergeError(f"cannot snapshot input databases: {exc}") from exc
    for path, label in inputs:
        _reject_sidecars(path, label)
        if _file_fingerprint(path, label) != fingerprints[path]:
            raise MergeError(f"{label} changed while being copied")
    for snapshot, source, label in (
        (device_snapshot, device_db, "device database snapshot"),
        (seed_snapshot, seed_db, "seed database snapshot"),
    ):
        if _file_fingerprint(snapshot, label)[2] != fingerprints[source][2]:
            raise MergeError(f"{label} size differs from its source")
    return device_snapshot, seed_snapshot


def _install_output(candidate: Path, output: Path, staging: Path) -> None:
    backup = staging / "previous-output"
    had_output = os.path.lexists(output)
    replaced = False
    try:
        _reject_sidecars(output, "output database")
        if had_output:
            os.link(output, backup, follow_symlinks=False)
        os.replace(candidate, output)
        replaced = True
        try:
            _reject_sidecars(output, "output database")
        except _SidecarError as sidecar_error:
            evidence = (
                f"recovery backup: {backup}"
                if had_output
                else f"recovery staging: {staging}"
            )
            raise RecoveryError(
                f"{sidecar_error}; current file set preserved; {evidence}"
            ) from sidecar_error
    except RecoveryError:
        raise
    except BaseException as operation_error:
        if replaced:
            try:
                if had_output:
                    os.replace(backup, output)
                else:
                    output.unlink(missing_ok=True)
            except OSError as rollback_error:
                raise RecoveryError(
                    f"{operation_error}; output rollback failed: {rollback_error}; "
                    f"recovery backup: {backup}"
                ) from operation_error
        raise


def merge_databases(device_db: Path, seed_db: Path, output: Path) -> dict[str, Any]:
    try:
        device_db, seed_db, output = _validate_paths(device_db, seed_db, output)
        for path, label in (
            (device_db, "device database"),
            (seed_db, "seed database"),
            (output, "output database"),
        ):
            _reject_sidecars(path, label)

        warnings: list[str] = []
        with _private_staging(output.parent, warnings) as staging:
            device_snapshot, seed_snapshot = _snapshot_inputs(
                device_db,
                seed_db,
                staging,
            )
            device_rows = _load_rows(device_snapshot, "device database")
            seed_rows = _load_rows(seed_snapshot, "seed database")
            added_decks, added_questions = _plan_additions(device_rows, seed_rows)

            candidate = staging / "merged.db"
            _write_merged_copy(
                device_snapshot,
                candidate,
                added_decks,
                added_questions,
            )
            _load_rows(candidate, "merged database")
            _install_output(candidate, output, staging)

            result: dict[str, Any] = {
                "ok": True,
                "changed": bool(added_decks or added_questions),
                "added_decks": len(added_decks),
                "added_questions": len(added_questions),
                "output": str(output),
            }
        if warnings:
            result["warnings"] = warnings
        return result
    except MergeError:
        raise
    except (OSError, sqlite3.Error) as exc:
        raise MergeError(f"database merge failed: {exc}") from exc


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--device-db", required=True, type=Path)
    parser.add_argument("--seed-db", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        result = merge_databases(args.device_db, args.seed_db, args.output)
    except MergeError as exc:
        print(
            json.dumps(
                {"ok": False, "error": str(exc)},
                ensure_ascii=False,
                separators=(",", ":"),
            ),
            file=sys.stderr,
        )
        return 1
    print(json.dumps(result, ensure_ascii=False, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
