import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class SecureSettings {
  static final _storage = const FlutterSecureStorage();

  static Future<void> saveKisKeys(String appKey, String appSecret, String cano) async {
    await _storage.write(key: 'kis_app_key', value: appKey);
    await _storage.write(key: 'kis_app_secret', value: appSecret);
    await _storage.write(key: 'kis_cano', value: cano);
  }

  static Future<Map<String, String>> getKisKeys() async {
    return {
      'appKey': await _storage.read(key: 'kis_app_key') ?? '',
      'appSecret': await _storage.read(key: 'kis_app_secret') ?? '',
      'cano': await _storage.read(key: 'kis_cano') ?? '',
    };
  }
}
