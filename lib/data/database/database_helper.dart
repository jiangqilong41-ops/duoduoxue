import 'package:path/path.dart';
import 'package:sqflite/sqflite.dart';
import '../../services/shared_image_store.dart';
import '../models/deck.dart';
import '../models/question.dart';
import '../models/study_record.dart';
import '../models/user_stats.dart';

/// SQLite 数据库帮助类
class DatabaseHelper {
  static final DatabaseHelper _instance = DatabaseHelper._internal();
  factory DatabaseHelper() => _instance;
  DatabaseHelper._internal();

  Database? _database;

  Future<Database> get database async {
    if (_database != null) return _database!;
    _database = await _initDatabase();
    return _database!;
  }

  Future<Database> _initDatabase() async {
    final dbPath = await getDatabasesPath();
    final path = join(dbPath, 'dlg_q.db');
    return await openDatabase(
      path,
      version: 1,
      onCreate: _onCreate,
    );
  }

  Future<void> _onCreate(Database db, int version) async {
    // 题包表
    await db.execute('''
      CREATE TABLE decks (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        source_text TEXT,
        source_image TEXT,
        question_count INTEGER DEFAULT 0,
        mastery_level INTEGER DEFAULT 0,
        created_at INTEGER NOT NULL,
        updated_at INTEGER NOT NULL
      )
    ''');

    // 题目表
    await db.execute('''
      CREATE TABLE questions (
        id TEXT PRIMARY KEY,
        deck_id TEXT NOT NULL,
        type TEXT NOT NULL,
        content TEXT NOT NULL,
        options TEXT,
        answer TEXT NOT NULL,
        explanation TEXT,
        match_left TEXT,
        match_right TEXT,
        FOREIGN KEY (deck_id) REFERENCES decks(id) ON DELETE CASCADE
      )
    ''');

    // 学习记录表
    await db.execute('''
      CREATE TABLE study_records (
        id TEXT PRIMARY KEY,
        deck_id TEXT NOT NULL,
        correct_count INTEGER DEFAULT 0,
        total_count INTEGER DEFAULT 0,
        last_studied_at INTEGER NOT NULL,
        FOREIGN KEY (deck_id) REFERENCES decks(id) ON DELETE CASCADE
      )
    ''');

    // 用户统计表(单行)
    await db.execute('''
      CREATE TABLE user_stats (
        id INTEGER PRIMARY KEY DEFAULT 1,
        xp INTEGER DEFAULT 0,
        streak INTEGER DEFAULT 0,
        hearts INTEGER DEFAULT 5,
        max_hearts INTEGER DEFAULT 5,
        last_study_date INTEGER NOT NULL,
        daily_goal INTEGER DEFAULT 50,
        today_xp INTEGER DEFAULT 0
      )
    ''');

    // 初始化用户统计
    await db.insert('user_stats', {
      'id': 1,
      'xp': 0,
      'streak': 0,
      'hearts': 5,
      'max_hearts': 5,
      'last_study_date': DateTime.now().millisecondsSinceEpoch,
      'daily_goal': 50,
      'today_xp': 0,
    });
  }

  // ============ Deck 操作 ============

  Future<String> insertDeck(Deck deck) async {
    final db = await database;
    await db.insert('decks', deck.toMap());
    return deck.id;
  }

  Future<List<Deck>> getAllDecks() async {
    final db = await database;
    final maps = await db.query('decks', orderBy: 'created_at DESC');
    return maps.map(Deck.fromMap).toList();
  }

  Future<Deck?> getDeck(String id) async {
    final db = await database;
    final maps = await db.query('decks', where: 'id = ?', whereArgs: [id]);
    if (maps.isEmpty) return null;
    return Deck.fromMap(maps.first);
  }

  Future<void> updateDeck(Deck deck) async {
    final db = await database;
    await db.update('decks', deck.toMap(), where: 'id = ?', whereArgs: [deck.id]);
  }

  Future<void> deleteDeck(String id) async {
    final db = await database;
    final deck = await getDeck(id);
    await db.delete('questions', where: 'deck_id = ?', whereArgs: [id]);
    await db.delete('study_records', where: 'deck_id = ?', whereArgs: [id]);
    await db.delete('decks', where: 'id = ?', whereArgs: [id]);
    try {
      await deleteOwnedImage(deck?.sourceImage);
    } catch (_) {
      // Database deletion has committed; leave cleanup as best effort.
    }
  }

  // ============ Question 操作 ============

  Future<String> insertQuestion(Question question) async {
    final db = await database;
    final id = question.id.isEmpty ? DateTime.now().microsecondsSinceEpoch.toString() : question.id;
    final q = Question(
      id: id,
      deckId: question.deckId,
      type: question.type,
      content: question.content,
      options: question.options,
      answer: question.answer,
      explanation: question.explanation,
      matchLeft: question.matchLeft,
      matchRight: question.matchRight,
    );
    await db.insert('questions', q.toMap());
    return id;
  }

  Future<List<Question>> getQuestionsByDeck(String deckId) async {
    final db = await database;
    final maps = await db.query('questions', where: 'deck_id = ?', whereArgs: [deckId]);
    return maps.map(Question.fromMap).toList();
  }

  // ============ 随机抽题 ============

  /// 获取所有题目（跨题包）
  Future<List<Question>> getAllQuestions() async {
    final db = await database;
    final maps = await db.query('questions');
    return maps.map(Question.fromMap).toList();
  }

  /// 随机抽取指定数量的题目
  Future<List<Question>> getRandomQuestions(int count) async {
    final db = await database;
    final maps = await db.rawQuery(
      'SELECT * FROM questions ORDER BY RANDOM() LIMIT ?',
      [count],
    );
    return maps.map(Question.fromMap).toList();
  }

  // ============ StudyRecord 操作 ============

  Future<void> upsertStudyRecord(StudyRecord record) async {
    final db = await database;
    await db.insert('study_records', record.toMap(),
        conflictAlgorithm: ConflictAlgorithm.replace);
  }

  Future<StudyRecord?> getStudyRecord(String deckId) async {
    final db = await database;
    final maps = await db.query('study_records', where: 'deck_id = ?', whereArgs: [deckId]);
    if (maps.isEmpty) return null;
    return StudyRecord.fromMap(maps.first);
  }

  // ============ UserStats 操作 ============

  Future<UserStats> getUserStats() async {
    final db = await database;
    final maps = await db.query('user_stats', where: 'id = 1');
    if (maps.isEmpty) {
      return UserStats(lastStudyDate: DateTime.now());
    }
    return UserStats.fromMap(maps.first);
  }

  Future<void> updateUserStats(UserStats stats) async {
    final db = await database;
    await db.update('user_stats', stats.toMap(), where: 'id = 1');
  }
}
