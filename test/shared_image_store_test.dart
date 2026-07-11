import 'dart:io';

import 'package:dlg_q/services/shared_image_store.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:path/path.dart' as path;

void main() {
  late Directory sandbox;

  setUp(() async {
    sandbox = await Directory.systemTemp.createTemp('duoduoxue_images_');
  });

  tearDown(() async {
    if (await sandbox.exists()) {
      await sandbox.delete(recursive: true);
    }
  });

  test('imports a temporary image and removes the source file', () async {
    final source = File(path.join(sandbox.path, 'shared.png'));
    const bytes = <int>[1, 2, 3, 4];
    await source.writeAsBytes(bytes);
    final supportRoot = Directory(path.join(sandbox.path, 'support'));

    final importedPath = await importTemporaryImage(
      source.path,
      root: supportRoot,
    );

    expect(await File(importedPath).readAsBytes(), bytes);
    expect(
        path.isWithin(
          path.join(supportRoot.path, 'source_images'),
          importedPath,
        ),
        isTrue);
    expect(await source.exists(), isFalse);
  });

  test('removes the temporary source when importing fails', () async {
    final source = File(path.join(sandbox.path, 'shared.png'));
    await source.writeAsBytes([1, 2, 3]);
    final supportRoot = Directory(path.join(sandbox.path, 'support'));
    await File(path.join(supportRoot.path, 'source_images'))
        .create(recursive: true);

    await expectLater(
      importTemporaryImage(source.path, root: supportRoot),
      throwsA(isA<FileSystemException>()),
    );

    expect(await source.exists(), isFalse);
  });

  test('keeps the imported copy when temporary source cleanup fails', () async {
    if (Platform.isWindows) return;
    final sourceDirectory = Directory(path.join(sandbox.path, 'readonly'));
    final source = File(path.join(sourceDirectory.path, 'shared.png'));
    const bytes = <int>[5, 6, 7, 8];
    await source.create(recursive: true);
    await source.writeAsBytes(bytes);
    final supportRoot = Directory(path.join(sandbox.path, 'support'));
    final locked = await Process.run('chmod', ['0555', sourceDirectory.path]);
    expect(locked.exitCode, 0);

    try {
      final importedPath = await importTemporaryImage(
        source.path,
        root: supportRoot,
      );

      expect(await File(importedPath).readAsBytes(), bytes);
      expect(await source.exists(), isTrue);
    } finally {
      await Process.run('chmod', ['0755', sourceDirectory.path]);
    }
  });

  test('deletes only images owned by the application', () async {
    final supportRoot = Directory(path.join(sandbox.path, 'support'));
    final owned = File(
      path.join(supportRoot.path, 'source_images', 'owned.png'),
    );
    final outside = File(path.join(sandbox.path, 'outside.png'));
    await owned.create(recursive: true);
    await outside.create();

    await deleteOwnedImage(owned.path, root: supportRoot);
    await deleteOwnedImage(owned.path, root: supportRoot);
    await deleteOwnedImage(outside.path, root: supportRoot);

    expect(await owned.exists(), isFalse);
    expect(await outside.exists(), isTrue);
  });

  test('does not confuse a sibling directory with the owned directory',
      () async {
    final supportRoot = Directory(path.join(sandbox.path, 'support'));
    final sibling = File(
      path.join(supportRoot.path, 'source_images_backup', 'outside.png'),
    );
    await sibling.create(recursive: true);

    await deleteOwnedImage(sibling.path, root: supportRoot);

    expect(await sibling.exists(), isTrue);
  });
}
