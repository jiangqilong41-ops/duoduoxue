import 'dart:async';

import 'package:dlg_q/core/providers/providers.dart';
import 'package:dlg_q/data/database/database_helper.dart';
import 'package:dlg_q/data/models/user_stats.dart';
import 'package:dlg_q/features/settings/settings_screen.dart';
import 'package:dlg_q/services/gamification_service.dart';
import 'package:dlg_q/services/openai_service.dart';
import 'package:dlg_q/shared/widgets/duo_button.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';

class _FakeGamificationService extends GamificationService {
  _FakeGamificationService() : super(DatabaseHelper());

  int dailyGoal = 50;
  bool failNextDailyGoalSave = false;

  @override
  Future<UserStats> getStats() async =>
      UserStats(lastStudyDate: DateTime.now(), dailyGoal: dailyGoal);

  @override
  Future<void> setDailyGoal(int goal) async {
    dailyGoal = goal;
    if (failNextDailyGoalSave) {
      failNextDailyGoalSave = false;
      throw StateError('daily goal save failed');
    }
  }
}

class _FailingOpenAIService extends OpenAIService {
  bool failModelSave = false;

  @override
  Future<void> setModel(String model) async {
    if (failModelSave) throw StateError('model save failed');
    await super.setModel(model);
  }
}

class _ThrowingReadOpenAIService extends OpenAIService {
  @override
  Future<String?> getApiKey() async => throw StateError('keychain unavailable');
}

class _PendingReadOpenAIService extends OpenAIService {
  final keyCompleter = Completer<String?>();

  @override
  Future<String?> getApiKey() => keyCompleter.future;
}

class _PendingSaveGamificationService extends _FakeGamificationService {
  final saveStarted = Completer<void>();
  final allowSaveToFinish = Completer<void>();

  @override
  Future<void> setDailyGoal(int goal) async {
    dailyGoal = goal;
    saveStarted.complete();
    await allowSaveToFinish.future;
  }
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  setUp(() {
    SharedPreferences.setMockInitialValues({});
    FlutterSecureStorage.setMockInitialValues({});
  });

  testWidgets('invalid base URL does not partially save settings',
      (tester) async {
    final openAI = OpenAIService();
    final gamification = _FakeGamificationService();
    await openAI.setApiKey('old-key');
    await openAI.setBaseUrl('https://api.deepseek.com/v1');

    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          openaiServiceProvider.overrideWithValue(openAI),
          gamificationServiceProvider.overrideWithValue(gamification),
          userStatsProvider.overrideWith(
            (ref) => UserStatsNotifier(gamification),
          ),
        ],
        child: const MaterialApp(home: SettingsScreen()),
      ),
    );
    await tester.pumpAndSettle();

    final fields = find.byType(TextField);
    await tester.enterText(fields.at(0), 'new-key');
    await tester.enterText(fields.at(1), 'http://insecure.example/v1');
    await tester.ensureVisible(find.text('保存设置'));
    await tester.tap(find.text('保存设置'));
    await tester.pumpAndSettle();

    expect(find.text('API Base URL 必须是有效的 HTTPS 地址'), findsOneWidget);
    expect(await openAI.getApiKey(), 'old-key');
    expect(await openAI.getBaseUrl(), 'https://api.deepseek.com/v1');
  });

  testWidgets('rollback restores a legacy HTTP base URL', (tester) async {
    SharedPreferences.setMockInitialValues({
      'ai_base_url': 'http://legacy.example/v1',
      'ai_model': 'gpt-4o-mini',
      'ai_provider_id': 'openai',
    });
    final openAI = _FailingOpenAIService();
    final gamification = _FakeGamificationService();
    await openAI.setApiKey('old-key');

    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          openaiServiceProvider.overrideWithValue(openAI),
          gamificationServiceProvider.overrideWithValue(gamification),
          userStatsProvider.overrideWith(
            (ref) => UserStatsNotifier(gamification),
          ),
        ],
        child: const MaterialApp(home: SettingsScreen()),
      ),
    );
    await tester.pumpAndSettle();

    final fields = find.byType(TextField);
    await tester.enterText(fields.at(0), 'new-key');
    await tester.enterText(fields.at(1), 'https://api.example.com/v1');
    openAI.failModelSave = true;
    await tester.ensureVisible(find.text('保存设置'));
    await tester.tap(find.text('保存设置'));
    await tester.pumpAndSettle();

    expect(await openAI.getApiKey(), 'old-key');
    expect(await openAI.getBaseUrl(), 'http://legacy.example/v1');
  });

  testWidgets('rollback restores every setting after a late write failure',
      (tester) async {
    SharedPreferences.setMockInitialValues({
      'ai_base_url': 'https://api.openai.com/v1',
      'ai_model': 'gpt-4o-mini',
      'ai_provider_id': 'openai',
    });
    final openAI = OpenAIService();
    final gamification = _FakeGamificationService()..dailyGoal = 20;
    await openAI.setApiKey('old-key');

    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          openaiServiceProvider.overrideWithValue(openAI),
          gamificationServiceProvider.overrideWithValue(gamification),
          userStatsProvider.overrideWith(
            (ref) => UserStatsNotifier(gamification),
          ),
        ],
        child: const MaterialApp(home: SettingsScreen()),
      ),
    );
    await tester.pumpAndSettle();

    await tester.tap(find.byType(DropdownButton<String>).first);
    await tester.pumpAndSettle();
    await tester.tap(find.text('DeepSeek').last);
    await tester.pumpAndSettle();
    await tester.ensureVisible(find.text('10 XP'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('10 XP'));
    final fields = find.byType(TextField);
    await tester.enterText(fields.at(0), 'new-key');
    gamification.failNextDailyGoalSave = true;
    tester.testTextInput.hide();
    await tester.pumpAndSettle();
    await tester.ensureVisible(find.text('保存设置'));
    await tester.pumpAndSettle();
    await tester.tap(find.widgetWithText(DuoButton, '保存设置'));
    await tester.pumpAndSettle();

    expect(await openAI.getApiKey(), 'old-key');
    expect(await openAI.getBaseUrl(), 'https://api.openai.com/v1');
    expect(await openAI.getProviderId(), 'openai');
    expect(await openAI.getModel(), 'gpt-4o-mini');
    expect(gamification.dailyGoal, 20);
    expect(find.textContaining('保存失败'), findsOneWidget);
  });

  testWidgets('secure storage read failure leaves settings in an error state',
      (tester) async {
    final openAI = _ThrowingReadOpenAIService();
    final gamification = _FakeGamificationService();

    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          openaiServiceProvider.overrideWithValue(openAI),
          gamificationServiceProvider.overrideWithValue(gamification),
          userStatsProvider.overrideWith(
            (ref) => UserStatsNotifier(gamification),
          ),
        ],
        child: const MaterialApp(home: SettingsScreen()),
      ),
    );
    await tester.pump();

    expect(tester.takeException(), isNull);
    expect(find.textContaining('设置加载失败'), findsOneWidget);
    expect(find.byType(CircularProgressIndicator), findsNothing);
  });

  testWidgets('settings ignores a completed read after it is disposed',
      (tester) async {
    final openAI = _PendingReadOpenAIService();
    final gamification = _FakeGamificationService();

    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          openaiServiceProvider.overrideWithValue(openAI),
          gamificationServiceProvider.overrideWithValue(gamification),
          userStatsProvider.overrideWith(
            (ref) => UserStatsNotifier(gamification),
          ),
        ],
        child: const MaterialApp(home: SettingsScreen()),
      ),
    );
    await tester.pump();
    await tester.pumpWidget(const SizedBox.shrink());
    openAI.keyCompleter.complete(null);
    await tester.pumpAndSettle();

    expect(tester.takeException(), isNull);
  });

  testWidgets('settings ignores a completed save after it is disposed',
      (tester) async {
    final openAI = OpenAIService();
    final gamification = _PendingSaveGamificationService();

    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          openaiServiceProvider.overrideWithValue(openAI),
          gamificationServiceProvider.overrideWithValue(gamification),
          userStatsProvider.overrideWith(
            (ref) => UserStatsNotifier(gamification),
          ),
        ],
        child: MaterialApp(
          home: Builder(
            builder: (context) => Scaffold(
              body: Center(
                child: ElevatedButton(
                  onPressed: () => Navigator.of(context).push(
                    MaterialPageRoute<void>(
                      builder: (_) => const SettingsScreen(),
                    ),
                  ),
                  child: const Text('Open settings'),
                ),
              ),
            ),
          ),
        ),
      ),
    );
    await tester.tap(find.text('Open settings'));
    await tester.pumpAndSettle();

    final baseUrlController = tester
        .widget<TextField>(find.byType(TextField).at(1))
        .controller!;
    await tester.enterText(
      find.byType(TextField).at(1),
      'https://api.example.com/v1/',
    );
    await tester.ensureVisible(find.text('保存设置'));
    await tester.tap(find.widgetWithText(DuoButton, '保存设置'));
    await tester.pumpAndSettle();
    expect(gamification.saveStarted.isCompleted, isTrue);

    Navigator.of(tester.element(find.byType(SettingsScreen))).pop();
    await tester.pumpAndSettle();
    gamification.allowSaveToFinish.complete();
    await tester.pumpAndSettle();

    expect(baseUrlController.text, 'https://api.example.com/v1/');
    expect(tester.takeException(), isNull);
  });
}
