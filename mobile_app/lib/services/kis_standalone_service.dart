import 'base_api_service.dart';
import '../../exchanges/kis_api.dart';
import 'database.dart';

class KisStandaloneService implements BaseApiService {
  final KisApi kisApi;

  KisStandaloneService(this.kisApi);

  @override
  Future<Map<String, dynamic>> getStatus() async {
    final positions = await DatabaseHelper.instance.getActivePositions("005930");
    return {
      'status': 'success',
      'config': {'exchange': 'kis', 'symbol': '005930'},
      'bullets': positions
    };
  }

  @override
  Future<double> getPrice(String exchange, String symbol) async {
    final price = await kisApi.fetch_current_price(symbol);
    return price.toDouble();
  }

  @override
  Future<Map<String, dynamic>> sendOrder(String side, String symbol, double quantity, double price) async {
    return {'status': 'error', 'message': '단독 모드 수동 주문 미지원'};
  }

  @override
  Future<Map<String, dynamic>> cancelOrder(String orderId) async {
    return {'status': 'error', 'message': '단독 모드 주문 취소 미지원'};
  }

  @override
  Future<Map<String, dynamic>> cancelAllOrders() async {
    // 단독 모드 KIS 일괄 취소: KIS Open API에는 일괄 취소 API가 없습니다.
    // 미체결 내역을 조회한 뒤 루프를 돌려 취소 주문을 넣어야 합니다.
    return {'status': 'error', 'message': '모바일 단독 모드에서는 미체결 일괄 취소를 지원하지 않습니다.'};
  }

  @override
  Future<Map<String, dynamic>> refreshBalance() async {
    return {'status': 'error', 'message': '모바일 단독 모드에서는 잔고 수동 동기화를 지원하지 않습니다.'};
  }

  @override
  Future<List<dynamic>> getHistory({int limit = 50}) async {
    return [];
  }

  @override
  Future<Map<String, dynamic>> clearHistory() async {
    return {'status': 'error', 'message': '모바일 단독 모드에서는 내역 초기화를 지원하지 않습니다.'};
  }
}
