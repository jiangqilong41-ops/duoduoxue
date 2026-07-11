import 'dart:convert';

import 'package:dio/dio.dart';
import 'package:dlg_q/services/openai_service.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:shared_preferences_platform_interface/shared_preferences_platform_interface.dart';

class _FailingRemovePreferencesStore extends InMemorySharedPreferencesStore {
  _FailingRemovePreferencesStore()
      : super.withData({'flutter.ai_api_key': 'plaintext-key'});

  @override
  Future<bool> remove(String key) async => false;
}

class _FailingWritePreferencesStore extends InMemorySharedPreferencesStore {
  _FailingWritePreferencesStore(this.failingKey) : super.empty();

  final String failingKey;

  @override
  Future<bool> setValue(String valueType, String key, Object value) async {
    if (key == 'flutter.$failingKey') return false;
    return super.setValue(valueType, key, value);
  }
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  setUp(() {
    SharedPreferences.setMockInitialValues({});
    FlutterSecureStorage.setMockInitialValues({});
  });

  test('migrates the current plaintext API key to secure storage', () async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('ai_api_key', 'legacy-key');

    final service = OpenAIService();

    expect(await service.getApiKey(), 'legacy-key');
    expect(
      await const FlutterSecureStorage().read(key: 'ai_api_key'),
      'legacy-key',
    );
    expect(prefs.containsKey('ai_api_key'), isFalse);
    expect(prefs.containsKey('openai_api_key'), isFalse);
  });

  test('migrates the old plaintext API key name', () async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('openai_api_key', 'old-key');

    expect(await OpenAIService().getApiKey(), 'old-key');
    expect(
      await const FlutterSecureStorage().read(key: 'ai_api_key'),
      'old-key',
    );
    expect(prefs.containsKey('openai_api_key'), isFalse);
  });

  test('secure API key wins and plaintext copies are removed', () async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('ai_api_key', 'plaintext-key');
    await prefs.setString('openai_api_key', 'older-key');
    await const FlutterSecureStorage().write(
      key: 'ai_api_key',
      value: 'secure-key',
    );

    expect(await OpenAIService().getApiKey(), 'secure-key');
    expect(prefs.containsKey('ai_api_key'), isFalse);
    expect(prefs.containsKey('openai_api_key'), isFalse);
  });

  test('reports plaintext cleanup failure instead of claiming migration',
      () async {
    SharedPreferencesStorePlatform.instance = _FailingRemovePreferencesStore();
    SharedPreferences.resetStatic();

    await expectLater(
      OpenAIService().getApiKey(),
      throwsA(
        isA<StateError>().having(
          (error) => error.message,
          'message',
          contains('明文 API Key'),
        ),
      ),
    );
    expect(
      await const FlutterSecureStorage().read(key: 'ai_api_key'),
      'plaintext-key',
    );
  });

  test('setting an empty API key deletes the secure value', () async {
    final service = OpenAIService();
    await service.setApiKey('secret');

    await service.setApiKey('');

    expect(await service.getApiKey(), isNull);
  });

  test('does not delete the secure key before plaintext cleanup succeeds',
      () async {
    await const FlutterSecureStorage().write(
      key: 'ai_api_key',
      value: 'secure-key',
    );
    SharedPreferencesStorePlatform.instance = _FailingRemovePreferencesStore();
    SharedPreferences.resetStatic();

    await expectLater(
        OpenAIService().setApiKey(''), throwsA(isA<StateError>()));

    expect(
      await const FlutterSecureStorage().read(key: 'ai_api_key'),
      'secure-key',
    );
  });

  test('normalizes supported HTTPS base URLs', () {
    for (final provider in AIProviders.builtin) {
      if (provider.baseUrl.isEmpty) continue;
      expect(
        OpenAIService.validateAndNormalizeBaseUrl(provider.baseUrl),
        provider.baseUrl,
      );
    }

    expect(
      OpenAIService.validateAndNormalizeBaseUrl(
        '  https://example.com:8443/compatible/v1///  ',
      ),
      'https://example.com:8443/compatible/v1',
    );
    expect(
      OpenAIService.validateAndNormalizeBaseUrl('HTTPS://EXAMPLE.COM/v1/'),
      'https://example.com/v1',
    );
    expect(
      OpenAIService.validateAndNormalizeBaseUrl('https://[::1]:8443/v1/'),
      'https://[::1]:8443/v1',
    );
  });

  test('rejects unsafe or ambiguous base URLs', () {
    const invalidUrls = [
      'http://example.com/v1',
      'https:///v1',
      'https://user@example.com/v1',
      'https://@example.com/v1',
      'HTTPS://@example.com/v1',
      'https://example.com/v1?token=x',
      'https://example.com/v1#fragment',
      'https://example.com/v1?',
      'https://example.com/v1#',
      'https://example.com:0/v1',
      'https://example.com:-1/v1',
      'https://example.com:65536/v1',
      'https://example.com:/v1',
      'https://example.com:+443/v1',
      r'https:\\example.com\v1',
      r'https://example.com\evil.com/v1',
      'https://exa mple.com/v1',
      'https://-/v1',
      'https://example..com/v1',
      'https://%40example.com/v1',
    ];

    for (final url in invalidUrls) {
      expect(
        () => OpenAIService.validateAndNormalizeBaseUrl(url),
        throwsFormatException,
        reason: url,
      );
    }
  });

  test('rejects a legacy HTTP URL before sending a request', () async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('ai_base_url', 'http://example.com/v1');
    await const FlutterSecureStorage().write(
      key: 'ai_api_key',
      value: 'secret',
    );
    var sent = false;
    final dio = Dio()
      ..interceptors.add(
        InterceptorsWrapper(
          onRequest: (options, handler) {
            sent = true;
            handler.reject(
              DioException(requestOptions: options, message: 'unexpected'),
            );
          },
        ),
      );

    final service = OpenAIService(dio: dio);

    await expectLater(
      service.chatCompletion(systemPrompt: 'system', userContent: 'content'),
      throwsFormatException,
    );
    expect(sent, isFalse);
  });

  test('uses the encoded image MIME type in vision requests', () async {
    await const FlutterSecureStorage().write(
      key: 'ai_api_key',
      value: 'secret',
    );
    String? imageUrl;
    final dio = Dio()
      ..interceptors.add(
        InterceptorsWrapper(
          onRequest: (options, handler) {
            final data =
                jsonDecode(options.data as String) as Map<String, dynamic>;
            final messages = data['messages'] as List<dynamic>;
            final content =
                (messages.last as Map<String, dynamic>)['content'] as List;
            imageUrl = ((content.last as Map<String, dynamic>)['image_url']
                as Map<String, dynamic>)['url'] as String;
            handler.resolve(
              Response(
                requestOptions: options,
                statusCode: 200,
                data: {
                  'choices': [
                    {
                      'message': {'content': '{}'},
                    },
                  ],
                },
              ),
            );
          },
        ),
      );
    final pngBase64 = base64Encode(const [
      0x89,
      0x50,
      0x4e,
      0x47,
      0x0d,
      0x0a,
      0x1a,
      0x0a,
    ]);

    await OpenAIService(dio: dio).chatCompletion(
      systemPrompt: 'system',
      userContent: 'content',
      imageBase64: pngBase64,
    );

    expect(imageUrl, startsWith('data:image/png;base64,'));
  });

  test('reports failed preference writes used by settings', () async {
    final cases = <(String, Future<void> Function(OpenAIService))>[
      (
        'ai_base_url',
        (service) => service.setBaseUrl('https://example.com/v1')
      ),
      ('ai_provider_id', (service) => service.setProviderId('deepseek')),
      ('ai_model', (service) => service.setModel('deepseek-chat')),
    ];

    for (final entry in cases) {
      SharedPreferencesStorePlatform.instance =
          _FailingWritePreferencesStore(entry.$1);
      SharedPreferences.resetStatic();

      await expectLater(entry.$2(OpenAIService()), throwsA(isA<StateError>()));
    }
  });
}
