import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/constants/app_colors.dart';
import '../../core/providers/providers.dart';
import '../../services/shared_image_store.dart';
import '../../shared/widgets/duo_button.dart';
import 'deck_preview_screen.dart';

typedef SharedImageLoader = Future<String> Function(String imagePath);

Future<String> _loadSharedImage(String imagePath) async {
  final bytes = await File(imagePath).readAsBytes();
  return base64Encode(bytes);
}

class IngestionScreen extends ConsumerStatefulWidget {
  final String? sharedText;
  final String? sharedImagePath;
  final SharedImageLoader imageLoader;

  const IngestionScreen({
    super.key,
    this.sharedText,
    this.sharedImagePath,
    this.imageLoader = _loadSharedImage,
  });

  @override
  ConsumerState<IngestionScreen> createState() => _IngestionScreenState();
}

class _IngestionScreenState extends ConsumerState<IngestionScreen> {
  final _textController = TextEditingController();
  String? _imagePath;
  String? _imageBase64;
  bool _isAnalyzing = false;
  String _statusText = '';
  String? _errorMessage;
  bool _imageTransferred = false;
  bool _isImageLoading = false;

  @override
  void initState() {
    super.initState();
    if (widget.sharedText != null && widget.sharedText!.isNotEmpty) {
      _textController.text = widget.sharedText!;
    }
    if (widget.sharedImagePath != null) {
      _imagePath = widget.sharedImagePath;
      _isImageLoading = true;
      _loadImageBase64();
    }
  }

  Future<void> _loadImageBase64() async {
    if (_imagePath == null) return;
    try {
      final imageBase64 = await widget.imageLoader(_imagePath!);
      if (!mounted) return;
      setState(() {
        _imageBase64 = imageBase64;
        _isImageLoading = false;
      });
    } catch (_) {
      if (!mounted) return;
      setState(() {
        _isImageLoading = false;
        _errorMessage = '图片读取失败，请重新分享或选择其他图片';
      });
    }
  }

  Future<void> _pasteFromClipboard() async {
    final clipData = await Clipboard.getData('text/plain');
    if (!mounted) return;
    if (clipData?.text != null && clipData!.text!.isNotEmpty) {
      setState(() {
        _textController.text = clipData.text!;
      });
    }
  }

  Future<void> _analyze() async {
    final text = _textController.text.trim();
    if (text.isEmpty && _imageBase64 == null) {
      setState(() => _errorMessage = '请输入或粘贴内容');
      return;
    }

    // 检查 API Key
    late final bool hasKey;
    try {
      hasKey = await ref.read(openaiServiceProvider).hasApiKey();
    } catch (error) {
      if (!mounted) return;
      setState(() => _errorMessage = '无法读取 API Key: $error');
      return;
    }
    if (!mounted) return;
    if (!hasKey) {
      setState(() => _errorMessage = '请先在设置中配置 OpenAI API Key');
      return;
    }

    setState(() {
      _isAnalyzing = true;
      _errorMessage = null;
      _statusText = '正在分析内容...';
    });

    try {
      final analyzer = ref.read(contentAnalyzerProvider);

      setState(() => _statusText = 'AI 正在拆解知识点...');
      final result = await analyzer.analyze(
        text: text,
        imageBase64: _imageBase64,
      );

      if (!mounted) return;
      setState(() => _statusText = '正在生成题目...');
      await Future.delayed(const Duration(milliseconds: 500));

      if (mounted) {
        setState(() => _isAnalyzing = false);
        // 跳转到预览页，用户确认后再保存
        _imageTransferred = true;
        Navigator.of(context).pushReplacement(
          MaterialPageRoute(
            builder: (_) => DeckPreviewScreen(
              result: result,
              sourceText: text,
              sourceImage: _imagePath,
            ),
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _isAnalyzing = false;
          _errorMessage = '分析失败: $e';
        });
      }
    }
  }

  @override
  void dispose() {
    if (!_imageTransferred) {
      unawaited(deleteOwnedImage(_imagePath));
    }
    _textController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('添加内容'),
        leading: IconButton(
          icon: const Icon(Icons.close),
          onPressed: () => Navigator.of(context).pop(),
        ),
      ),
      body: SafeArea(
        child: _isAnalyzing ? _buildLoadingView() : _buildInputView(),
      ),
    );
  }

  Widget _buildInputView() {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // 说明
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: AppColors.blueLight,
              borderRadius: BorderRadius.circular(16),
            ),
            child: Row(
              children: [
                const Icon(Icons.lightbulb, color: AppColors.blue, size: 24),
                const SizedBox(width: 12),
                Expanded(
                  child: Text(
                    '粘贴你在知乎、小红书等看到的知识内容，AI 会自动拆解为题目',
                    style: TextStyle(
                      fontSize: 14,
                      color: AppColors.blueDark,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),
          // 图片预览
          if (_imagePath != null) ...[
            ClipRRect(
              borderRadius: BorderRadius.circular(16),
              child: Image.file(
                File(_imagePath!),
                height: 200,
                width: double.infinity,
                fit: BoxFit.cover,
                errorBuilder: (_, __, ___) => Container(
                  height: 200,
                  color: AppColors.surface,
                  child: const Center(child: Icon(Icons.broken_image, size: 48)),
                ),
              ),
            ),
            const SizedBox(height: 12),
          ],
          // 文本输入区
          TextField(
            controller: _textController,
            maxLines: 10,
            decoration: InputDecoration(
              hintText: '在此粘贴或输入要学习的内容...\n\n例如：\n• 知乎文章片段\n• 小红书知识笔记\n• 任何你想记住的内容',
              hintStyle: TextStyle(color: AppColors.textLight, height: 1.8),
              filled: true,
              fillColor: AppColors.surface,
              border: OutlineInputBorder(
                borderRadius: BorderRadius.circular(16),
                borderSide: BorderSide.none,
              ),
              focusedBorder: OutlineInputBorder(
                borderRadius: BorderRadius.circular(16),
                borderSide: const BorderSide(color: AppColors.blue, width: 2),
              ),
            ),
          ),
          const SizedBox(height: 12),
          // 粘贴按钮
          Row(
            children: [
              Expanded(
                child: OutlinedButton.icon(
                  onPressed: _pasteFromClipboard,
                  icon: const Icon(Icons.content_paste, size: 20),
                  label: const Text('从粘贴板粘贴'),
                  style: OutlinedButton.styleFrom(
                    foregroundColor: AppColors.blue,
                    side: const BorderSide(color: AppColors.blue, width: 2),
                    padding: const EdgeInsets.symmetric(vertical: 14),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(16),
                    ),
                  ),
                ),
              ),
            ],
          ),
          // 错误信息
          if (_errorMessage != null) ...[
            const SizedBox(height: 12),
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: AppColors.redLight,
                borderRadius: BorderRadius.circular(12),
              ),
              child: Row(
                children: [
                  const Icon(Icons.error, color: AppColors.red, size: 20),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      _errorMessage!,
                      style: const TextStyle(color: AppColors.redDark, fontSize: 14),
                    ),
                  ),
                ],
              ),
            ),
          ],
          const SizedBox(height: 24),
          // 开始拆解按钮
          DuoButton(
            label: 'AI 拆解为题目',
            color: AppColors.green,
            width: double.infinity,
            height: 56,
            icon: Icons.auto_awesome,
            fontSize: 18,
            enabled: !_isImageLoading,
            onPressed: _analyze,
          ),
        ],
      ),
    );
  }

  Widget _buildLoadingView() {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            // 动画图标
            Container(
              width: 80,
              height: 80,
              decoration: BoxDecoration(
                color: AppColors.greenLight,
                shape: BoxShape.circle,
              ),
              child: const Icon(
                Icons.auto_awesome,
                color: AppColors.green,
                size: 40,
              ),
            ).animate(
              onPlay: (controller) => controller.repeat(),
            ).shimmer(duration: 1500.ms),
            const SizedBox(height: 24),
            Text(
              _statusText,
              style: const TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.w700,
                color: AppColors.textPrimary,
              ),
            ),
            const SizedBox(height: 8),
            const Text(
              'AI 正在分析内容并生成题目，请稍候...',
              style: TextStyle(
                fontSize: 14,
                color: AppColors.textSecondary,
              ),
            ),
            const SizedBox(height: 32),
            // 进度指示器
            const SizedBox(
              width: 200,
              child: LinearProgressIndicator(
                backgroundColor: AppColors.surface,
                color: AppColors.green,
                minHeight: 8,
                borderRadius: BorderRadius.all(Radius.circular(4)),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
