import 'dart:async';

import 'package:dlg_q/data/database/database_helper.dart';
import 'package:dlg_q/data/models/user_stats.dart';
import 'package:dlg_q/services/gamification_service.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:shared_preferences_platform_interface/shared_preferences_platform_interface.dart';

class _FailFirstMarkerWritePreferencesStore
    extends InMemorySharedPreferencesStore {
  _FailFirstMarkerWritePreferencesStore() : super.empty();

  int markerWriteCount = 0;

  @override
  Future<bool> setValue(String valueType, String key, Object value) async {
    if (key == 'flutter.last_heart_reset_date') {
      markerWriteCount++;
      if (markerWriteCount == 1) return false;
    }
    return super.setValue(valueType, key, value);
  }
}

class _FakeDatabaseHelper implements DatabaseHelper {
  _FakeDatabaseHelper(this.stats);

  UserStats stats;
  int updateCount = 0;
  bool failNextUpdate = false;

  @override
  Future<UserStats> getUserStats() async => stats;

  @override
  Future<void> updateUserStats(UserStats stats) async {
    updateCount++;
    if (failNextUpdate) {
      failNextUpdate = false;
      throw StateError('update failed');
    }
    this.stats = stats;
  }

  @override
  dynamic noSuchMethod(Invocation invocation) => super.noSuchMethod(invocation);
}

class _TwoReadBarrierDatabaseHelper extends _FakeDatabaseHelper {
  _TwoReadBarrierDatabaseHelper(super.stats);

  final _bothReadsStarted = Completer<void>();
  int _readCount = 0;

  @override
  Future<UserStats> getUserStats() async {
    final snapshot = stats;
    _readCount++;
    if (_readCount == 2) _bothReadsStarted.complete();
    await _bothReadsStarted.future;
    return snapshot;
  }
}

class _FirstUpdateBarrierDatabaseHelper extends _FakeDatabaseHelper {
  _FirstUpdateBarrierDatabaseHelper(super.stats);

  final firstUpdateStarted = Completer<void>();
  final releaseFirstUpdate = Completer<void>();
  int readCount = 0;

  @override
  Future<UserStats> getUserStats() async {
    readCount++;
    return super.getUserStats();
  }

  @override
  Future<void> updateUserStats(UserStats stats) async {
    updateCount++;
    if (updateCount == 1) {
      firstUpdateStarted.complete();
      await releaseFirstUpdate.future;
    }
    this.stats = stats;
  }
}

class _MidnightClock {
  _MidnightClock(this.beforeMidnight, this.afterMidnight);

  final DateTime beforeMidnight;
  final DateTime afterMidnight;
  int callCount = 0;

  DateTime call() => callCount++ == 0 ? beforeMidnight : afterMidnight;
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  setUp(() {
    SharedPreferences.setMockInitialValues({});
  });

  test('first rollover from yesterday restores hearts and preserves streak',
      () async {
    final now = DateTime.now();
    final lastStudyDate = DateTime(now.year, now.month, now.day - 1);
    final db = _FakeDatabaseHelper(
      UserStats(
        xp: 120,
        streak: 7,
        hearts: 0,
        maxHearts: 5,
        lastStudyDate: lastStudyDate,
        dailyGoal: 30,
        todayXp: 20,
      ),
    );

    final stats = await GamificationService(db).getStats();

    expect(stats.hearts, 99);
    expect(stats.maxHearts, 99);
    expect(stats.todayXp, 0);
    expect(stats.streak, 7);
    expect(stats.lastStudyDate, lastStudyDate);
    expect(stats.xp, 120);
    expect(stats.dailyGoal, 30);
    expect(db.stats, same(stats));
    expect(db.updateCount, 1);
  });

  test('first rollover after a missed day resets streak', () async {
    final now = DateTime.now();
    final lastStudyDate = DateTime(now.year, now.month, now.day - 2);
    final db = _FakeDatabaseHelper(
      UserStats(
        streak: 7,
        hearts: 0,
        lastStudyDate: lastStudyDate,
        todayXp: 20,
      ),
    );

    final stats = await GamificationService(db).getStats();

    expect(stats.hearts, 99);
    expect(stats.maxHearts, 99);
    expect(stats.todayXp, 0);
    expect(stats.streak, 0);
    expect(stats.lastStudyDate, lastStudyDate);
    expect(db.updateCount, 1);
  });

  test('stats from today are not reset', () async {
    final now = DateTime.now();
    final lastStudyDate = DateTime(now.year, now.month, now.day);
    final db = _FakeDatabaseHelper(
      UserStats(
        streak: 7,
        hearts: 3,
        maxHearts: 5,
        lastStudyDate: lastStudyDate,
        todayXp: 20,
      ),
    );

    final stats = await GamificationService(db).getStats();

    expect(stats.hearts, 3);
    expect(stats.maxHearts, 5);
    expect(stats.todayXp, 20);
    expect(stats.streak, 7);
    expect(stats.lastStudyDate, lastStudyDate);
    expect(db.updateCount, 0);
  });

  test('getStats only restores hearts once per day', () async {
    final now = DateTime.now();
    final db = _FakeDatabaseHelper(
      UserStats(
        hearts: 0,
        lastStudyDate: DateTime(now.year, now.month, now.day - 1),
      ),
    );
    final service = GamificationService(db);

    final first = await service.getStats();
    db.stats = first.copyWith(hearts: 98);
    final second = await service.getStats();

    expect(second.hearts, 98);
    expect(second.maxHearts, 99);
    expect(db.updateCount, 1);
  });

  test('concurrent rollover and wrong answer share a single reset', () async {
    final now = DateTime.now();
    final db = _TwoReadBarrierDatabaseHelper(
      UserStats(
        hearts: 0,
        lastStudyDate: DateTime(now.year, now.month, now.day - 1),
      ),
    );
    final service = GamificationService(db);

    await Future.wait([service.getStats(), service.onWrongAnswer()]);

    expect(db.stats.hearts, 98);
    expect(db.updateCount, 2);
  });

  test('rollover pending across midnight is rerun for the captured day',
      () async {
    var now = DateTime(2040, 5, 2, 23, 59, 59);
    final db = _FirstUpdateBarrierDatabaseHelper(
      UserStats(
        hearts: 0,
        lastStudyDate: DateTime(2040, 5, 1, 12),
        todayXp: 40,
      ),
    );
    final service = GamificationService(db, clock: () => now);

    final dayDRollover = service.getStats();
    await db.firstUpdateStarted.future;
    now = DateTime(2040, 5, 3);
    final dayDPlusOneRollover = service.getStats();

    db.releaseFirstUpdate.complete();
    await Future.wait([dayDRollover, dayDPlusOneRollover]);

    expect(db.readCount, 2);
    expect(db.updateCount, 2);
    expect(
      (await SharedPreferences.getInstance())
          .getString('last_heart_reset_date'),
      '2040-5-3',
    );
  });

  test('correct answer uses one captured time across midnight', () async {
    final clock = _MidnightClock(
      DateTime(2040, 5, 2, 23, 59, 59),
      DateTime(2040, 5, 3),
    );
    final db = _FakeDatabaseHelper(
      UserStats(
        xp: 120,
        streak: 7,
        hearts: 0,
        lastStudyDate: DateTime(2040, 5, 1, 12),
        todayXp: 40,
      ),
    );
    final service = GamificationService(db, clock: clock.call);

    final stats = await service.onCorrectAnswer();

    expect(clock.callCount, 1);
    expect(stats.xp, 130);
    expect(stats.todayXp, 10);
    expect(stats.hearts, 99);
    expect(stats.streak, 8);
    expect(stats.lastStudyDate, clock.beforeMidnight);
  });

  test('wrong answer uses one captured time across midnight', () async {
    final clock = _MidnightClock(
      DateTime(2040, 5, 2, 23, 59, 59),
      DateTime(2040, 5, 3),
    );
    final db = _FakeDatabaseHelper(
      UserStats(
        streak: 7,
        hearts: 0,
        lastStudyDate: DateTime(2040, 5, 1, 12),
        todayXp: 40,
      ),
    );
    final service = GamificationService(db, clock: clock.call);

    final stats = await service.onWrongAnswer();

    expect(clock.callCount, 1);
    expect(stats.todayXp, 0);
    expect(stats.hearts, 98);
    expect(stats.streak, 8);
    expect(stats.lastStudyDate, clock.beforeMidnight);
  });

  test('a failed database reset is retried', () async {
    final now = DateTime.now();
    final db = _FakeDatabaseHelper(
      UserStats(
        hearts: 0,
        lastStudyDate: DateTime(now.year, now.month, now.day - 1),
      ),
    )..failNextUpdate = true;
    final service = GamificationService(db);

    await expectLater(service.getStats(), throwsStateError);
    final stats = await service.getStats();

    expect(stats.hearts, 99);
    expect(db.updateCount, 2);
  });

  test('a failed reset marker write reloads cache and retries after restart',
      () async {
    final store = _FailFirstMarkerWritePreferencesStore();
    SharedPreferencesStorePlatform.instance = store;
    SharedPreferences.resetStatic();
    final now = DateTime.now();
    final db = _FakeDatabaseHelper(
      UserStats(
        hearts: 0,
        lastStudyDate: DateTime(now.year, now.month, now.day - 1),
      ),
    );

    await expectLater(
      GamificationService(db).getStats(),
      throwsA(isA<StateError>()),
    );
    expect(
      (await SharedPreferences.getInstance())
          .getString('last_heart_reset_date'),
      isNull,
    );

    SharedPreferences.resetStatic();
    final stats = await GamificationService(db).getStats();

    expect(stats.hearts, 99);
    expect(db.updateCount, 2);
    expect(store.markerWriteCount, 2);
  });
}
