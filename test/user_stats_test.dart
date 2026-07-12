import 'dart:io';

import 'package:dlg_q/data/models/user_stats.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('new user stats start with 99 hearts', () {
    final stats = UserStats(lastStudyDate: DateTime(2026));

    expect(stats.hearts, 99);
    expect(stats.maxHearts, 99);
  });

  test('missing persisted heart values fall back to 99', () {
    final stats = UserStats.fromMap({
      'last_study_date': DateTime(2026).millisecondsSinceEpoch,
    });

    expect(stats.hearts, 99);
    expect(stats.maxHearts, 99);
  });

  test('new database schema and seed start with 99 hearts', () {
    final source =
        File('lib/data/database/database_helper.dart').readAsStringSync();

    expect(source, contains('hearts INTEGER DEFAULT 99'));
    expect(source, contains('max_hearts INTEGER DEFAULT 99'));
    expect(source, contains("'hearts': 99"));
    expect(source, contains("'max_hearts': 99"));
  });
}
