import 'package:flutter_test/flutter_test.dart';

void main() {
  group('1. KIS 호가 틱 보정 알고리즘 검증 (Ping-Pong)', () {
    test('매수 체결 후 매도 핑퐁 목표가 (900원 단위 고정)', () {
      // 체결가 32000원 -> +4000원 마진 -> 36000원
      double price = 32000.0;
      double targetPrice = price + 4000.0;
      targetPrice = ((targetPrice - 900) / 1000).round() * 1000 + 900;
      expect(targetPrice, 35900.0); // 36000원에 가장 가까운 900원 단위

      // 체결가 32400원 -> +4000원 -> 36400원
      price = 32400.0;
      targetPrice = price + 4000.0;
      targetPrice = ((targetPrice - 900) / 1000).round() * 1000 + 900;
      expect(targetPrice, 36900.0); // 36400 -> (35.5).round() -> 36 * 1000 + 900 = 36900
    });

    test('매도 체결 후 매수 핑퐁 목표가 (100원 단위 고정)', () {
      // 체결가 36000원 -> -4000원 마진 -> 32000원
      double price = 36000.0;
      double targetPrice = price - 4000.0;
      targetPrice = ((targetPrice - 100) / 1000).round() * 1000 + 100;
      expect(targetPrice, 32100.0); // 32000원에 가장 가까운 100원 단위

      // 체결가 36600원 -> -4000원 -> 32600원
      price = 36600.0;
      targetPrice = price - 4000.0;
      targetPrice = ((targetPrice - 100) / 1000).round() * 1000 + 100;
      expect(targetPrice, 33100.0); // 32600 -> (32.5).round() -> 33 * 1000 + 100 = 33100
    });
  });

  group('2. 계단형 그리드 수량 증액 알고리즘 검증', () {
    test('매도 방향 증액 검증 (단계=3, 기본=10, 증액=5)', () {
      int stairSteps = 3;
      double stairAddQty = 5.0;
      double orderQuantity = 10.0;

      List<double> quantities = [];
      for (int i = 1; i <= 6; i++) {
        double qty = orderQuantity + ((i - 1) ~/ stairSteps) * stairAddQty;
        quantities.add(qty);
      }

      // 1~3단계는 10주, 4~6단계는 15주
      expect(quantities, [10.0, 10.0, 10.0, 15.0, 15.0, 15.0]);
    });
  });

  group('3. 중복 주문 필터링 룰 검증', () {
    test('Set 캐싱을 통한 기존 포지션 제거 (removeWhere)', () {
      // 현재 UI 큐에 담긴 생성된 그리드
      List<Map<String, dynamic>> finalOrders = [
        {'side': 'sell', 'price': 35900.0, 'quantity': 10},
        {'side': 'sell', 'price': 37900.0, 'quantity': 10},
        {'side': 'buy', 'price': 32100.0, 'quantity': 10},
      ];

      // SQLite에서 긁어왔다고 가정한 기존 포지션 (35900원이 이미 존재)
      List<Map<String, dynamic>> dbPositions = [
        {'id': 1, 'avg_price': 35900.0},
        {'id': 2, 'avg_price': 80000.0},
      ];

      final Set<double> existingPrices = dbPositions
          .map<double>((e) => (e['avg_price'] as num).toDouble())
          .toSet();

      finalOrders.removeWhere(
          (o) => existingPrices.contains((o['price'] as num).toDouble()));

      // 35900원이 제거되고 2개만 남아야 함
      expect(finalOrders.length, 2);
      expect(finalOrders[0]['price'], 37900.0);
    });
  });
}

