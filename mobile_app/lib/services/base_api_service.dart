abstract class BaseApiService {
  Future<Map<String, dynamic>> getStatus();
  Future<double> getPrice(String exchange, String symbol);
  Future<Map<String, dynamic>> sendOrder(String side, String symbol, double quantity, double price);
  Future<Map<String, dynamic>> cancelOrder(String orderId);
  Future<Map<String, dynamic>> cancelAllOrders();
  Future<Map<String, dynamic>> refreshBalance();
  Future<Map<String, dynamic>> syncOrders();
  Future<Map<String, dynamic>> updateConfig(Map<String, dynamic> payload);
  Future<List<dynamic>> getHistory({int limit = 50});
  Future<Map<String, dynamic>> clearHistory();
}
