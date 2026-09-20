import 'dart:async';
import 'package:flutter/foundation.dart';
import '../api/kis_api.dart'; // 가정된 경로
import 'database.dart'; // SQLite 래퍼

class TraderLoop {
  bool isRunning = false;
  Timer? _timer;
  final KisApi kisApi;
  final DatabaseService db;
  
  // 설정값 (기본값)
  int autoSyncIntervalMinutes = 1;
  int gridInterval = 2000;
  int quantity = 10;
  
  TraderLoop({required this.kisApi, required this.db});

  void start() {
    if (isRunning) return;
    isRunning = true;
    _runCycle(); // 즉시 1회 실행
    _timer = Timer.periodic(Duration(minutes: autoSyncIntervalMinutes), (timer) {
      _runCycle();
    });
    debugPrint("Mobile TraderLoop started.");
  }

  void stop() {
    isRunning = false;
    _timer?.cancel();
    debugPrint("Mobile TraderLoop stopped.");
  }

  int _adjustKisTick(int price, bool isBuy) {
    int base = (price ~/ 1000) * 1000;
    if (isBuy) {
      int cand1 = base - 900;
      int cand2 = base + 100;
      int cand3 = base + 1100;
      List<int> cands = [cand1, cand2, cand3];
      cands.sort((a, b) => (price - a).abs().compareTo((price - b).abs()));
      return cands.first;
    } else {
      int cand1 = base - 100;
      int cand2 = base + 900;
      int cand3 = base + 1900;
      List<int> cands = [cand1, cand2, cand3];
      cands.sort((a, b) => (price - a).abs().compareTo((price - b).abs()));
      return cands.first;
    }
  }

  Future<void> _runCycle() async {
    if (!isRunning) return;
    
    // 운영 시간 체크 (08:00 ~ 20:00 KST)
    DateTime nowKst = DateTime.now().toUtc().add(Duration(hours: 9));
    if (nowKst.hour < 8 || nowKst.hour >= 20) {
      debugPrint("Outside KIS operating hours. Skipping sync.");
      return;
    }
    
    try {
      debugPrint("--- Starting Mobile Sync Cycle ---");
      // 1. 거래소 데이터 조회 (미체결, 체결내역)
      final openOrdersRes = await kisApi.getOpenOrders();
      final executionRes = await kisApi.getExecutionHistory();
      
      // 파싱
      Set<String> exchangeOpenIds = {};
      if (openOrdersRes['output'] != null) {
        for (var o in openOrdersRes['output']) {
          exchangeOpenIds.add(o['odno'] ?? '');
        }
      }
      
      Set<String> executionIds = {};
      if (executionRes['output1'] != null) {
        for (var e in executionRes['output1']) {
          executionIds.add(e['odno'] ?? '');
        }
      }

      // 2. 로컬 DB 조회
      List<Map<String, dynamic>> localOpenOrders = await db.getOpenOrders();

      // 3. 교차 검증 및 핑퐁
      for (var order in localOpenOrders) {
        String orderId = order['order_id'];
        if (!exchangeOpenIds.contains(orderId)) {
          if (executionIds.contains(orderId)) {
            debugPrint("Execution confirmed for \$orderId");
            await db.markOrderExecuted(orderId);
            
            int executedPrice = (order['price'] as num).toInt();
            String side = order['side']; // 'buy' or 'sell'
            String symbol = order['symbol'];
            
            if (side == 'buy') {
              int targetPrice = _adjustKisTick(executedPrice + (gridInterval * 2), false);
              await _placeOrderWithBackoff(symbol, 'sell', targetPrice, quantity);
            } else if (side == 'sell') {
              int targetPrice = _adjustKisTick(executedPrice - (gridInterval * 2), true);
              await _placeOrderWithBackoff(symbol, 'buy', targetPrice, quantity);
            }
          } else {
            // 장 마감 등으로 자동 소멸된 경우
            await db.markOrderCancelled(orderId);
          }
        }
      }
      debugPrint("--- Mobile Sync Cycle Completed ---");
    } catch (e) {
      debugPrint("Error in Mobile Sync Cycle: \$e");
    }
  }

  Future<void> _placeOrderWithBackoff(String symbol, String side, int targetPrice, int qty) async {
    int maxRetries = 3;
    for (int i = 0; i < maxRetries; i++) {
      try {
        final res = await kisApi.placeOrder(orderType: side, symbol: symbol, price: targetPrice, qty: qty);
        if (res['rt_cd'] == '0') {
          // 성공 시 DB 저장 및 1초 딜레이(다중 체결 방어)
          await db.addOpenOrder(res['output']['KRX_FWDG_ORD_ORGNO'] ?? '', symbol, side, targetPrice, qty);
          await Future.delayed(const Duration(seconds: 1));
          return;
        }
      } catch (e) {
        debugPrint("Order failed. Attempt \${i + 1}");
      }
      // Exponential Backoff (1초, 2초, 4초)
      await Future.delayed(Duration(seconds: 1 << i));
    }
  }
}
