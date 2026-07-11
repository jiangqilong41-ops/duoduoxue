import 'dart:io';

import 'package:path/path.dart' as path;
import 'package:path_provider/path_provider.dart';

Future<String> importTemporaryImage(
  String imagePath, {
  Directory? root,
}) async {
  final supportRoot = root ?? await getApplicationSupportDirectory();
  final uri = Uri.tryParse(imagePath);
  final source =
      uri != null && uri.scheme == 'file' ? File.fromUri(uri) : File(imagePath);
  final imageDirectory = Directory(
    path.join(supportRoot.path, 'source_images'),
  );

  late File destination;
  try {
    await imageDirectory.create(recursive: true);
    final extension = path.extension(source.path);
    destination = File(
      path.join(
        imageDirectory.path,
        '${DateTime.now().microsecondsSinceEpoch}${extension.isEmpty ? '.img' : extension}',
      ),
    );
    await source.copy(destination.path);
  } catch (_) {
    await _deleteTemporarySource(source);
    rethrow;
  }
  await _deleteTemporarySource(source);
  return destination.path;
}

Future<void> _deleteTemporarySource(File source) async {
  try {
    if (await source.exists()) await source.delete();
  } on FileSystemException {
    // A completed persistent copy remains usable even if temp cleanup fails.
  }
}

Future<void> deleteOwnedImage(
  String? imagePath, {
  Directory? root,
}) async {
  if (imagePath == null || imagePath.isEmpty) return;

  final supportRoot = root ?? await getApplicationSupportDirectory();
  final imageDirectory = Directory(
    path.join(supportRoot.path, 'source_images'),
  );
  final image = File(imagePath);
  if (!await imageDirectory.exists() || !await image.exists()) return;

  final ownedRoot = await imageDirectory.resolveSymbolicLinks();
  final resolvedImage = await image.resolveSymbolicLinks();
  if (!path.isWithin(ownedRoot, resolvedImage)) return;

  try {
    await image.delete();
  } on FileSystemException {
    if (await image.exists()) rethrow;
  }
}
