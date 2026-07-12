import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:receive_sharing_intent/receive_sharing_intent.dart';
import 'core/providers/providers.dart';
import 'services/shared_image_store.dart';
import '../features/home/home_screen.dart';
import '../features/deck/deck_list_screen.dart';
import '../features/profile/profile_screen.dart';
import '../features/ingestion/ingestion_screen.dart';

({String? text, String? imagePath}) selectSharedMedia(
  List<SharedMediaFile> files,
) {
  String? text;
  String? imagePath;

  for (final file in files) {
    if (text == null &&
        (file.type == SharedMediaType.text ||
            file.type == SharedMediaType.url)) {
      text = file.path;
    } else if (imagePath == null && file.type == SharedMediaType.image) {
      imagePath = file.path;
    }
    if (text != null && imagePath != null) break;
  }

  return (text: text, imagePath: imagePath);
}

class MainApp extends ConsumerStatefulWidget {
  const MainApp({super.key});

  @override
  ConsumerState<MainApp> createState() => _MainAppState();
}

class _MainAppState extends ConsumerState<MainApp> with WidgetsBindingObserver {
  int _currentIndex = 0;
  StreamSubscription? _sharingSubscription;

  final _screens = const [
    HomeScreen(),
    DeckListScreen(),
    ProfileScreen(),
  ];

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    _initSharingIntent();
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.resumed) {
      unawaited(ref.read(userStatsProvider.notifier).refresh());
    }
  }

  void _initSharingIntent() {
    try {
      // 处理 APP 通过分享启动时的内容(文本和图片)
      ReceiveSharingIntent.instance
          .getInitialMedia()
          .then((List<SharedMediaFile> files) async {
        if (files.isNotEmpty) {
          await _handleSharedFiles(files);
        }
        await ReceiveSharingIntent.instance.reset();
      }).catchError((_) {});

      // 监听 APP 运行时的分享事件
      _sharingSubscription = ReceiveSharingIntent.instance
          .getMediaStream()
          .listen((List<SharedMediaFile> files) {
        if (files.isNotEmpty) {
          unawaited(_handleSharedFiles(files));
        }
      }, onError: (_) {});
    } catch (e) {
      // release 模式下初始化失败时静默处理，不影响正常渲染
    }
  }

  Future<void> _handleSharedFiles(List<SharedMediaFile> files) async {
    final selected = selectSharedMedia(files);
    String? imagePath;
    if (selected.imagePath != null) {
      try {
        imagePath = await importTemporaryImage(selected.imagePath!);
      } catch (_) {
        imagePath = null;
      }
    }

    if (!mounted) {
      await deleteOwnedImage(imagePath);
      return;
    }

    if (selected.text != null || imagePath != null) {
      Navigator.of(context).push(
        MaterialPageRoute(
          builder: (_) => IngestionScreen(
            sharedText: selected.text,
            sharedImagePath: imagePath,
          ),
        ),
      );
    }
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    _sharingSubscription?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: IndexedStack(
        index: _currentIndex,
        children: _screens,
      ),
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: _currentIndex,
        onTap: (index) => setState(() => _currentIndex = index),
        items: const [
          BottomNavigationBarItem(
            icon: Icon(Icons.home_outlined),
            activeIcon: Icon(Icons.home),
            label: '学习',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.quiz_outlined),
            activeIcon: Icon(Icons.quiz),
            label: '题库',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.person_outline),
            activeIcon: Icon(Icons.person),
            label: '我的',
          ),
        ],
      ),
    );
  }
}
