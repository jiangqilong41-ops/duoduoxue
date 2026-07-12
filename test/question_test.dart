import 'dart:convert';

import 'package:dlg_q/data/models/question.dart';
import 'package:dlg_q/data/models/question_type.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('serializes absent matching lists as empty JSON arrays', () {
    final question = Question(
      id: 'question-1',
      deckId: 'deck-1',
      type: QuestionType.multipleChoice,
      content: 'content',
      options: const ['A', 'B'],
      answer: 'A',
    );

    final map = question.toMap();

    expect(map['match_left'], '[]');
    expect(map['match_right'], '[]');
    expect(Question.fromMap(map).matchLeft, isEmpty);
    expect(Question.fromMap(map).matchRight, isEmpty);
  });

  test('serializes list fields as NUL-safe JSON and round-trips them', () {
    final question = Question(
      id: 'question-1',
      deckId: 'deck-1',
      type: QuestionType.matching,
      content: 'content',
      options: const ['A', 'B\u0000inside', 'C', 'D'],
      answer: 'A',
      explanation: 'explanation',
      matchLeft: const ['left 1', 'left 2'],
      matchRight: const ['right 1', 'right 2'],
    );

    final map = question.toMap();

    expect(map['options'], jsonEncode(question.options));
    expect(map['match_left'], jsonEncode(question.matchLeft));
    expect(map['match_right'], jsonEncode(question.matchRight));
    expect((map['options'] as String).contains('\u0000'), isFalse);

    final restored = Question.fromMap(map);
    expect(restored.options, question.options);
    expect(restored.matchLeft, question.matchLeft);
    expect(restored.matchRight, question.matchRight);
  });

  test('reads legacy NUL-separated list fields', () {
    final question = Question.fromMap({
      'id': 'legacy-question',
      'deck_id': 'legacy-deck',
      'type': 'multiple_choice',
      'content': 'legacy content',
      'options': 'A\u0000B\u0000C\u0000D',
      'answer': 'A',
      'explanation': null,
      'match_left': 'left 1\u0000left 2',
      'match_right': 'right 1\u0000right 2',
    });

    expect(question.options, ['A', 'B', 'C', 'D']);
    expect(question.matchLeft, ['left 1', 'left 2']);
    expect(question.matchRight, ['right 1', 'right 2']);
  });

  test('rejects actual NUL characters in scalar SQLite fields', () {
    final variants = <String, Question>{
      'id': Question(
        id: 'question\u0000hidden',
        deckId: 'deck-1',
        type: QuestionType.multipleChoice,
        content: 'content',
        options: const ['A', 'B', 'C', 'D'],
        answer: 'A',
      ),
      'deck_id': Question(
        id: 'question-1',
        deckId: 'deck\u0000hidden',
        type: QuestionType.multipleChoice,
        content: 'content',
        options: const ['A', 'B', 'C', 'D'],
        answer: 'A',
      ),
      'content': Question(
        id: 'question-1',
        deckId: 'deck-1',
        type: QuestionType.multipleChoice,
        content: 'content\u0000hidden',
        options: const ['A', 'B', 'C', 'D'],
        answer: 'A',
      ),
      'answer': Question(
        id: 'question-1',
        deckId: 'deck-1',
        type: QuestionType.multipleChoice,
        content: 'content',
        options: const ['A\u0000hidden', 'B', 'C', 'D'],
        answer: 'A\u0000hidden',
      ),
      'explanation': Question(
        id: 'question-1',
        deckId: 'deck-1',
        type: QuestionType.multipleChoice,
        content: 'content',
        options: const ['A', 'B', 'C', 'D'],
        answer: 'A',
        explanation: 'explanation\u0000hidden',
      ),
    };

    for (final entry in variants.entries) {
      expect(
        entry.value.toMap,
        throwsA(
          isA<FormatException>().having(
            (error) => error.message,
            'message',
            contains(entry.key),
          ),
        ),
        reason: entry.key,
      );
    }
  });

  test('canonicalizes valid matching answers from JSON', () {
    final question = Question.fromJson({
      'type': 'matching',
      'content': 'content',
      'answer': 'second-two|pre-fix-right-value',
      'match_left': ['pre-fix', 'second'],
      'match_right': ['right-value', 'two'],
    }, 'deck-1');

    expect(question.answer, 'pre-fix-right-value|second-two');
  });

  test('rejects ambiguous matching answers from JSON', () {
    expect(
      () => Question.fromJson({
        'type': 'matching',
        'content': 'content',
        'answer': 'a-b-c|a-b-c',
        'match_left': ['a', 'a-b'],
        'match_right': ['b-c', 'c'],
      }, 'deck-1'),
      throwsFormatException,
    );
  });
}
