import 'dart:convert';

import 'question_type.dart';

List<String>? _decodeStringList(Object? value) {
  if (value == null) return null;
  final encoded = value as String;

  try {
    final decoded = jsonDecode(encoded);
    if (decoded is List) return List<String>.from(decoded);
  } on FormatException {
    // Existing databases use NUL-separated strings.
  }

  return encoded.split('\x00').where((item) => item.isNotEmpty).toList();
}

String _nulSafeText(String value, String field) {
  if (value.contains('\x00')) {
    throw FormatException('$field must not contain an actual NUL character');
  }
  return value;
}

bool _validMatchingLabels(List<String> labels) {
  return labels.isNotEmpty &&
      labels.toSet().length == labels.length &&
      labels.every(
        (label) =>
            label.isNotEmpty && label == label.trim() && !label.contains('|'),
      );
}

Map<String, String> parseMatchingAnswer(
  List<String> matchLeft,
  String answer, {
  required List<String> matchRight,
}) {
  if (!_validMatchingLabels(matchLeft) ||
      !_validMatchingLabels(matchRight) ||
      matchRight.length != matchLeft.length) {
    return {};
  }

  final pairs = answer.split('|').map((pair) => pair.trim()).toList();
  if (pairs.length != matchLeft.length) return {};

  final result = <String, String>{};
  final usedRights = <String>{};
  for (final pair in pairs) {
    final candidates = <MapEntry<String, String>>[];
    for (final left in matchLeft) {
      for (final right in matchRight) {
        if (pair == '$left-$right') candidates.add(MapEntry(left, right));
      }
    }
    if (candidates.length != 1) return {};
    final candidate = candidates.single;
    if (result.containsKey(candidate.key) || !usedRights.add(candidate.value)) {
      return {};
    }
    result[candidate.key] = candidate.value;
  }
  return result.length == matchLeft.length ? result : {};
}

String serializeMatchingAnswer(
  List<String> matchLeft,
  Map<String, String> matches,
) {
  if (!_validMatchingLabels(matchLeft) || matchLeft.length != matches.length) {
    return '';
  }

  final rights = <String>[];
  for (final left in matchLeft) {
    final right = matches[left];
    if (right == null) return '';
    rights.add(right);
  }
  if (!_validMatchingLabels(rights)) return '';
  return matchLeft.map((left) => '$left-${matches[left]}').join('|');
}

String canonicalizeMatchingAnswer(
  List<String> matchLeft,
  List<String> matchRight,
  String answer,
) {
  final matches = parseMatchingAnswer(
    matchLeft,
    answer,
    matchRight: matchRight,
  );
  return matches.isEmpty ? '' : serializeMatchingAnswer(matchLeft, matches);
}

bool matchingAnswersEqual(
  List<String> matchLeft,
  List<String> matchRight,
  String submitted,
  String expected,
) {
  final submittedMatches = parseMatchingAnswer(
    matchLeft,
    submitted,
    matchRight: matchRight,
  );
  final expectedMatches = parseMatchingAnswer(
    matchLeft,
    expected,
    matchRight: matchRight,
  );
  return expectedMatches.isNotEmpty &&
      submittedMatches.length == expectedMatches.length &&
      expectedMatches.entries.every(
        (entry) => submittedMatches[entry.key] == entry.value,
      );
}

/// 题目模型
class Question {
  final String id;
  final String deckId;
  final QuestionType type;
  final String content; // 题干
  final List<String> options; // 选项(选择题/判断题/排序题用)
  final String answer; // 正确答案
  final String? explanation; // 解析
  // 匹配题专用: 左右两列
  final List<String>? matchLeft;
  final List<String>? matchRight;

  Question({
    required this.id,
    required this.deckId,
    required this.type,
    required this.content,
    this.options = const [],
    required this.answer,
    this.explanation,
    this.matchLeft,
    this.matchRight,
  });

  Map<String, dynamic> toMap() {
    return {
      'id': _nulSafeText(id, 'id'),
      'deck_id': _nulSafeText(deckId, 'deck_id'),
      'type': type.value,
      'content': _nulSafeText(content, 'content'),
      'options': jsonEncode(options),
      'answer': _nulSafeText(answer, 'answer'),
      'explanation': explanation == null
          ? null
          : _nulSafeText(explanation!, 'explanation'),
      'match_left': jsonEncode(matchLeft ?? const <String>[]),
      'match_right': jsonEncode(matchRight ?? const <String>[]),
    };
  }

  factory Question.fromMap(Map<String, dynamic> map) {
    return Question(
      id: map['id'] as String,
      deckId: map['deck_id'] as String,
      type: QuestionType.fromString(map['type'] as String),
      content: map['content'] as String,
      options: _decodeStringList(map['options']) ?? [],
      answer: map['answer'] as String,
      explanation: map['explanation'] as String?,
      matchLeft: _decodeStringList(map['match_left']),
      matchRight: _decodeStringList(map['match_right']),
    );
  }

  /// 从 OpenAI 返回的 JSON 构建
  factory Question.fromJson(Map<String, dynamic> json, String deckId) {
    final type =
        QuestionType.fromString(json['type'] as String? ?? 'multiple_choice');
    final options = (json['options'] as List<dynamic>?)
            ?.map((e) => e.toString())
            .toList() ??
        [];
    final matchLeft = (json['match_left'] as List<dynamic>?)
        ?.map((e) => e.toString())
        .toList();
    final matchRight = (json['match_right'] as List<dynamic>?)
        ?.map((e) => e.toString())
        .toList();
    var answer = json['answer']?.toString() ?? '';
    if (type == QuestionType.matching) {
      answer = canonicalizeMatchingAnswer(
        matchLeft ?? const [],
        matchRight ?? const [],
        answer,
      );
      if (answer.isEmpty) {
        throw const FormatException('invalid or ambiguous matching answer');
      }
    }

    return Question(
      id: '',
      deckId: deckId,
      type: type,
      content: json['content'] as String? ?? '',
      options: options,
      answer: answer,
      explanation: json['explanation'] as String?,
      matchLeft: matchLeft,
      matchRight: matchRight,
    );
  }
}
