import 'package:shared_preferences/shared_preferences.dart';

import '../data/database/database_helper.dart';
import '../data/models/user_stats.dart';

/// 游戏化服务 - 管理 XP、连续打卡、心数、掌握度、月度打卡
class GamificationService {
  final DatabaseHelper _db;
  final DateTime Function() _clock;
  ({DateTime day, Future<UserStats> future})? _pendingRollover;

  GamificationService(this._db, {DateTime Function()? clock})
      : _clock = clock ?? DateTime.now;

  static const int xpPerCorrect = 10;
  static const int xpPerDeckComplete = 50;
  static const int xpPerPerfectDeck = 100;
  static const int streakBonusBase = 5; // 每天连续学习额外奖励基数
  static const String _lastHeartResetDateKey = 'last_heart_reset_date';

  /// 获取用户统计(自动检查每日重置)
  Future<UserStats> getStats() => _getStatsAt(_clock());

  Future<UserStats> _getStatsAt(DateTime now) async {
    while (true) {
      var pending = _pendingRollover;
      if (pending != null) {
        if (_isSameDay(pending.day, now)) return pending.future;
        await pending.future;
        continue;
      }

      final stats = await _db.getUserStats();
      pending = _pendingRollover;
      if (pending != null) {
        if (_isSameDay(pending.day, now)) return pending.future;
        await pending.future;
        continue;
      }
      if (_isSameDay(stats.lastStudyDate, now)) return stats;

      late final Future<UserStats> rollover;
      rollover = _rollover(stats, now).whenComplete(() {
        if (identical(_pendingRollover?.future, rollover)) {
          _pendingRollover = null;
        }
      });
      _pendingRollover = (
        day: DateTime(now.year, now.month, now.day),
        future: rollover,
      );
      return rollover;
    }
  }

  Future<UserStats> _rollover(UserStats stats, DateTime now) async {
    final prefs = await SharedPreferences.getInstance();
    final today = '${now.year}-${now.month}-${now.day}';
    if (prefs.getString(_lastHeartResetDateKey) == today) return stats;

    final resetStats = stats.copyWith(
      streak: _studiedYesterday(stats.lastStudyDate, now) ? stats.streak : 0,
      hearts: 99,
      maxHearts: 99,
      todayXp: 0,
    );
    await _db.updateUserStats(resetStats);
    if (!await prefs.setString(_lastHeartResetDateKey, today)) {
      await prefs.reload();
      throw StateError('failed to persist daily heart reset marker');
    }
    return resetStats;
  }

  /// 答对一题
  Future<UserStats> onCorrectAnswer() async {
    final now = _clock();
    var stats = await _getStatsAt(now);
    stats = stats.copyWith(
      xp: stats.xp + xpPerCorrect,
      todayXp: stats.todayXp + xpPerCorrect,
    );

    // 更新 streak
    if (!_isSameDay(stats.lastStudyDate, now)) {
      if (_studiedYesterday(stats.lastStudyDate, now)) {
        stats = stats.copyWith(streak: stats.streak + 1);
      } else {
        stats = stats.copyWith(streak: 1);
      }
      stats = stats.copyWith(lastStudyDate: now);
    }

    await _db.updateUserStats(stats);
    return stats;
  }

  /// 答错一题(扣心)
  Future<UserStats> onWrongAnswer() async {
    final now = _clock();
    var stats = await _getStatsAt(now);

    // 更新 streak (即使答错也记录今天学习了)
    if (!_isSameDay(stats.lastStudyDate, now)) {
      if (_studiedYesterday(stats.lastStudyDate, now)) {
        stats = stats.copyWith(streak: stats.streak + 1);
      } else {
        stats = stats.copyWith(streak: 1);
      }
      stats = stats.copyWith(lastStudyDate: now);
    }

    // 扣心
    if (stats.hearts > 0) {
      stats = stats.copyWith(hearts: stats.hearts - 1);
    }

    await _db.updateUserStats(stats);
    return stats;
  }

  /// 完成题包（含连续天数奖励）
  Future<UserStats> onDeckComplete({required bool allCorrect}) async {
    final now = _clock();
    var stats = await _getStatsAt(now);
    final bonus = allCorrect ? xpPerPerfectDeck : xpPerDeckComplete;
    // 连续天数额外奖励：streak * base
    final streakBonus = stats.streak * streakBonusBase;
    stats = stats.copyWith(
      xp: stats.xp + bonus + streakBonus,
      todayXp: stats.todayXp + bonus + streakBonus,
    );
    await _db.updateUserStats(stats);
    return stats;
  }

  /// 完美完成答题，恢复一颗心
  Future<UserStats> onPerfectQuiz() async {
    final now = _clock();
    var stats = await _getStatsAt(now);
    if (stats.hearts < stats.maxHearts) {
      stats = stats.copyWith(hearts: stats.hearts + 1);
      await _db.updateUserStats(stats);
    }
    return stats;
  }

  /// 检查心数是否为0
  bool isOutOfHearts(UserStats stats) => stats.hearts <= 0;

  /// 恢复一颗心
  Future<UserStats> refillOneHeart() async {
    final now = _clock();
    var stats = await _getStatsAt(now);
    if (stats.hearts < stats.maxHearts) {
      stats = stats.copyWith(hearts: stats.hearts + 1);
      await _db.updateUserStats(stats);
    }
    return stats;
  }

  /// 设置每日目标
  Future<void> setDailyGoal(int goal) async {
    final now = _clock();
    var stats = await _getStatsAt(now);
    stats = stats.copyWith(dailyGoal: goal);
    await _db.updateUserStats(stats);
  }

  /// 检查是否完成每日目标
  bool isDailyGoalComplete(UserStats stats) {
    return stats.todayXp >= stats.dailyGoal;
  }

  /// 计算题包掌握度
  int calculateMasteryLevel(int correctCount, int totalCount) {
    if (totalCount == 0) return 0;
    final accuracy = correctCount / totalCount;
    return (accuracy * 100).round();
  }

  // ============ 月度打卡系统 ============

  /// 记录今日打卡（每天只记一次）
  Future<void> recordCheckIn() async {
    final now = _clock();
    final prefs = await SharedPreferences.getInstance();
    final dateStr =
        '${now.year}-${now.month.toString().padLeft(2, '0')}-${now.day.toString().padLeft(2, '0')}';
    final monthKey = 'checkin_${now.year}_${now.month}';
    final dates = prefs.getStringList(monthKey) ?? [];
    if (!dates.contains(dateStr)) {
      dates.add(dateStr);
      await prefs.setStringList(monthKey, dates);
      // 达到 20 天自动颁发勋章
      if (dates.length >= 20) {
        await prefs.setBool('medal_${now.year}_${now.month}', true);
      }
    }
  }

  /// 获取某月打卡日期列表
  Future<List<String>> getMonthlyCheckInDates(int year, int month) async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getStringList('checkin_${year}_$month') ?? [];
  }

  /// 获取某月打卡天数
  Future<int> getMonthlyCheckInCount(int year, int month) async {
    return (await getMonthlyCheckInDates(year, month)).length;
  }

  /// 检查某月是否获得勋章（20天+）
  Future<bool> hasMonthlyMedal(int year, int month) async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getBool('medal_${year}_$month') ?? false;
  }

  /// 获取所有已获得的月度勋章
  Future<List<({int year, int month})>> getEarnedMedals() async {
    final prefs = await SharedPreferences.getInstance();
    final keys = prefs
        .getKeys()
        .where((k) => k.startsWith('medal_') && prefs.getBool(k) == true);
    final medals = <({int year, int month})>[];
    for (final key in keys) {
      final parts = key.split('_');
      if (parts.length == 3) {
        medals.add((year: int.parse(parts[1]), month: int.parse(parts[2])));
      }
    }
    medals.sort((a, b) {
      if (a.year != b.year) return b.year.compareTo(a.year);
      return b.month.compareTo(a.month);
    });
    return medals;
  }

  // ============ 答题统计 ============

  /// 增加答对题数
  Future<int> incrementTotalCorrect() async {
    final prefs = await SharedPreferences.getInstance();
    final val = (prefs.getInt('total_correct') ?? 0) + 1;
    await prefs.setInt('total_correct', val);
    return val;
  }

  /// 获取总答对题数
  Future<int> getTotalCorrect() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getInt('total_correct') ?? 0;
  }

  /// 增加完美通关次数
  Future<int> incrementPerfectCount() async {
    final prefs = await SharedPreferences.getInstance();
    final val = (prefs.getInt('perfect_count') ?? 0) + 1;
    await prefs.setInt('perfect_count', val);
    return val;
  }

  /// 获取完美通关次数
  Future<int> getPerfectCount() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getInt('perfect_count') ?? 0;
  }

  bool _isSameDay(DateTime date, DateTime other) {
    return date.year == other.year &&
        date.month == other.month &&
        date.day == other.day;
  }

  bool _studiedYesterday(DateTime lastStudyDate, DateTime now) {
    return _isSameDay(
      lastStudyDate,
      DateTime(now.year, now.month, now.day - 1),
    );
  }
}
