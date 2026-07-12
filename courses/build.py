#!/usr/bin/env python3
"""Validate course sources and build the app's schema-v1 seed database."""

from __future__ import annotations

import argparse
import json
import os
import re
import sqlite3
import sys
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any


BASE_CREATED_AT = 1_783_699_200_000
QUESTIONS_PER_DECK = 5
COURSE_SPECS = (
    {
        "course_file": "agent-harness.json",
        "prefix": "AG",
        "lab_file": "agent.md",
        "lesson_count": 14,
        "ref": "shareAI-lab/learn-claude-code@a9cafe953aa714f9cb1171f217d96bd2734bbcc7",
        "snapshot": "2026-07-11",
    },
    {
        "course_file": "codex-harness.json",
        "prefix": "CX",
        "lab_file": "codex.md",
        "lesson_count": 10,
        "ref": "codex-cli-0.144.1",
        "snapshot": "2026-07-11",
    },
    {
        "course_file": "fastapi1-project.json",
        "prefix": "FA",
        "lab_file": "fastapi1.md",
        "lesson_count": 12,
        "ref": "fastapi1@b21b6e4",
        "snapshot": "2026-07-11",
    },
)

# Backward-compatible views; COURSE_SPECS is the only release specification source.
COURSE_FILES = tuple(spec["course_file"] for spec in COURSE_SPECS)
LAB_FILES = {spec["prefix"]: spec["lab_file"] for spec in COURSE_SPECS}
EXPECTED_DECKS = {spec["prefix"]: spec["lesson_count"] for spec in COURSE_SPECS}
EXPECTED_SOURCES = {spec["prefix"]: spec["ref"] for spec in COURSE_SPECS}

COURSE_SPEC_FIELDS = {
    "course_file",
    "prefix",
    "lab_file",
    "lesson_count",
    "ref",
    "snapshot",
}
DECK_FIELDS = {
    "id",
    "code",
    "title",
    "order",
    "lab_ref",
    "source_text",
    "questions",
}
QUESTION_TYPES = {
    "multiple_choice",
    "fill_blank",
    "true_false",
    "matching",
    "ordering",
}
BASE_QUESTION_FIELDS = {
    "id",
    "type",
    "content",
    "options",
    "answer",
    "explanation",
}

SENSITIVE_PATTERNS = (
    re.compile(r"\bsk-[A-Za-z0-9_-]{16,}"),
    re.compile(r"\btvly-[A-Za-z0-9_-]{16,}"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}"),
    re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b"),
    re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{20,}"),
    re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b"),
    re.compile(r"\bBearer\s+[A-Za-z0-9._~+/=-]{16,}", re.IGNORECASE),
    re.compile(
        r"\b[A-Za-z][A-Za-z0-9+.-]*://[^\s/@]+(?::[^\s/@]*)?@",
        re.IGNORECASE,
    ),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"/Users/[A-Za-z0-9._-]+"),
    re.compile(r"\bTAVILY_API_KEY\s*=\s*['\"](?!<redacted>|\$)[^'\"]+['\"]", re.IGNORECASE),
    re.compile(r"\bexperimental_bearer_token\s*=\s*['\"](?!<redacted>|\$)[^'\"]+['\"]", re.IGNORECASE),
)

EXPECTED_TABLE_COLUMNS = {
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
EXPECTED_FOREIGN_KEYS = {
    "decks": (),
    "questions": (("decks", "deck_id", "id", "NO ACTION", "CASCADE", "NONE"),),
    "study_records": (("decks", "deck_id", "id", "NO ACTION", "CASCADE", "NONE"),),
    "user_stats": (),
}


class ValidationError(ValueError):
    pass


def _json_object_without_duplicate_keys(
    pairs: list[tuple[str, Any]],
) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValidationError(f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def reject_nul(value: Any, label: str) -> None:
    if isinstance(value, str):
        if "\x00" in value:
            raise ValidationError(f"{label} contains an actual NUL character")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            reject_nul(key, f"{label} key ({type(key).__name__})")
            key_label = key if isinstance(key, str) else f"<{type(key).__name__}>"
            reject_nul(item, f"{label}.{key_label}")
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            reject_nul(item, f"{label}[{index}]")


def scan_sensitive(text: str, label: str) -> None:
    for pattern in SENSITIVE_PATTERNS:
        match = pattern.search(text)
        if match:
            raise ValidationError(
                f"{label} contains sensitive or machine-specific text matching {pattern.pattern!r}"
            )


def _require(mapping: dict[str, Any], key: str, label: str) -> Any:
    if key not in mapping:
        raise ValidationError(f"{label} is missing {key!r}")
    return mapping[key]


def _validated_course_specs() -> tuple[dict[str, Any], ...]:
    if not isinstance(COURSE_SPECS, tuple) or not COURSE_SPECS:
        raise ValidationError("COURSE_SPECS must be a non-empty ordered tuple")

    seen: dict[str, set[str]] = {
        "course_file": set(),
        "prefix": set(),
        "lab_file": set(),
    }
    for index, spec in enumerate(COURSE_SPECS, start=1):
        label = f"COURSE_SPECS item {index}"
        if not isinstance(spec, dict) or set(spec) != COURSE_SPEC_FIELDS:
            raise ValidationError(
                f"{label} fields must be {', '.join(sorted(COURSE_SPEC_FIELDS))}"
            )
        lesson_count = spec["lesson_count"]
        if (
            not isinstance(lesson_count, int)
            or isinstance(lesson_count, bool)
            or lesson_count <= 0
        ):
            raise ValidationError(f"{label} lesson_count must be a positive integer")
        if not isinstance(spec["prefix"], str) or not re.fullmatch(
            r"[A-Z]{2}", spec["prefix"]
        ):
            raise ValidationError(f"{label} prefix must contain two uppercase letters")
        for key in ("course_file", "lab_file", "ref", "snapshot"):
            if not isinstance(spec[key], str) or not spec[key].strip():
                raise ValidationError(f"{label} {key} must be non-empty text")
        for key, values in seen.items():
            value = spec[key]
            if value in values:
                raise ValidationError(f"{label} has duplicate {key} {value!r}")
            values.add(value)
    return COURSE_SPECS


def _text_list(value: Any, label: str) -> list[str]:
    if not isinstance(value, list) or any(
        not isinstance(item, str) or not item.strip() for item in value
    ):
        raise ValidationError(f"{label} must be a list of non-empty texts")
    if any(item != item.strip() for item in value):
        raise ValidationError(f"{label} items must not have surrounding whitespace")
    return value


def _explanation_sections(
    explanation: Any,
    question_type: str,
    label: str,
) -> tuple[str, ...]:
    if not isinstance(explanation, str):
        raise ValidationError(
            f"{label} explanation must contain 结论、依据、实践 exactly once"
        )
    if any(
        explanation.count(marker) != 1 for marker in ("结论：", "依据：", "实践：")
    ):
        raise ValidationError(
            f"{label} explanation must contain 结论、依据、实践 exactly once"
        )

    if question_type == "multiple_choice":
        if explanation.count("错误选项：") != 1:
            raise ValidationError(
                f"{label} explanation wrong option section must appear exactly once"
            )
        pattern = r"结论：(.*?)\n依据：(.*?)\n错误选项：(.*?)\n实践：(.*)"
    else:
        if "错误选项：" in explanation:
            raise ValidationError(
                f"{label} non-multiple-choice explanation must not contain 错误选项"
            )
        pattern = r"结论：(.*?)\n依据：(.*?)\n实践：(.*)"

    match = re.fullmatch(pattern, explanation, re.DOTALL)
    if match is None:
        raise ValidationError(f"{label} explanation sections must be ordered")
    sections = match.groups()
    if any(not section.strip() for section in sections):
        raise ValidationError(f"{label} explanation sections must be non-empty")
    return sections


def _validate_question_contract(
    question: dict[str, Any],
    label: str,
) -> int | None:
    question_type = _require(question, "type", label)
    if not isinstance(question_type, str):
        raise ValidationError(f"{label} type must be text")
    if question_type not in QUESTION_TYPES:
        raise ValidationError(f"{label} has unsupported type {question_type!r}")

    expected_fields = set(BASE_QUESTION_FIELDS)
    if question_type == "matching":
        expected_fields.update(("match_left", "match_right"))
    if set(question) != expected_fields:
        raise ValidationError(
            f"{label} fields for {question_type} must be "
            f"{', '.join(sorted(expected_fields))}"
        )

    content = _require(question, "content", label)
    if not isinstance(content, str):
        raise ValidationError(
            f"{label} content must contain a non-empty course tag and question"
        )
    tagged_content = re.fullmatch(r"\[([^\[\]]+)\](.*)", content, re.DOTALL)
    if tagged_content is None or any(
        not part.strip() for part in tagged_content.groups()
    ):
        raise ValidationError(
            f"{label} content must contain a non-empty course tag and question"
        )
    options = _text_list(_require(question, "options", label), f"{label} options")
    answer = _require(question, "answer", label)
    if not isinstance(answer, str) or not answer.strip():
        raise ValidationError(f"{label} answer must be non-empty text")

    answer_position: int | None = None
    if question_type == "multiple_choice":
        if len(options) != 4 or len(set(options)) != 4:
            raise ValidationError(f"{label} options must contain four unique texts")
        if answer not in options:
            raise ValidationError(f"{label} answer must exactly match one option")
        answer_position = options.index(answer)
    elif question_type == "fill_blank":
        if options:
            raise ValidationError(f"{label} fill_blank options must be []")
        if content.count("___") != 1:
            raise ValidationError(f"{label} content must contain exactly one ___")
    elif question_type == "true_false":
        if options != ["正确", "错误"]:
            raise ValidationError(
                f"{label} true_false options must be ['正确', '错误']"
            )
        if answer not in options:
            raise ValidationError(f"{label} true_false answer must be 正确 or 错误")
    elif question_type == "matching":
        if options:
            raise ValidationError(f"{label} matching options must be []")
        match_left = _text_list(
            _require(question, "match_left", label), f"{label} match_left"
        )
        match_right = _text_list(
            _require(question, "match_right", label), f"{label} match_right"
        )
        if not match_left or len(match_left) != len(match_right):
            raise ValidationError(
                f"{label} matching columns must be equal non-empty lists"
            )
        if len(set(match_left)) != len(match_left) or len(set(match_right)) != len(
            match_right
        ):
            raise ValidationError(f"{label} matching columns must each be unique")

        encoded_pairs = answer.split("|")
        if len(encoded_pairs) != len(match_left):
            raise ValidationError(
                f"{label} matching answer must follow match_left order"
            )
        mapped_right: list[str] = []
        for left, encoded_pair in zip(match_left, encoded_pairs):
            candidates = [
                (candidate_left, candidate_right)
                for candidate_left in match_left
                for candidate_right in match_right
                if encoded_pair == f"{candidate_left}-{candidate_right}"
            ]
            if len(candidates) != 1:
                raise ValidationError(
                    f"{label} matching answer pairs must be unambiguous"
                )
            candidate_left, candidate_right = candidates[0]
            if candidate_left != left:
                raise ValidationError(
                    f"{label} matching answer must follow match_left order"
                )
            mapped_right.append(candidate_right)
        if Counter(mapped_right) != Counter(match_right):
            raise ValidationError(
                f"{label} matching answer must exactly cover match_right"
            )
    else:
        if not options:
            raise ValidationError(f"{label} ordering options must be non-empty")
        correct_order = answer.split("|")
        if len(correct_order) != len(options) or Counter(correct_order) != Counter(
            options
        ):
            raise ValidationError(
                f"{label} ordering answer must be a complete permutation of options"
            )
        if correct_order == options:
            raise ValidationError(
                f"{label} ordering initial order must differ from the correct order"
            )

    explanation = _require(question, "explanation", label)
    explanation_sections = _explanation_sections(explanation, question_type, label)
    if question_type == "multiple_choice":
        wrong_section = explanation_sections[2]
        explained_options: list[tuple[str, str]] = []
        for entry in wrong_section.split("；"):
            match = re.fullmatch(r"([ABCD])：([^；\n]*)", entry)
            if match is None or not match.group(2).strip():
                raise ValidationError(
                    f"{label} wrong option explanations must have non-empty text"
                )
            explained_options.append((match.group(1), match.group(2)))
        answer_letter = "ABCD"[answer_position]
        expected_letters = [letter for letter in "ABCD" if letter != answer_letter]
        if Counter(letter for letter, _text in explained_options) != Counter(
            expected_letters
        ):
            raise ValidationError(
                f"{label} explanation must address each wrong option exactly once"
            )
    return answer_position


def validate_course(
    course: dict[str, Any],
    lab_text: str,
    *,
    expected_questions_per_deck: int | None = None,
) -> Counter[int]:
    reject_nul(course, "course source")
    reject_nul(lab_text, "lab manual")
    if not isinstance(course, dict):
        raise ValidationError("course source must be a JSON object")
    if set(course) != {"course", "source", "decks"}:
        raise ValidationError("course source fields must be course, source, and decks")

    metadata = _require(course, "course", "course source")
    source = _require(course, "source", "course source")
    decks = _require(course, "decks", "course source")
    if (
        not isinstance(metadata, dict)
        or not isinstance(source, dict)
        or not isinstance(decks, list)
    ):
        raise ValidationError(
            "course metadata and source must be objects and decks must be a list"
        )
    if set(metadata) != {"id", "prefix", "title"}:
        raise ValidationError("course metadata fields must be id, prefix, and title")
    if set(source) != {"kind", "ref", "snapshot"}:
        raise ValidationError("course source fields must be kind, ref, and snapshot")

    prefix = str(_require(metadata, "prefix", "course metadata"))
    if not re.fullmatch(r"[A-Z]{2}", prefix):
        raise ValidationError(f"invalid course prefix {prefix!r}")
    for key in ("id", "title"):
        value = _require(metadata, key, "course metadata")
        if not isinstance(value, str) or not value.strip():
            raise ValidationError(f"course metadata {key!r} must be non-empty text")
    for key in ("kind", "ref", "snapshot"):
        value = _require(source, key, "course source metadata")
        if not isinstance(value, str) or not value.strip():
            raise ValidationError(f"course source {key!r} must be non-empty text")

    answer_positions: Counter[int] = Counter()
    seen_ids: set[str] = set()
    expected_orders = list(range(1, len(decks) + 1))
    actual_orders: list[int] = []
    for deck_number, deck in enumerate(decks, start=1):
        if not isinstance(deck, dict):
            raise ValidationError(f"{prefix} deck {deck_number} must be an object")
        if set(deck) != DECK_FIELDS:
            raise ValidationError(
                f"{prefix} deck {deck_number} fields must be "
                f"{', '.join(sorted(DECK_FIELDS))}"
            )
        order = deck.get("order")
        if not isinstance(order, int) or isinstance(order, bool):
            raise ValidationError(
                f"{prefix} deck {deck_number} order must be a non-boolean integer"
            )
        actual_orders.append(order)
    if actual_orders != expected_orders:
        raise ValidationError(
            f"{prefix} deck order must be contiguous and sorted: {expected_orders}"
        )

    for deck in decks:
        order = deck["order"]
        code = f"{prefix}{order:02d}"
        label = f"{prefix} deck {code}"
        expected_deck_id = f"course-{prefix.lower()}-{order:02d}"
        if _require(deck, "id", label) != expected_deck_id:
            raise ValidationError(f"{label} id must be {expected_deck_id!r}")
        if _require(deck, "code", label) != code:
            raise ValidationError(f"{label} code must be {code!r}")
        if _require(deck, "lab_ref", label) != code:
            raise ValidationError(f"{label} lab_ref must be {code!r}")
        title = _require(deck, "title", label)
        if not isinstance(title, str) or not title.startswith(f"{code} "):
            raise ValidationError(f"{label} title must start with {code!r}")
        if len(title) > 20:
            raise ValidationError(f"{label} title is too long for the existing path UI")
        source_text = _require(deck, "source_text", label)
        if not isinstance(source_text, str) or not source_text.strip():
            raise ValidationError(f"{label} source_text must be non-empty text")
        if not re.search(rf"^##\s+{re.escape(code)}(?:\s|$)", lab_text, re.MULTILINE):
            raise ValidationError(f"lab manual is missing a heading for {code}")

        questions = _require(deck, "questions", label)
        if not isinstance(questions, list) or not questions:
            raise ValidationError(f"{label} questions must be a non-empty list")
        if (
            expected_questions_per_deck is not None
            and len(questions) != expected_questions_per_deck
        ):
            raise ValidationError(
                f"{label} must contain exactly {expected_questions_per_deck} questions"
            )

        for question_number, question in enumerate(questions, start=1):
            qlabel = f"{code} question {question_number}"
            if not isinstance(question, dict):
                raise ValidationError(f"{qlabel} must be an object")
            expected_question_id = f"{expected_deck_id}-q{question_number:02d}"
            question_id = _require(question, "id", qlabel)
            if question_id != expected_question_id:
                raise ValidationError(f"{qlabel} id must be {expected_question_id!r}")
            if question_id in seen_ids:
                raise ValidationError(f"duplicate question id {question_id!r}")
            seen_ids.add(question_id)
            answer_position = _validate_question_contract(
                question,
                qlabel,
            )
            if answer_position is not None:
                answer_positions[answer_position] += 1

    scan_sensitive(json.dumps(course, ensure_ascii=False), f"{prefix} course")
    scan_sensitive(lab_text, f"{prefix} lab manual")
    return answer_positions


def load_release(course_dir: Path) -> tuple[list[dict[str, Any]], dict[str, str]]:
    courses: list[dict[str, Any]] = []
    labs: dict[str, str] = {}
    for spec in _validated_course_specs():
        path = course_dir / spec["course_file"]
        try:
            raw = path.read_text(encoding="utf-8")
            payload = json.loads(
                raw,
                object_pairs_hook=_json_object_without_duplicate_keys,
            )
        except FileNotFoundError as exc:
            raise ValidationError(f"missing course file: {path}") from exc
        except json.JSONDecodeError as exc:
            raise ValidationError(f"invalid JSON in {path}: {exc}") from exc
        scan_sensitive(raw, str(path))
        courses.append(payload)
        lab_path = course_dir / "labs" / spec["lab_file"]
        try:
            labs[spec["prefix"]] = lab_path.read_text(encoding="utf-8")
        except FileNotFoundError as exc:
            raise ValidationError(f"missing lab manual: {lab_path}") from exc
    return courses, labs


def validate_release(courses: list[dict[str, Any]], labs: dict[str, str]) -> None:
    specs = _validated_course_specs()
    expected_prefixes = [spec["prefix"] for spec in specs]
    prefixes: list[str] = []
    for course_number, course in enumerate(courses, start=1):
        if not isinstance(course, dict):
            raise ValidationError(
                f"release course {course_number} must be a JSON object"
            )
        metadata = course.get("course")
        if not isinstance(metadata, dict):
            raise ValidationError(
                f"release course {course_number} metadata must be an object"
            )
        prefix = metadata.get("prefix")
        if not isinstance(prefix, str):
            raise ValidationError(
                f"release course {course_number} prefix must be text"
            )
        prefixes.append(prefix)
    if prefixes != expected_prefixes:
        raise ValidationError(
            f"release course order must be {', '.join(expected_prefixes)}"
        )

    total_positions: Counter[int] = Counter()
    seen_ids: set[str] = set()
    total_decks = 0
    total_questions = 0
    for course, spec in zip(courses, specs):
        prefix = spec["prefix"]
        lab_text = labs.get(prefix)
        if not isinstance(lab_text, str):
            raise ValidationError(f"release is missing lab manual for {prefix}")
        total_positions.update(
            validate_course(
                course,
                lab_text,
                expected_questions_per_deck=QUESTIONS_PER_DECK,
            )
        )

        decks = course["decks"]
        if len(decks) != spec["lesson_count"]:
            raise ValidationError(
                f"{prefix} must contain exactly {spec['lesson_count']} decks"
            )
        source = course["source"]
        if source["ref"] != spec["ref"]:
            raise ValidationError(
                f"{prefix} source ref must be {spec['ref']!r}"
            )
        if source["snapshot"] != spec["snapshot"]:
            raise ValidationError(
                f"{prefix} source snapshot must be {spec['snapshot']!r}"
            )
        for deck in decks:
            if deck["id"] in seen_ids:
                raise ValidationError(f"duplicate deck id {deck['id']!r}")
            seen_ids.add(deck["id"])
            total_decks += 1
            total_questions += len(deck["questions"])

    expected_decks = sum(spec["lesson_count"] for spec in specs)
    expected_questions = expected_decks * QUESTIONS_PER_DECK
    if total_decks != expected_decks or total_questions != expected_questions:
        raise ValidationError(
            f"release must contain {expected_decks} decks and {expected_questions} "
            f"questions, got {total_decks} and {total_questions}"
        )
    position_counts = [total_positions[index] for index in range(4)]
    if max(position_counts) - min(position_counts) > 1:
        raise ValidationError(
            "multiple-choice answer positions must differ by at most one, "
            f"got A/B/C/D={position_counts}"
        )


def _release_database_rows(
    courses: list[dict[str, Any]],
) -> tuple[list[tuple[Any, ...]], list[tuple[Any, ...]]]:
    deck_rows: list[tuple[Any, ...]] = []
    question_rows: list[tuple[Any, ...]] = []
    sequence = 0
    for course in courses:
        for deck in sorted(course["decks"], key=lambda item: item["order"]):
            created_at = BASE_CREATED_AT - sequence * 1_000
            questions = deck["questions"]
            deck_rows.append(
                (
                    deck["id"],
                    deck["title"],
                    deck["source_text"],
                    None,
                    len(questions),
                    0,
                    created_at,
                    created_at,
                )
            )
            for question in questions:
                question_rows.append(
                    (
                        question["id"],
                        deck["id"],
                        question["type"],
                        question["content"],
                        json.dumps(
                            question["options"],
                            ensure_ascii=False,
                            separators=(",", ":"),
                        ),
                        question["answer"],
                        question["explanation"],
                        json.dumps(
                            question.get("match_left", []),
                            ensure_ascii=False,
                            separators=(",", ":"),
                        ),
                        json.dumps(
                            question.get("match_right", []),
                            ensure_ascii=False,
                            separators=(",", ":"),
                        ),
                    )
                )
            sequence += 1
    return deck_rows, question_rows


def _valid_existing_deck_timestamps(path: Path) -> dict[str, int] | None:
    if not path.is_file():
        return None

    connection: sqlite3.Connection | None = None
    try:
        uri = path.resolve().as_uri() + "?mode=ro&immutable=1"
        connection = sqlite3.connect(uri, uri=True)
        deck_count = connection.execute("SELECT COUNT(*) FROM decks").fetchone()[0]
        question_count = connection.execute(
            "SELECT COUNT(*) FROM questions"
        ).fetchone()[0]
        timestamps = dict(connection.execute("SELECT id, created_at FROM decks"))
        if any(not isinstance(created_at, int) for created_at in timestamps.values()):
            return None
        connection.close()
        connection = None
        check_database(
            path,
            expected_decks=deck_count,
            expected_questions=question_count,
        )
    except (OSError, sqlite3.DatabaseError, ValidationError):
        return None
    finally:
        if connection is not None:
            connection.close()
    return timestamps


def build_database(courses: list[dict[str, Any]], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    for suffix in ("-wal", "-shm", "-journal"):
        sidecar = output.with_name(output.name + suffix)
        if sidecar.exists():
            raise ValidationError(
                f"refusing to replace database with existing sidecar: {sidecar.name}"
            )

    deck_rows, question_rows = _release_database_rows(courses)
    existing_timestamps = _valid_existing_deck_timestamps(output)
    if existing_timestamps is not None:
        missing = sorted(existing_timestamps.keys() - {row[0] for row in deck_rows})
        if missing:
            raise ValidationError(
                "existing deck IDs must not disappear from a new release; "
                f"append new courses after existing specs: {missing}"
            )
        drift = [
            (deck_id, existing_timestamps[deck_id], created_at)
            for deck_id, *_values, created_at, _updated_at in deck_rows
            if deck_id in existing_timestamps
            and existing_timestamps[deck_id] != created_at
        ]
        if drift:
            raise ValidationError(
                "existing deck created_at values are immutable; "
                f"append new courses after existing specs: {drift}"
            )

    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{output.name}.",
        suffix=".tmp",
        dir=output.parent,
    )
    os.close(descriptor)
    temporary = Path(temporary_name)
    connection: sqlite3.Connection | None = None
    try:
        connection = sqlite3.connect(temporary)
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA journal_mode = DELETE")
        connection.executescript(
            """
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
        )
        connection.execute(
            """
            INSERT INTO user_stats
              (id, xp, streak, hearts, max_hearts, last_study_date, daily_goal, today_xp)
            VALUES (1, 0, 0, 99, 99, ?, 50, 0)
            """,
            (BASE_CREATED_AT,),
        )

        connection.executemany(
            """
            INSERT INTO decks
              (id, title, source_text, source_image, question_count,
               mastery_level, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            deck_rows,
        )
        connection.executemany(
            """
            INSERT INTO questions
              (id, deck_id, type, content, options, answer,
               explanation, match_left, match_right)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            question_rows,
        )

        connection.execute("PRAGMA user_version = 1")
        connection.commit()
        integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
        if integrity != "ok":
            raise ValidationError(f"generated database integrity check failed: {integrity}")
        connection.close()
        connection = None

        check_database(
            temporary,
            expected_decks=len(deck_rows),
            expected_questions=len(question_rows),
            expected_courses=courses,
        )
        os.replace(temporary, output)
    finally:
        if connection is not None:
            connection.close()
        temporary.unlink(missing_ok=True)
        for suffix in ("-wal", "-shm", "-journal"):
            temporary.with_name(temporary.name + suffix).unlink(missing_ok=True)


def check_database(
    path: Path,
    *,
    expected_decks: int | None = None,
    expected_questions: int | None = None,
    expected_courses: list[dict[str, Any]] | None = None,
) -> dict[str, int]:
    if not path.is_file():
        raise ValidationError(f"database does not exist: {path}")

    if expected_courses is not None:
        course_deck_count = sum(len(course["decks"]) for course in expected_courses)
        course_question_count = sum(
            len(deck["questions"])
            for course in expected_courses
            for deck in course["decks"]
        )
    else:
        course_deck_count = sum(
            spec["lesson_count"] for spec in _validated_course_specs()
        )
        course_question_count = course_deck_count * QUESTIONS_PER_DECK
    if expected_decks is None:
        expected_decks = course_deck_count
    if expected_questions is None:
        expected_questions = course_question_count

    sidecars = [
        path.with_name(path.name + suffix)
        for suffix in ("-wal", "-shm", "-journal")
    ]
    for sidecar in sidecars:
        if sidecar.exists():
            raise ValidationError(f"database sidecar must not exist: {sidecar.name}")

    with path.open("rb") as database_file:
        header = database_file.read(20)
    if len(header) != 20 or header[:16] != b"SQLite format 3\x00":
        raise ValidationError("database is not a SQLite 3 file")
    if header[18:20] != b"\x01\x01":
        raise ValidationError("database journal_mode must be DELETE")

    uri = path.resolve().as_uri() + "?mode=ro&immutable=1"
    connection = sqlite3.connect(uri, uri=True)
    try:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }
        expected_tables = {"decks", "questions", "study_records", "user_stats"}
        if tables != expected_tables:
            raise ValidationError(f"database tables differ: {sorted(tables)}")
        extra_schema_objects = connection.execute(
            """
            SELECT type, name
            FROM sqlite_master
            WHERE type != 'table' AND sql IS NOT NULL
            ORDER BY type, name
            """
        ).fetchall()
        if extra_schema_objects:
            raise ValidationError(
                f"database has unexpected schema objects: {extra_schema_objects}"
            )
        for table in sorted(expected_tables):
            columns = tuple(
                (row[1], row[2], row[3], row[4], row[5])
                for row in connection.execute(f"PRAGMA table_info({table})")
            )
            if columns != EXPECTED_TABLE_COLUMNS[table]:
                raise ValidationError(f"database schema differs for table {table}")
            foreign_keys = tuple(
                (row[2], row[3], row[4], row[5], row[6], row[7])
                for row in connection.execute(f"PRAGMA foreign_key_list({table})")
            )
            if foreign_keys != EXPECTED_FOREIGN_KEYS[table]:
                raise ValidationError(f"database schema foreign keys differ for table {table}")
            for column, column_type, *_ in EXPECTED_TABLE_COLUMNS[table]:
                if column_type != "TEXT":
                    continue
                contains_nul = connection.execute(
                    f'SELECT 1 FROM "{table}" '
                    f'WHERE instr("{column}", char(0)) > 0 LIMIT 1'
                ).fetchone()
                if contains_nul:
                    raise ValidationError(
                        f"database {table}.{column} contains an actual NUL character"
                    )
        if connection.execute("PRAGMA user_version").fetchone()[0] != 1:
            raise ValidationError("database user_version must be 1")
        if connection.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            raise ValidationError("database integrity_check failed")
        foreign_key_errors = connection.execute("PRAGMA foreign_key_check").fetchall()
        if foreign_key_errors:
            raise ValidationError(f"database foreign_key_check failed: {foreign_key_errors}")

        deck_count = connection.execute("SELECT COUNT(*) FROM decks").fetchone()[0]
        question_count = connection.execute("SELECT COUNT(*) FROM questions").fetchone()[0]
        if (deck_count, question_count) != (expected_decks, expected_questions):
            raise ValidationError(
                f"database counts must be {expected_decks}/{expected_questions}, got {deck_count}/{question_count}"
            )
        drift = connection.execute(
            """
            SELECT decks.id, decks.question_count, COUNT(questions.id)
            FROM decks
            LEFT JOIN questions ON questions.deck_id = decks.id
            GROUP BY decks.id
            HAVING decks.question_count != COUNT(questions.id)
            """
        ).fetchall()
        if drift:
            raise ValidationError(f"database question_count drift: {drift}")
        stats_rows = connection.execute(
            """
            SELECT id, xp, streak, hearts, max_hearts, last_study_date,
                   daily_goal, today_xp
            FROM user_stats
            ORDER BY id
            """
        ).fetchall()
        expected_stats = [(1, 0, 0, 99, 99, BASE_CREATED_AT, 50, 0)]
        if stats_rows != expected_stats:
            raise ValidationError(
                f"database initial user_stats differ: {stats_rows}"
            )
        if connection.execute("SELECT COUNT(*) FROM study_records").fetchone()[0] != 0:
            raise ValidationError("database initial study_records must be empty")
        timestamps = connection.execute(
            "SELECT created_at FROM decks ORDER BY created_at DESC"
        ).fetchall()
        if len({row[0] for row in timestamps}) != deck_count:
            raise ValidationError("deck created_at values must be unique")

        if expected_courses is not None:
            expected_deck_rows, expected_question_rows = _release_database_rows(
                expected_courses
            )
            actual_deck_rows = connection.execute(
                """
                SELECT id, title, source_text, source_image, question_count,
                       mastery_level, created_at, updated_at
                FROM decks
                ORDER BY id
                """
            ).fetchall()
            actual_question_rows = connection.execute(
                """
                SELECT id, deck_id, type, content, options, answer,
                       explanation, match_left, match_right
                FROM questions
                ORDER BY id
                """
            ).fetchall()
            if actual_deck_rows != sorted(expected_deck_rows):
                raise ValidationError("database deck content differs from course JSON")
            if actual_question_rows != sorted(expected_question_rows):
                raise ValidationError("database question content differs from course JSON")

        for row in connection.execute(
            "SELECT title, COALESCE(source_text, '') FROM decks"
        ):
            scan_sensitive("\n".join(row), "database deck")
        for row in connection.execute(
            """
            SELECT id, type, content, options, answer, explanation,
                   match_left, match_right
            FROM questions
            ORDER BY deck_id, id
            """
        ):
            (
                question_id,
                question_type,
                content,
                encoded_options,
                answer,
                explanation,
                encoded_match_left,
                encoded_match_right,
            ) = row
            scan_sensitive(
                "\n".join(
                    value or ""
                    for value in (
                        content,
                        encoded_options,
                        answer,
                        explanation,
                        encoded_match_left,
                        encoded_match_right,
                    )
                ),
                "database question",
            )
            decoded_lists: dict[str, list[str]] = {}
            for column, encoded in (
                ("options", encoded_options),
                ("match_left", encoded_match_left),
                ("match_right", encoded_match_right),
            ):
                try:
                    decoded = json.loads(encoded)
                except (json.JSONDecodeError, TypeError) as exc:
                    raise ValidationError(
                        f"database question {column} must be a JSON array"
                    ) from exc
                if not isinstance(decoded, list):
                    raise ValidationError(
                        f"database question {column} must be a JSON array"
                    )
                decoded_lists[column] = decoded

            question = {
                "id": question_id,
                "type": question_type,
                "content": content,
                "options": decoded_lists["options"],
                "answer": answer,
                "explanation": explanation,
            }
            if question_type == "matching":
                question["match_left"] = decoded_lists["match_left"]
                question["match_right"] = decoded_lists["match_right"]
            elif decoded_lists["match_left"] or decoded_lists["match_right"]:
                raise ValidationError(
                    "database non-matching question match columns must be []"
                )
            _validate_question_contract(
                question,
                f"database question {question_id}",
            )
    finally:
        connection.close()

    for sidecar in sidecars:
        if sidecar.exists():
            raise ValidationError(f"database check created sidecar: {sidecar.name}")
    return {"decks": deck_count, "questions": question_count}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="validate sources and the existing database without rebuilding it",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).resolve().parent / "dist" / "dlg_q.db",
        help="database output path",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    course_dir = Path(__file__).resolve().parent
    try:
        courses, labs = load_release(course_dir)
        validate_release(courses, labs)
        if not args.check:
            build_database(courses, args.output)
        summary = check_database(args.output, expected_courses=courses)
    except (OSError, sqlite3.DatabaseError, ValidationError) as exc:
        print(f"course build failed: {exc}", file=sys.stderr)
        return 1

    action = "checked" if args.check else "built"
    print(
        f"{action} {args.output}: {summary['decks']} decks, "
        f"{summary['questions']} questions"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
