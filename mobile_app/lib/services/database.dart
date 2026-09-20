import 'package:sqflite/sqflite.dart';
import 'package:path/path.dart';

class DatabaseService {
  Database? _db;

  Future<Database> get database async {
    if (_db != null) return _db!;
    _db = await _initDB();
    return _db!;
  }

  Future<Database> _initDB() async {
    String dbPath = await getDatabasesPath();
    String path = join(dbPath, 'trading_bot.db');

    return await openDatabase(
      path,
      version: 1,
      onCreate: (db, version) async {
        await db.execute('''
          CREATE TABLE open_orders(
            order_id TEXT PRIMARY KEY,
            symbol TEXT,
            side TEXT,
            price INTEGER,
            qty INTEGER,
            status TEXT DEFAULT 'OPEN',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
          )
        ''');
      },
    );
  }

  // 아직 활성화된(미체결) 주문 목록 가져오기
  Future<List<Map<String, dynamic>>> getOpenOrders() async {
    final db = await database;
    return await db.query('open_orders', where: 'status = ?', whereArgs: ['OPEN']);
  }

  // 체결 완료 처리
  Future<void> markOrderExecuted(String id) async {
    final db = await database;
    await db.update('open_orders', {'status': 'EXECUTED'}, where: 'order_id = ?', whereArgs: [id]);
  }

  // 취소/장마감 소멸 처리
  Future<void> markOrderCancelled(String id) async {
    final db = await database;
    await db.update('open_orders', {'status': 'CANCELLED'}, where: 'order_id = ?', whereArgs: [id]);
  }

  // 신규 주문 DB 저장
  Future<void> addOpenOrder(String id, String symbol, String side, int price, int qty) async {
    final db = await database;
    await db.insert('open_orders', {
      'order_id': id,
      'symbol': symbol,
      'side': side,
      'price': price,
      'qty': qty,
      'status': 'OPEN'
    }, conflictAlgorithm: ConflictAlgorithm.replace);
  }
}

