import 'dart:async';
import 'dart:io';

import 'package:dlg_q/features/ingestion/deck_preview_screen.dart';
import 'package:dlg_q/features/ingestion/ingestion_screen.dart';
import 'package:dlg_q/core/providers/providers.dart';
import 'package:dlg_q/services/content_analyzer.dart';
import 'package:dlg_q/services/openai_service.dart';
import 'package:dlg_q/shared/widgets/duo_button.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:path/path.dart' as path;

class _ThrowingApiKeyService extends OpenAIService {
  @override
  Future<bool> hasApiKey() async => throw StateError('keychain unavailable');
}

class _PendingApiKeyService extends OpenAIService {
  final keyCompleter = Completer<bool>();

  @override
  Future<bool> hasApiKey() => keyCompleter.future;
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  const pathProviderChannel = MethodChannel('plugins.flutter.io/path_provider');
  late Directory sandbox;
  late Directory supportRoot;

  setUp(() async {
    sandbox = await Directory.systemTemp.createTemp('duoduoxue_ingestion_');
    supportRoot = Directory(path.join(sandbox.path, 'support'));
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(pathProviderChannel, (call) async {
      if (call.method == 'getApplicationSupportDirectory') {
        return supportRoot.path;
      }
      return null;
    });
  });

  tearDown(() async {
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(pathProviderChannel, null);
    if (await sandbox.exists()) {
      await sandbox.delete(recursive: true);
    }
  });

  testWidgets('shared image keeps the AI button disabled until loading ends',
      (tester) async {
    final loader = Completer<String>();

    await tester.pumpWidget(
      ProviderScope(
        child: MaterialApp(
          home: IngestionScreen(
            sharedImagePath: path.join(sandbox.path, 'shared.png'),
            imageLoader: (_) => loader.future,
          ),
        ),
      ),
    );

    expect(_aiButton(tester).enabled, isFalse);

    loader.complete('encoded-image');
    await tester.pump();

    expect(_aiButton(tester).enabled, isTrue);
  });

  testWidgets(
      'shared image read failure restores the button and shows an error',
      (tester) async {
    await tester.pumpWidget(
      ProviderScope(
        child: MaterialApp(
          home: IngestionScreen(
            sharedImagePath: path.join(sandbox.path, 'missing.png'),
            imageLoader: (_) async => throw const FileSystemException('failed'),
          ),
        ),
      ),
    );
    await tester.pump();

    expect(_aiButton(tester).enabled, isTrue);
    expect(find.text('图片读取失败，请重新分享或选择其他图片'), findsOneWidget);
  });

  testWidgets('cancelling ingestion deletes its owned shared image',
      (tester) async {
    final image = (await tester.runAsync(
      () => _createOwnedImage(supportRoot, 'ingestion.png'),
    ))!;

    await tester.pumpWidget(
      ProviderScope(
        child: MaterialApp(
          home: Builder(
            builder: (context) => TextButton(
              onPressed: () => Navigator.of(context).push(
                MaterialPageRoute<void>(
                  builder: (_) => IngestionScreen(
                    sharedImagePath: image.path,
                    imageLoader: (_) async => 'encoded-image',
                  ),
                ),
              ),
              child: const Text('打开导入'),
            ),
          ),
        ),
      ),
    );

    await tester.tap(find.text('打开导入'));
    await tester.pumpAndSettle();
    await tester.tap(find.byIcon(Icons.close));
    await tester.pumpAndSettle();
    expect(find.text('打开导入'), findsOneWidget);
    await _waitUntilDeleted(tester, image);

    expect(await tester.runAsync(image.exists), isFalse);
  });

  testWidgets('disposing an unsaved preview deletes its owned shared image',
      (tester) async {
    final image = (await tester.runAsync(
      () => _createOwnedImage(supportRoot, 'preview.png'),
    ))!;

    await tester.pumpWidget(
      ProviderScope(
        child: MaterialApp(
          home: DeckPreviewScreen(
            result: AnalysisResult(title: '预览', questions: const []),
            sourceImage: image.path,
          ),
        ),
      ),
    );
    await tester.pumpWidget(const SizedBox.shrink());
    await _waitUntilDeleted(tester, image);

    expect(await tester.runAsync(image.exists), isFalse);
  });

  testWidgets('API key read failure is shown instead of escaping',
      (tester) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          openaiServiceProvider.overrideWithValue(_ThrowingApiKeyService()),
        ],
        child: const MaterialApp(
          home: IngestionScreen(sharedText: '公开示例文本'),
        ),
      ),
    );

    await tester.tap(find.widgetWithText(DuoButton, 'AI 拆解为题目'));
    await tester.pump();

    expect(tester.takeException(), isNull);
    expect(find.textContaining('无法读取 API Key'), findsOneWidget);
  });

  testWidgets('ingestion ignores an API key read after it is disposed',
      (tester) async {
    final openAI = _PendingApiKeyService();
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          openaiServiceProvider.overrideWithValue(openAI),
        ],
        child: const MaterialApp(
          home: IngestionScreen(sharedText: '公开示例文本'),
        ),
      ),
    );
    await tester.tap(find.widgetWithText(DuoButton, 'AI 拆解为题目'));
    await tester.pump();
    await tester.pumpWidget(const SizedBox.shrink());
    openAI.keyCompleter.complete(true);
    await tester.pumpAndSettle();

    expect(tester.takeException(), isNull);
  });
}

DuoButton _aiButton(WidgetTester tester) {
  return tester.widget<DuoButton>(
    find.widgetWithText(DuoButton, 'AI 拆解为题目'),
  );
}

Future<File> _createOwnedImage(Directory supportRoot, String name) async {
  final image = File(
    path.join(supportRoot.path, 'source_images', name),
  );
  await image.create(recursive: true);
  await image.writeAsBytes(const [1, 2, 3]);
  return image;
}

Future<void> _waitUntilDeleted(WidgetTester tester, File file) async {
  for (var attempt = 0; attempt < 100; attempt++) {
    final exists = await tester.runAsync(file.exists);
    if (exists == false) return;
    await tester.runAsync(
      () => Future<void>.delayed(const Duration(milliseconds: 10)),
    );
    await tester.pump();
  }
}
