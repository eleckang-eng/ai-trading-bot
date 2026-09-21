import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart';

class SecureSettings {
  static const _storage = FlutterSecureStorage();

  static Future<void> saveKisKeys(String appKey, String appSecret, String cano) async {
    await _storage.write(key: 'appKey', value: appKey);
    await _storage.write(key: 'appSecret', value: appSecret);
    await _storage.write(key: 'cano', value: cano);
  }

  static Future<Map<String, String>> getKisKeys() async {
    // 1. .env 파일의 환경변수를 최우선으로 확인
    String appKey = dotenv.env['KIS_APP_KEY'] ?? '';
    String appSecret = dotenv.env['KIS_APP_SECRET'] ?? '';
    String cano = dotenv.env['KIS_CANO'] ?? '';

    // 2. .env에 값이 없을 경우에만 SecureStorage에서 읽음
    if (appKey.isEmpty) appKey = await _storage.read(key: 'appKey') ?? '';
    if (appSecret.isEmpty) appSecret = await _storage.read(key: 'appSecret') ?? '';
    if (cano.isEmpty) cano = await _storage.read(key: 'cano') ?? '';

    return {
      'appKey': appKey,
      'appSecret': appSecret,
      'cano': cano,
    };
  }
}
