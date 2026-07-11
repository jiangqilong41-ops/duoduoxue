import 'dart:async';

import 'package:dlg_q/core/providers/providers.dart';
import 'package:dlg_q/data/database/database_helper.dart';
import 'package:dlg_q/data/models/user_stats.dart';
import 'package:dlg_q/services/gamification_service.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:dlg_q/main.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:receive_sharing_intent/receive_sharing_intent.dart';
import 'package:shared_preferences/shared_preferences.dart';

class _FakeGamificationService extends GamificationService {
  _FakeGamificationService() : super(DatabaseHelper());

  @override
  Future<UserStats> getStats() async =>
      UserStats(lastStudyDate: DateTime.now());
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  setUp(() {
    SharedPreferences.setMockInitialValues({});
    FlutterSecureStorage.setMockInitialValues({});
    ReceiveSharingIntent.setMockValues(
      initialMedia: [],
      mediaStream: const Stream.empty(),
    );
  });

  testWidgets('App launches smoke test', (WidgetTester tester) async {
    final gamification = _FakeGamificationService();
    final originalErrorWidgetBuilder = ErrorWidget.builder;
    try {
      await tester.pumpWidget(
        ProviderScope(
          overrides: [
            deckListProvider.overrideWith((ref) async => []),
            allQuestionsProvider.overrideWith((ref) async => []),
            gamificationServiceProvider.overrideWithValue(gamification),
            userStatsProvider.overrideWith(
              (ref) => UserStatsNotifier(gamification),
            ),
          ],
          child: const DIYDuolingoApp(),
        ),
      );
      await tester.pumpAndSettle(const Duration(seconds: 2));
      expect(find.text('学习'), findsWidgets);
    } finally {
      ErrorWidget.builder = originalErrorWidgetBuilder;
    }
  });

  testWidgets('sharing stream errors do not escape the app', (tester) async {
    ReceiveSharingIntent.setMockValues(
      initialMedia: [],
      mediaStream: Stream<List<SharedMediaFile>>.error(
        StateError('sharing unavailable'),
      ),
    );
    final gamification = _FakeGamificationService();
    final originalErrorWidgetBuilder = ErrorWidget.builder;
    try {
      await tester.pumpWidget(
        ProviderScope(
          overrides: [
            deckListProvider.overrideWith((ref) async => []),
            allQuestionsProvider.overrideWith((ref) async => []),
            gamificationServiceProvider.overrideWithValue(gamification),
            userStatsProvider.overrideWith(
              (ref) => UserStatsNotifier(gamification),
            ),
          ],
          child: const DIYDuolingoApp(),
        ),
      );
      await tester.pumpAndSettle(const Duration(seconds: 2));
      expect(tester.takeException(), isNull);
    } finally {
      ErrorWidget.builder = originalErrorWidgetBuilder;
    }
  });
}
