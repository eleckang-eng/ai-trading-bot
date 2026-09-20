import 'dart:convert';
import 'package:http/http.dart' as http;
import 'base_api_service.dart';

class RemoteApiService implements BaseApiService {
  final String baseUrl;
  final String exchange;

  RemoteApiService({required this.baseUrl, required this.exchange});

  @override
  Future<Map<String, dynamic>> getStatus() async {
    try {
      final res = await http.get(Uri.parse('${baseUrl}/status?exchange=${exchange}')).timeout(const Duration(seconds: 5));
      if (res.statusCode == 200) return jsonDecode(res.body);
      return {'status': 'error', 'message': 'HTTP ${res.statusCode}'};
    } catch (e) {
      return {'status': 'error', 'message': e.toString()};
    }
  }

  @override
  Future<double> getPrice(String symbol) async {
    try {
      final res = await http.get(Uri.parse('${baseUrl}/price?exchange=${exchange}&symbol=${symbol}')).timeout(const Duration(seconds: 3));
      if (res.statusCode == 200) {
        final data = jsonDecode(res.body);
        return (data['price'] ?? 0).toDouble();
      }
      return 0.0;
    } catch (e) {
      return 0.0;
    }
  }

  @override
  Future<Map<String, dynamic>> sendOrder(String side, String symbol, double quantity, double price) async {
    try {
      final res = await http.post(
        Uri.parse('${baseUrl}/order/manual'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({"exchange": exchange, "side": side, "symbol": symbol, "quantity": quantity, "price": price}),
      ).timeout(const Duration(seconds: 10));
      if (res.statusCode == 200) return jsonDecode(res.body);
      return {'status': 'error', 'message': 'HTTP ${res.statusCode}'};
    } catch (e) {
      return {'status': 'error', 'message': e.toString()};
    }
  }

  @override
  Future<Map<String, dynamic>> cancelAllOrders() async {
    try {
      final res = await http.post(
        Uri.parse('${baseUrl}/order/cancel_all'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({"exchange": exchange}),
      ).timeout(const Duration(seconds: 15));
      if (res.statusCode == 200) return jsonDecode(res.body);
      return {'status': 'error', 'message': 'HTTP ${res.statusCode}'};
    } catch (e) {
      return {'status': 'error', 'message': e.toString()};
    }
  }

  @override
  Future<Map<String, dynamic>> refreshBalance() async {
    try {
      final res = await http.post(Uri.parse('${baseUrl}/refresh_balance')).timeout(const Duration(seconds: 15));
      if (res.statusCode == 200) return jsonDecode(res.body);
      return {'status': 'error', 'message': 'HTTP ${res.statusCode}'};
    } catch (e) {
      return {'status': 'error', 'message': e.toString()};
    }
  }

  @override
  Future<List<dynamic>> getHistory({int limit = 50}) async {
    try {
      final res = await http.get(Uri.parse('${baseUrl}/history?limit=$limit')).timeout(const Duration(seconds: 5));
      if (res.statusCode == 200) return jsonDecode(res.body);
      return [];
    } catch (e) {
      return [];
    }
  }

  @override
  Future<Map<String, dynamic>> clearHistory() async {
    try {
      final res = await http.post(Uri.parse('${baseUrl}/history/clear')).timeout(const Duration(seconds: 5));
      if (res.statusCode == 200) return jsonDecode(res.body);
      return {'status': 'error', 'message': 'HTTP ${res.statusCode}'};
    } catch (e) {
      return {'status': 'error', 'message': e.toString()};
    }
  }
}
