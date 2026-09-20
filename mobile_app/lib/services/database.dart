import 'package:sqflite/sqflite.dart';
import 'package:path/path.dart';

class DatabaseHelper {
  static final DatabaseHelper instance = DatabaseHelper._init();
  static Database? _database;

  DatabaseHelper._init();

  Future<Database> get database async {
    if (_database != null) return _database!;
    _database = await _initDB('positions.db');
    return _database!;
  }

  Future<Database> _initDB(String filePath) async {
    final dbPath = await getDatabasesPath();
    final path = join(dbPath, filePath);

    return await openDatabase(path, version: 1, onCreate: _createDB);
  }

  Future _createDB(Database db, int version) async {
    await db.execute('''
      CREATE TABLE positions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        symbol TEXT NOT NULL,
        side TEXT NOT NULL,
        quantity REAL NOT NULL,
        price REAL NOT NULL,
        status TEXT DEFAULT 'open',
        order_id TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      )
    ''');
  }

  Future<int> insertPosition(Map<String, dynamic> position) async {
    final db = await instance.database;
    return await db.insert('positions', position);
  }

  Future<List<Map<String, dynamic>>> getActivePositions(String symbol) async {
    final db = await instance.database;
    return await db.query(
      'positions',
      where: 'symbol = ? AND status = ?',
      whereArgs: [symbol, 'open'],
      orderBy: 'price DESC',
    );
  }

  Future<int> updatePositionStatus(int id, String status) async {
    final db = await instance.database;
    return await db.update(
      'positions',
      {'status': status},
      where: 'id = ?',
      whereArgs: [id],
    );
  }
  
  Future<int> deletePosition(int id) async {
    final db = await instance.database;
    return await db.delete(
      'positions',
      where: 'id = ?',
      whereArgs: [id],
    );
  }
}
