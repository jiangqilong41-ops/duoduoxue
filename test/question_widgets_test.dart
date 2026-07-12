import 'package:dlg_q/core/providers/providers.dart';
import 'package:dlg_q/core/constants/app_colors.dart';
import 'package:dlg_q/data/database/database_helper.dart';
import 'package:dlg_q/data/models/question.dart';
import 'package:dlg_q/data/models/question_type.dart';
import 'package:dlg_q/data/models/user_stats.dart';
import 'package:dlg_q/features/learning/quiz_screen.dart';
import 'package:dlg_q/features/learning/widgets/question_widgets.dart';
import 'package:dlg_q/services/gamification_service.dart';
import 'package:dlg_q/services/openai_service.dart';
import 'package:dlg_q/shared/widgets/duo_button.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

class _FakeGamificationService extends GamificationService {
  _FakeGamificationService() : super(DatabaseHelper());

  @override
  Future<UserStats> getStats() async =>
      UserStats(lastStudyDate: DateTime.now());

  @override
  Future<UserStats> onCorrectAnswer() => getStats();

  @override
  Future<UserStats> onWrongAnswer() => getStats();

  @override
  Future<void> recordCheckIn() async {}

  @override
  Future<int> incrementTotalCorrect() async => 1;
}

class _SemanticCorrectOpenAIService extends OpenAIService {
  @override
  Future<bool> hasApiKey() async => true;

  @override
  Future<bool> judgeFillBlankAnswer({
    required String question,
    required String userAnswer,
    required String correctAnswer,
  }) async =>
      true;
}

void main() {
  test('matching answer parsing follows left prefixes in order', () {
    expect(
      parseMatchingAnswer(
        const ['pre-fix', 'second'],
        'pre-fix-right-value|second-other-value',
        matchRight: const ['right-value', 'other-value'],
      ),
      const {
        'pre-fix': 'right-value',
        'second': 'other-value',
      },
    );
  });

  test('matching answer parsing ignores pair order', () {
    expect(
      parseMatchingAnswer(
        const ['first', 'second'],
        'second-two|first-one',
        matchRight: const ['one', 'two'],
      ),
      const {'first': 'one', 'second': 'two'},
    );
  });

  test('matching answers follow the matchLeft order', () {
    expect(
      serializeMatchingAnswer(
        const ['first', 'second'],
        const {'second': 'two', 'first': 'one'},
      ),
      'first-one|second-two',
    );
  });

  test('incomplete matching answers serialize as empty', () {
    expect(
      serializeMatchingAnswer(
        const ['first', 'second'],
        const {'second': 'two'},
      ),
      isEmpty,
    );
  });

  test('duplicate matching left items serialize as empty', () {
    expect(
      serializeMatchingAnswer(
        const ['first', ' first '],
        const {'first': 'one', ' first ': 'two'},
      ),
      isEmpty,
    );
  });

  test('blank matching left items serialize as empty', () {
    expect(
      serializeMatchingAnswer(
        const ['   '],
        const {'   ': 'one'},
      ),
      isEmpty,
    );
  });

  test('blank matching right items serialize as empty', () {
    expect(
      serializeMatchingAnswer(
        const ['first'],
        const {'first': '   '},
      ),
      isEmpty,
    );
  });

  test('duplicate matching right items serialize as empty', () {
    expect(
      serializeMatchingAnswer(
        const ['first', 'second'],
        const {'first': 'one', 'second': ' one '},
      ),
      isEmpty,
    );
  });

  test('extra matching entries serialize as empty', () {
    expect(
      serializeMatchingAnswer(
        const ['first'],
        const {'first': 'one', 'second': 'two'},
      ),
      isEmpty,
    );
  });

  testWidgets('unmatching a complete answer clears and disables submission',
      (tester) async {
    final question = Question(
      id: 'question-1',
      deckId: 'deck-1',
      type: QuestionType.matching,
      content: 'Match the pairs',
      answer: 'first-one|second-two',
      matchLeft: const ['first', 'second'],
      matchRight: const ['one', 'two'],
    );
    final gamification = _FakeGamificationService();

    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          gamificationServiceProvider.overrideWithValue(gamification),
        ],
        child: MaterialApp(
          home: QuizScreen(questions: [question]),
        ),
      ),
    );
    await tester.pumpAndSettle();

    await tester.tap(find.text('second'));
    await tester.pump();
    await tester.tap(find.text('two'));
    await tester.pump();
    await tester.tap(find.text('first'));
    await tester.pump();
    await tester.tap(find.text('one'));
    await tester.pump();

    expect(
      tester.widget<QuestionWidget>(find.byType(QuestionWidget)).selectedAnswer,
      'first-one|second-two',
    );
    expect(
      tester.widget<DuoButton>(find.widgetWithText(DuoButton, '检查')).enabled,
      isTrue,
    );

    await tester.tap(find.text('first'));
    await tester.pump();

    expect(
      tester.widget<QuestionWidget>(find.byType(QuestionWidget)).selectedAnswer,
      isEmpty,
    );
    expect(
      tester.widget<DuoButton>(find.widgetWithText(DuoButton, '检查')).enabled,
      isFalse,
    );
  });

  testWidgets('matching state resets when the question changes',
      (tester) async {
    var question = Question(
      id: 'question-1',
      deckId: 'deck-1',
      type: QuestionType.matching,
      content: 'First question',
      answer: 'alpha-one',
      matchLeft: const ['alpha'],
      matchRight: const ['one'],
    );
    String? selectedAnswer;
    late StateSetter setHostState;

    await tester.pumpWidget(
      MaterialApp(
        home: StatefulBuilder(
          builder: (context, setState) {
            setHostState = setState;
            return QuestionWidget(
              question: question,
              selectedAnswer: selectedAnswer,
              onAnswerSelected: (answer) => selectedAnswer = answer,
            );
          },
        ),
      ),
    );

    await tester.tap(find.text('alpha'));
    await tester.pump();
    await tester.tap(find.text('one'));
    await tester.pump();
    expect(selectedAnswer, 'alpha-one');

    setHostState(() {
      question = Question(
        id: 'question-2',
        deckId: 'deck-1',
        type: QuestionType.matching,
        content: 'Second question',
        answer: 'beta-two',
        matchLeft: const ['beta'],
        matchRight: const ['two'],
      );
      selectedAnswer = null;
    });
    await tester.pump();

    await tester.tap(find.text('beta'));
    await tester.pump();
    await tester.tap(find.text('two'));
    await tester.pump();

    expect(selectedAnswer, 'beta-two');
  });

  testWidgets('ordering state resets only when the question changes',
      (tester) async {
    var question = Question(
      id: 'ordering-question',
      deckId: 'deck-1',
      type: QuestionType.ordering,
      content: 'First ordering question',
      options: const ['first', 'second'],
      answer: 'second|first',
    );
    var showResult = false;
    late StateSetter setHostState;

    await tester.pumpWidget(
      MaterialApp(
        home: StatefulBuilder(
          builder: (context, setState) {
            setHostState = setState;
            return OrderingWidget(
              question: question,
              showResult: showResult,
              onOrderChanged: (_) {},
            );
          },
        ),
      ),
    );

    await tester.tap(find.byIcon(Icons.arrow_downward).first);
    await tester.pump();

    setHostState(() => showResult = true);
    await tester.pump();
    expect(
      tester.getTopLeft(find.text('second')).dy,
      lessThan(tester.getTopLeft(find.text('first')).dy),
    );

    setHostState(() {
      question = Question(
        id: 'ordering-question',
        deckId: 'deck-1',
        type: QuestionType.ordering,
        content: 'Second ordering question',
        options: const ['third', 'fourth'],
        answer: 'third|fourth',
      );
      showResult = false;
    });
    await tester.pump();

    expect(find.text('first'), findsNothing);
    expect(find.text('second'), findsNothing);
    expect(find.text('third'), findsOneWidget);
    expect(find.text('fourth'), findsOneWidget);
  });

  testWidgets('matching result supports hyphens in left items', (tester) async {
    final question = Question(
      id: 'question-1',
      deckId: 'deck-1',
      type: QuestionType.matching,
      content: 'Hyphenated left item',
      answer: 'pre-fix-right-value',
      matchLeft: const ['pre-fix'],
      matchRight: const ['right-value'],
    );
    var showResult = false;
    late StateSetter setHostState;

    await tester.pumpWidget(
      MaterialApp(
        home: StatefulBuilder(
          builder: (context, setState) {
            setHostState = setState;
            return QuestionWidget(
              question: question,
              showResult: showResult,
              onAnswerSelected: (_) {},
            );
          },
        ),
      ),
    );

    await tester.tap(find.text('pre-fix'));
    await tester.pump();
    await tester.tap(find.text('right-value'));
    await tester.pump();

    setHostState(() => showResult = true);
    await tester.pump();

    expect(find.byIcon(Icons.check), findsNWidgets(2));
    expect(find.byIcon(Icons.close), findsNothing);
  });

  testWidgets('non-canonical stored matching answer is correct and highlighted',
      (tester) async {
    final question = Question(
      id: 'question-1',
      deckId: 'deck-1',
      type: QuestionType.matching,
      content: 'Match the pairs',
      answer: 'second-two|pre-fix-right-value',
      matchLeft: const ['pre-fix', 'second'],
      matchRight: const ['right-value', 'two'],
    );

    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          gamificationServiceProvider.overrideWithValue(
            _FakeGamificationService(),
          ),
        ],
        child: MaterialApp(home: QuizScreen(questions: [question])),
      ),
    );
    await tester.pumpAndSettle();

    await tester.tap(find.text('pre-fix'));
    await tester.pump();
    await tester.tap(find.text('right-value'));
    await tester.pump();
    await tester.tap(find.text('second'));
    await tester.pump();
    await tester.tap(find.text('two'));
    await tester.pump();
    await tester.tap(find.widgetWithText(DuoButton, '检查'));
    await tester.pumpAndSettle();

    expect(find.text('答对了！'), findsOneWidget);
    expect(
      find.descendant(
        of: find.byType(MatchingWidget),
        matching: find.byIcon(Icons.check),
      ),
      findsNWidgets(4),
    );
    expect(
      find.descendant(
        of: find.byType(MatchingWidget),
        matching: find.byIcon(Icons.close),
      ),
      findsNothing,
    );
  });

  testWidgets('fill blank state resets for a new question instance',
      (tester) async {
    var question = Question(
      id: '',
      deckId: 'deck-1',
      type: QuestionType.fillBlank,
      content: 'First ___',
      answer: 'answer',
    );
    late StateSetter setHostState;

    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: StatefulBuilder(
            builder: (context, setState) {
              setHostState = setState;
              return QuestionWidget(
                question: question,
                onAnswerSelected: (_) {},
              );
            },
          ),
        ),
      ),
    );
    await tester.enterText(find.byType(TextField), 'old answer');

    setHostState(() {
      question = Question(
        id: '',
        deckId: 'deck-1',
        type: QuestionType.fillBlank,
        content: 'Second ___',
        answer: 'new answer',
      );
    });
    await tester.pump();

    expect(find.text('old answer'), findsNothing);
    expect(tester.widget<TextField>(find.byType(TextField)).controller!.text,
        isEmpty);
  });

  testWidgets('true false state resets for a new question instance',
      (tester) async {
    var question = Question(
      id: 'reused-id',
      deckId: 'deck-1',
      type: QuestionType.trueFalse,
      content: 'First statement',
      answer: '正确',
    );
    late StateSetter setHostState;

    await tester.pumpWidget(
      MaterialApp(
        home: StatefulBuilder(
          builder: (context, setState) {
            setHostState = setState;
            return QuestionWidget(
              question: question,
              onAnswerSelected: (_) {},
            );
          },
        ),
      ),
    );
    await tester.tap(find.text('正确'));
    await tester.pump();

    setHostState(() {
      question = Question(
        id: 'reused-id',
        deckId: 'deck-1',
        type: QuestionType.trueFalse,
        content: 'Second statement',
        answer: '错误',
      );
    });
    await tester.pump();

    expect(
      tester.widget<Text>(find.text('正确')).style!.color,
      AppColors.textSecondary,
    );
  });

  testWidgets('multiple choice clears a reused option for a new question',
      (tester) async {
    var question = Question(
      id: 'reused-id',
      deckId: 'deck-1',
      type: QuestionType.multipleChoice,
      content: 'First question',
      options: const ['Shared', 'First only'],
      answer: 'Shared',
    );
    late StateSetter setHostState;

    await tester.pumpWidget(
      MaterialApp(
        home: StatefulBuilder(
          builder: (context, setState) {
            setHostState = setState;
            return QuestionWidget(
              question: question,
              onAnswerSelected: (_) {},
            );
          },
        ),
      ),
    );
    await tester.tap(find.text('Shared'));
    await tester.pump();

    setHostState(() {
      question = Question(
        id: 'reused-id',
        deckId: 'deck-1',
        type: QuestionType.multipleChoice,
        content: 'Second question',
        options: const ['Shared', 'Second only'],
        answer: 'Second only',
      );
    });
    await tester.pump();

    final option = tester.widget<AnimatedContainer>(
      find
          .ancestor(
            of: find.text('Shared'),
            matching: find.byType(AnimatedContainer),
          )
          .first,
    );
    expect((option.decoration! as BoxDecoration).color, Colors.white);
  });

  testWidgets('standalone fill blank result ignores answer case',
      (tester) async {
    final question = Question(
      id: 'fill-1',
      deckId: 'deck-1',
      type: QuestionType.fillBlank,
      content: 'Use ___ to edit code',
      answer: 'Codex',
    );
    var showResult = false;
    late StateSetter setHostState;

    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: StatefulBuilder(
            builder: (context, setState) {
              setHostState = setState;
              return FillBlankWidget(
                question: question,
                showResult: showResult,
                onAnswerChanged: (_) {},
              );
            },
          ),
        ),
      ),
    );
    await tester.enterText(find.byType(TextField), 'codex');
    setHostState(() => showResult = true);
    await tester.pump();

    expect(find.text('正确答案: Codex'), findsNothing);
    expect(
      tester.widget<TextField>(find.byType(TextField)).style!.color,
      AppColors.green,
    );
    expect(tester.widget<TextField>(find.byType(TextField)).controller!.text,
        'codex');
  });

  testWidgets('semantic fill blank result follows the quiz verdict',
      (tester) async {
    final question = Question(
      id: 'fill-2',
      deckId: 'deck-1',
      type: QuestionType.fillBlank,
      content: 'A command-line interface is also called a ___',
      answer: 'command-line interface',
    );

    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          gamificationServiceProvider.overrideWithValue(
            _FakeGamificationService(),
          ),
          openaiServiceProvider.overrideWithValue(
            _SemanticCorrectOpenAIService(),
          ),
        ],
        child: MaterialApp(home: QuizScreen(questions: [question])),
      ),
    );
    await tester.pumpAndSettle();
    await tester.enterText(find.byType(TextField), 'CLI');
    await tester.pump();
    await tester.tap(find.widgetWithText(DuoButton, '检查'));
    await tester.pumpAndSettle();

    expect(find.text('答对了！'), findsOneWidget);
    expect(find.text('正确答案: command-line interface'), findsNothing);
    expect(
      tester.widget<TextField>(find.byType(TextField)).style!.color,
      AppColors.green,
    );
    expect(tester.widget<TextField>(find.byType(TextField)).controller!.text,
        'CLI');
  });
}
