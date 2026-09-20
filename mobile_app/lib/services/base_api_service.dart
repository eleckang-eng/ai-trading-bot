abstract class BaseApiService {
  Future<Map<String, dynamic>> getStatus();
  Future<double> getPrice(String symbol);
  Future<Map<String, dynamic>> sendOrder(String side, String symbol, double quantity, double price);
  Future<Map<String, dynamic>> cancelAllOrders();
}
