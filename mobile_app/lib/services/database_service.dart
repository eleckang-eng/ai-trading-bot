import 'package:sqflite/sqflite.dart';
import 'package:path/path.dart';

class DatabaseService {
  static final DatabaseService instance = DatabaseService._init();
  static Database? _database;

  DatabaseService._init();

  Future<Database> get database async {
    if (_database != null) return _database!;
    _database = await _initDB('positions.db');
    return _database!;
  }

  Future<Database> _initDB(String filePath) async {
    final dbPath = await getDatabasesPath();
    final path = join(dbPath, filePath);

    return await openDatabase(
      path,
      version: 1,
      onCreate: _createDB,
    );
  }

  Future _createDB(Database db, int version) async {
    await db.execute('''
      CREATE TABLE grid_bullets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        symbol TEXT,
        quantity REAL,
        buy_price REAL,
        side TEXT DEFAULT 'buy',
        exchange_mode TEXT DEFAULT 'kis_real',
        order_id TEXT DEFAULT ''
      )
    ''');

    await db.execute('''
      CREATE TABLE trade_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        symbol TEXT,
        quantity REAL,
        price REAL,
        side TEXT,
        exchange_mode TEXT,
        filled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        status TEXT DEFAULT 'filled'
      )
    ''');
    
    await db.execute('''
      CREATE TABLE config (
        key TEXT PRIMARY KEY,
        value TEXT
      )
    ''');
  }

  // 포지션 조회
  Future<List<Map<String, dynamic>>> getPositions(String mode) async {
    final db = await instance.database;
    final result = await db.query('grid_bullets', where: 'exchange_mode = ?', whereArgs: [mode]);
    return result;
  }

  // 포지션 저장
  Future<void> savePosition(String symbol, double qty, double price, String side, String mode, String orderId) async {
    final db = await instance.database;
    await db.insert('grid_bullets', {
      'symbol': symbol,
      'quantity': qty,
      'buy_price': price,
      'side': side,
      'exchange_mode': mode,
      'order_id': orderId,
    });
  }

  // 포지션 삭제
  Future<void> deletePosition(int id) async {
    final db = await instance.database;
    await db.delete('grid_bullets', where: 'id = ?', whereArgs: [id]);
  }
  
  // 전체 미체결 초기화
  Future<void> clearAllPositions(String mode) async {
    final db = await instance.database;
    await db.delete('grid_bullets', where: 'exchange_mode = ?', whereArgs: [mode]);
  }

  // 거래 내역 기록
  Future<void> recordTrade(String symbol, double qty, double price, String side, String mode, String status) async {
    final db = await instance.database;
    await db.insert('trade_history', {
      'symbol': symbol,
      'quantity': qty,
      'price': price,
      'side': side,
      'exchange_mode': mode,
      'status': status,
      'filled_at': DateTime.now().toIso8601String(),
    });
  }
  
  // 거래 내역 조회
  Future<List<Map<String, dynamic>>> getTradeHistory(String mode, {int limit = 50}) async {
    final db = await instance.database;
    return await db.query('trade_history', where: 'exchange_mode = ?', whereArgs: [mode], orderBy: 'id DESC', limit: limit);
  }

  // 거래 내역 초기화
  Future<void> clearTradeHistory(String mode) async {
    final db = await instance.database;
    await db.delete('trade_history', where: 'exchange_mode = ?', whereArgs: [mode]);
  }
}
