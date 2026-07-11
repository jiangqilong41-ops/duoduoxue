import 'dart:convert';
import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// AI 厂商预设
class AIProviderPreset {
  final String id;
  final String name;
  final String baseUrl;
  final List<String> models;
  final String keyHelpUrl;
  final String keyHint;

  const AIProviderPreset({
    required this.id,
    required this.name,
    required this.baseUrl,
    required this.models,
    required this.keyHelpUrl,
    required this.keyHint,
  });
}

/// 内置 AI 厂商列表
class AIProviders {
  static const List<AIProviderPreset> builtin = [
    AIProviderPreset(
      id: 'openai',
      name: 'OpenAI',
      baseUrl: 'https://api.openai.com/v1',
      models: ['gpt-4o-mini', 'gpt-4o', 'gpt-4-turbo'],
      keyHelpUrl: 'https://platform.openai.com/api-keys',
      keyHint: 'sk-...',
    ),
    AIProviderPreset(
      id: 'deepseek',
      name: 'DeepSeek',
      baseUrl: 'https://api.deepseek.com/v1',
      models: ['deepseek-chat', 'deepseek-reasoner'],
      keyHelpUrl: 'https://platform.deepseek.com/api_keys',
      keyHint: 'sk-...',
    ),
    AIProviderPreset(
      id: 'qwen',
      name: '通义千问 (百炼)',
      baseUrl: 'https://dashscope.aliyuncs.com/compatible-mode/v1',
      models: ['qwen-turbo', 'qwen-plus', 'qwen-max'],
      keyHelpUrl: 'https://bailian.console.aliyun.com/?apiKey=1',
      keyHint: 'sk-...',
    ),
    AIProviderPreset(
      id: 'moonshot',
      name: '月之暗面 (Kimi)',
      baseUrl: 'https://api.moonshot.cn/v1',
      models: ['moonshot-v1-8k', 'moonshot-v1-32k', 'moonshot-v1-128k'],
      keyHelpUrl: 'https://platform.moonshot.cn/console/api-keys',
      keyHint: 'sk-...',
    ),
    AIProviderPreset(
      id: 'zhipu',
      name: '智谱 AI',
      baseUrl: 'https://open.bigmodel.cn/api/paas/v4',
      models: ['glm-4-flash', 'glm-4-air', 'glm-4-plus', 'glm-4v-plus'],
      keyHelpUrl: 'https://open.bigmodel.cn/usercenter/apikeys',
      keyHint: '...',
    ),
    AIProviderPreset(
      id: 'gemini',
      name: 'Google Gemini',
      baseUrl: 'https://generativelanguage.googleapis.com/v1beta/openai',
      models: ['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-2.0-flash'],
      keyHelpUrl: 'https://aistudio.google.com/apikey',
      keyHint: 'AIza...',
    ),
    AIProviderPreset(
      id: 'custom',
      name: '自定义',
      baseUrl: '',
      models: [],
      keyHelpUrl: '',
      keyHint: '',
    ),
  ];

  static AIProviderPreset? getById(String id) {
    for (final p in builtin) {
      if (p.id == id) return p;
    }
    return null;
  }
}

/// AI 服务（兼容 OpenAI 接口格式）
class OpenAIService {
  static const String _apiKeyKey = 'ai_api_key';
  static const String _modelKey = 'ai_model';
  static const String _baseUrlKey = 'ai_base_url';
  static const String _providerIdKey = 'ai_provider_id';

  final Dio _dio;
  final FlutterSecureStorage _secureStorage;

  OpenAIService({Dio? dio, FlutterSecureStorage? secureStorage})
      : _dio = dio ??
            Dio(BaseOptions(
              connectTimeout: const Duration(seconds: 30),
              receiveTimeout: const Duration(seconds: 120),
            )),
        _secureStorage = secureStorage ??
            const FlutterSecureStorage(
              iOptions: IOSOptions(
                accessibility: KeychainAccessibility.unlocked_this_device,
                synchronizable: false,
              ),
            );

  Future<String?> getApiKey() async {
    final prefs = await SharedPreferences.getInstance();
    final secureKey = await _secureStorage.read(key: _apiKeyKey);
    if (secureKey != null) {
      await _removePlaintextApiKeys(prefs);
      return secureKey;
    }

    final plaintextKey =
        prefs.getString(_apiKeyKey) ?? prefs.getString('openai_api_key');
    if (plaintextKey != null) {
      await _secureStorage.write(key: _apiKeyKey, value: plaintextKey);
      await _removePlaintextApiKeys(prefs);
    }
    return plaintextKey;
  }

  Future<void> setApiKey(String key) async {
    final prefs = await SharedPreferences.getInstance();
    if (key.isEmpty) {
      await _removePlaintextApiKeys(prefs);
      await _secureStorage.delete(key: _apiKeyKey);
    } else {
      await _secureStorage.write(key: _apiKeyKey, value: key);
      await _removePlaintextApiKeys(prefs);
    }
  }

  Future<void> _removePlaintextApiKeys(SharedPreferences prefs) async {
    final currentKeyRemoved = await prefs.remove(_apiKeyKey);
    final oldKeyRemoved = await prefs.remove('openai_api_key');
    if (!currentKeyRemoved || !oldKeyRemoved) {
      throw StateError('无法清理明文 API Key，请重试');
    }
  }

  Future<String> getModel() async {
    final prefs = await SharedPreferences.getInstance();
    final model = prefs.getString(_modelKey);
    if (model != null) return model;
    // 兼容旧版本
    final oldModel = prefs.getString('openai_model');
    if (oldModel != null) {
      await prefs.setString(_modelKey, oldModel);
      await prefs.remove('openai_model');
      return oldModel;
    }
    return 'gpt-4o-mini';
  }

  Future<void> setModel(String model) async {
    final prefs = await SharedPreferences.getInstance();
    final saved = await prefs.setString(_modelKey, model);
    if (!saved) throw StateError('无法保存 AI 模型');
  }

  Future<String> getBaseUrl() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString(_baseUrlKey) ?? 'https://api.openai.com/v1';
  }

  Future<void> setBaseUrl(String url) async {
    final prefs = await SharedPreferences.getInstance();
    final saved = await prefs.setString(
      _baseUrlKey,
      validateAndNormalizeBaseUrl(url),
    );
    if (!saved) throw StateError('无法保存 API Base URL');
  }

  Future<void> restoreBaseUrlForRollback(String url) async {
    final prefs = await SharedPreferences.getInstance();
    final restored = await prefs.setString(_baseUrlKey, url);
    if (!restored) throw StateError('无法恢复 API Base URL');
  }

  static String validateAndNormalizeBaseUrl(String value) {
    final trimmed = value.trim();
    final match = RegExp(
      r'^https://([^/?#]*)([^?#]*)$',
      caseSensitive: false,
    ).firstMatch(trimmed);
    final uri = Uri.tryParse(trimmed);
    if (trimmed.contains(r'\') ||
        match == null ||
        uri == null ||
        uri.scheme != 'https' ||
        uri.host.isEmpty ||
        !_isValidAuthority(match.group(1)!) ||
        uri.userInfo.isNotEmpty ||
        uri.hasQuery ||
        uri.hasFragment) {
      throw const FormatException('API Base URL 必须是有效的 HTTPS 地址');
    }
    return uri
        .replace(scheme: 'https')
        .toString()
        .replaceFirst(RegExp(r'/+$'), '');
  }

  static bool _isValidAuthority(String authority) {
    if (authority.isEmpty ||
        authority.contains('@') ||
        authority.contains('%') ||
        RegExp(r'\s').hasMatch(authority)) {
      return false;
    }

    late String host;
    String? portText;
    if (authority.startsWith('[')) {
      final closingBracket = authority.indexOf(']');
      if (closingBracket <= 1) return false;
      host = authority.substring(1, closingBracket);
      final suffix = authority.substring(closingBracket + 1);
      if (suffix.isNotEmpty) {
        if (!suffix.startsWith(':')) return false;
        portText = suffix.substring(1);
      }
      if (!RegExp(r'^[0-9a-fA-F:.]+$').hasMatch(host) ||
          !host.contains(':')) {
        return false;
      }
    } else {
      final parts = authority.split(':');
      if (parts.length > 2) return false;
      host = parts.first;
      if (parts.length == 2) portText = parts.last;

      final dnsHost = host.endsWith('.')
          ? host.substring(0, host.length - 1)
          : host;
      final validLabel = RegExp(
        r'^[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?$',
      );
      if (dnsHost.isEmpty ||
          dnsHost.split('.').any(
                (label) => label.isEmpty || !validLabel.hasMatch(label),
              )) {
        return false;
      }
    }

    if (portText != null) {
      if (!RegExp(r'^\d+$').hasMatch(portText)) return false;
      final port = int.tryParse(portText);
      if (port == null || port < 1 || port > 65535) return false;
    }
    return true;
  }

  Future<String> getProviderId() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString(_providerIdKey) ?? 'openai';
  }

  Future<void> setProviderId(String id) async {
    final prefs = await SharedPreferences.getInstance();
    final saved = await prefs.setString(_providerIdKey, id);
    if (!saved) throw StateError('无法保存 AI 厂商');
  }

  Future<bool> hasApiKey() async {
    final key = await getApiKey();
    return key != null && key.isNotEmpty;
  }

  /// 调用 AI Chat Completions API（OpenAI 兼容格式）
  Future<String> chatCompletion({
    required String systemPrompt,
    required String userContent,
    String? imageBase64,
    double? temperature,
  }) async {
    final apiKey = await getApiKey();
    if (apiKey == null || apiKey.isEmpty) {
      throw Exception('未设置 API Key，请先在设置中配置');
    }

    final model = await getModel();
    final baseUrl = validateAndNormalizeBaseUrl(await getBaseUrl());

    final messages = <Map<String, dynamic>>[
      {'role': 'system', 'content': systemPrompt},
    ];

    if (imageBase64 != null) {
      final imageMimeType = _detectImageMimeType(imageBase64);
      messages.add({
        'role': 'user',
        'content': [
          {'type': 'text', 'text': userContent},
          {
            'type': 'image_url',
            'image_url': {'url': 'data:$imageMimeType;base64,$imageBase64'},
          },
        ],
      });
    } else {
      messages.add({'role': 'user', 'content': userContent});
    }

    final response = await _dio.post(
      '$baseUrl/chat/completions',
      options: Options(
        headers: {
          'Authorization': 'Bearer $apiKey',
          'Content-Type': 'application/json',
        },
      ),
      data: jsonEncode({
        'model': model,
        'messages': messages,
        'temperature': temperature ?? 0.7,
        'max_tokens': 4096,
      }),
    );

    if (response.statusCode != 200) {
      throw Exception('API 请求失败: ${response.statusCode}');
    }

    final data = response.data as Map<String, dynamic>;
    final choices = data['choices'] as List;
    if (choices.isEmpty) {
      throw Exception('API 返回空结果');
    }

    return choices[0]['message']['content'] as String;
  }

  static String _detectImageMimeType(String encodedImage) {
    try {
      final prefixLength = encodedImage.length < 32 ? encodedImage.length : 32;
      final alignedLength = prefixLength - (prefixLength % 4);
      final bytes = base64Decode(encodedImage.substring(0, alignedLength));
      if (bytes.length >= 8 &&
          bytes[0] == 0x89 &&
          bytes[1] == 0x50 &&
          bytes[2] == 0x4e &&
          bytes[3] == 0x47) {
        return 'image/png';
      }
      if (bytes.length >= 3 &&
          bytes[0] == 0xff &&
          bytes[1] == 0xd8 &&
          bytes[2] == 0xff) {
        return 'image/jpeg';
      }
      if (bytes.length >= 6 &&
          bytes[0] == 0x47 &&
          bytes[1] == 0x49 &&
          bytes[2] == 0x46) {
        return 'image/gif';
      }
      if (bytes.length >= 12 &&
          bytes[0] == 0x52 &&
          bytes[1] == 0x49 &&
          bytes[2] == 0x46 &&
          bytes[8] == 0x57 &&
          bytes[9] == 0x45 &&
          bytes[10] == 0x42 &&
          bytes[11] == 0x50) {
        return 'image/webp';
      }
      if (bytes.length >= 12 &&
          bytes[4] == 0x66 &&
          bytes[5] == 0x74 &&
          bytes[6] == 0x79 &&
          bytes[7] == 0x70 &&
          bytes[8] == 0x68 &&
          bytes[9] == 0x65 &&
          bytes[10] == 0x69) {
        return 'image/heic';
      }
    } on FormatException {
      // Existing callers only pass base64-encoded files; preserve the old fallback.
    }
    return 'image/jpeg';
  }

  /// AI 判断填空题答案是否正确
  ///
  /// 当用户答案与标准答案不完全匹配时，调用大模型判断语义是否等价。
  /// 返回 true 表示正确，false 表示错误。
  Future<bool> judgeFillBlankAnswer({
    required String question,
    required String userAnswer,
    required String correctAnswer,
  }) async {
    final systemPrompt = '你是一个判题助手。你的任务是判断用户的填空题答案是否与标准答案在语义上等价。'
        '允许的情况包括但不限于：同义词、近义词、不同的表述方式、大小写差异、标点差异、简称与全称。'
        '你只需要回答 JSON 格式：{"correct": true} 或 {"correct": false}，不要输出其他内容。';

    final userContent = '题目：$question\n'
        '标准答案：$correctAnswer\n'
        '用户答案：$userAnswer\n'
        '请判断用户答案是否正确。';

    try {
      final result = await chatCompletion(
        systemPrompt: systemPrompt,
        userContent: userContent,
        temperature: 0.0,
      );

      // 解析 JSON 结果
      final cleaned = result.trim();
      // 尝试提取 JSON
      final jsonMatch = RegExp(r'\{[^}]*\}').firstMatch(cleaned);
      if (jsonMatch != null) {
        final json = jsonDecode(jsonMatch.group(0)!) as Map<String, dynamic>;
        return json['correct'] == true;
      }
      // 如果不是 JSON，尝试直接匹配 true/false
      return cleaned.toLowerCase().contains('true');
    } catch (e) {
      // AI 判题失败时，回退到不通过
      return false;
    }
  }
}
