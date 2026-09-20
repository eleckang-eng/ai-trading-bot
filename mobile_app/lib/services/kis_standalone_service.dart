import 'base_api_service.dart';
import '../api/kis_api.dart';

class KisStandaloneService implements BaseApiService {
  final KisApi kisApi;

  KisStandaloneService(this.kisApi);

  @override
  Future<Map<String, dynamic>> getStatus() async {
    try {
      final data = await kisApi.getBalance();
      
      // KIS API 응답을 공통 포맷으로 매핑
      // KIS 응답: output1(잔고내역 배열), output2(계좌종합)
      final output2 = data['output2'];
      int balance = 0;
      if (output2 != null && output2 is List && output2.isNotEmpty) {
        balance = int.tryParse(output2[0]['dnca_tot_amt'] ?? '0') ?? 0;
      }
      
      List<dynamic> positions = [];
      final output1 = data['output1'];
      if (output1 != null && output1 is List) {
        for (var item in output1) {
          positions.add({
            'symbol': item['pdno'] ?? '',
            'avg_price': double.tryParse(item['pchs_avg_pric'] ?? '0') ?? 0,
            'quantity': double.tryParse(item['hldg_qty'] ?? '0') ?? 0,
          });
        }
      }
      
      return {
        'status': 'success',
        'balance': balance,
        'positions': positions,
      };
    } catch (e) {
      return {'status': 'error', 'message': e.toString()};
    }
  }

  @override
  Future<double> getPrice(String symbol) async {
    // KIS 단독 모드에서는 WebSocket이나 별도의 현재가 API가 필요하지만
    // 여기서는 임시로 잔고 API나 고정값을 리턴(실제 구현에서는 KIS 시세 API 호출 필요)
    return 30000.0; 
  }

  @override
  Future<Map<String, dynamic>> sendOrder(String side, String symbol, double quantity, double price) async {
    try {
      final data = await kisApi.placeOrder(
        orderType: side,
        symbol: symbol,
        price: price.toInt(),
        qty: quantity.toInt()
      );
      // rt_cd == '0' 이면 성공
      if (data['rt_cd'] == '0') {
        return {'status': 'success', 'data': data};
      }
      return {'status': 'error', 'message': data['msg1'] ?? 'Unknown error'};
    } catch (e) {
      return {'status': 'error', 'message': e.toString()};
    }
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
