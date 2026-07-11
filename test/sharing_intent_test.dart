import 'dart:async';

import 'package:dlg_q/app.dart';
import 'package:dlg_q/core/providers/providers.dart';
import 'package:dlg_q/data/database/database_helper.dart';
import 'package:dlg_q/data/models/user_stats.dart';
import 'package:dlg_q/features/ingestion/ingestion_screen.dart';
import 'package:dlg_q/services/gamification_service.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_test/flutter_test.dart';
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

  late StreamController<List<SharedMediaFile>> mediaController;

  setUp(() {
    SharedPreferences.setMockInitialValues({});
    FlutterSecureStorage.setMockInitialValues({});
    mediaController = StreamController<List<SharedMediaFile>>.broadcast();
    ReceiveSharingIntent.setMockValues(
      initialMedia: [],
      mediaStream: mediaController.stream,
    );
  });

  tearDown(() async {
    await mediaController.close();
  });

  test('uses a Safari URL as ingestion text', () {
    final selected = selectSharedMedia([
      SharedMediaFile(
        path: 'https://example.com/article',
        type: SharedMediaType.url,
      ),
    ]);

    expect(selected.text, 'https://example.com/article');
    expect(selected.imagePath, isNull);
  });

  test('uses only the first text or URL and the first image', () {
    final selected = selectSharedMedia([
      SharedMediaFile(path: 'first text', type: SharedMediaType.text),
      SharedMediaFile(path: 'second text', type: SharedMediaType.text),
      SharedMediaFile(path: '/tmp/first.png', type: SharedMediaType.image),
      SharedMediaFile(path: '/tmp/second.png', type: SharedMediaType.image),
    ]);

    expect(selected.text, 'first text');
    expect(selected.imagePath, '/tmp/first.png');
  });

  testWidgets('cold Safari URL opens ingestion, fills text, and resets',
      (tester) async {
    const url = 'https://example.com/cold-article';
    ReceiveSharingIntent.setMockValues(
      initialMedia: [
        SharedMediaFile(path: url, type: SharedMediaType.url),
      ],
      mediaStream: mediaController.stream,
    );

    await tester.pumpWidget(_testApp());
    await tester.pumpAndSettle();

    expect(find.byType(IngestionScreen), findsOneWidget);
    expect(_ingestionTextField(tester).controller!.text, url);
    expect(await ReceiveSharingIntent.instance.getInitialMedia(), isEmpty);
  });

  testWidgets('hot Safari URL stream opens ingestion and fills text',
      (tester) async {
    const url = 'https://example.com/hot-article';
    await tester.pumpWidget(_testApp());
    await tester.pumpAndSettle();

    mediaController.add([
      SharedMediaFile(path: url, type: SharedMediaType.url),
    ]);
    await tester.pumpAndSettle();

    expect(find.byType(IngestionScreen), findsOneWidget);
    expect(_ingestionTextField(tester).controller!.text, url);
  });
}

Widget _testApp() {
  final gamification = _FakeGamificationService();
  return ProviderScope(
    overrides: [
      deckListProvider.overrideWith((ref) async => []),
      allQuestionsProvider.overrideWith((ref) async => []),
      gamificationServiceProvider.overrideWithValue(gamification),
      userStatsProvider.overrideWith(
        (ref) => UserStatsNotifier(gamification),
      ),
    ],
    child: const MaterialApp(home: MainApp()),
  );
}

TextField _ingestionTextField(WidgetTester tester) {
  return tester.widget<TextField>(
    find.descendant(
      of: find.byType(IngestionScreen),
      matching: find.byType(TextField),
    ),
  );
}
