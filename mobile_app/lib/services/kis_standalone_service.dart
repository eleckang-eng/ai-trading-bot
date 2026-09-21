import 'dart:async';
import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';
import 'base_api_service.dart';
import '../api/kis_api.dart';
import 'database_service.dart';

import '../core/trading_engine.dart';

class KisStandaloneService implements BaseApiService {
  final KisApi kisApi;
  final TradingEngine? engine;
  DateTime _lastSyncTime = DateTime.fromMillisecondsSinceEpoch(0);
  int _cachedProfit = 0;
  bool _isSyncing = false;

  KisStandaloneService(this.kisApi, {this.engine});

  @override
  Future<Map<String, dynamic>> getStatus() async {
    try {
      final balRes = await kisApi.getBalance();
      int balance = 0;
      if (balRes['output2'] != null && balRes['output2'].isNotEmpty) {
        balance = int.tryParse(balRes['output2'][0]['dnca_tot_amt'].toString()) ?? 0;
        // 하이브리드 보정: KIS API에서 실현손익을 추출하여 갱신
        // 실제 윈도우 환경처럼 1분 주기로 동기화
        if (DateTime.now().difference(_lastSyncTime).inMinutes >= 1) {
           _lastSyncTime = DateTime.now();
           try {
             final now = DateTime.now();
             final startDt = "${now.year}${now.month.toString().padLeft(2, '0')}01";
             final endDt = "${now.year}${now.month.toString().padLeft(2, '0')}${now.day.toString().padLeft(2, '0')}";
             final profitRes = await kisApi.getRealizedProfit(startDate: startDt, endDate: endDt);
             if (profitRes['rt_cd'] == '0' && profitRes['output2'] != null && profitRes['output2'].isNotEmpty) {
               _cachedProfit = int.tryParse(profitRes['output2'][0]['rlzt_erng_amt'].toString()) ?? _cachedProfit;
             }
           } catch (e) {
             // ignore
           }
           // 스마트 동기화 트리거
           unawaited(syncOrders());
        }
      }
      
      // SQLite에서 포지션 불러오기
      final dbPositions = await DatabaseService.instance.getPositions('kis_real');
      List<Map<String, dynamic>> positions = dbPositions.map((p) => <String, dynamic>{
        'id': p['id'],
        'symbol': p['symbol'],
        'quantity': p['quantity'],
        'avg_price': p['buy_price'],
        'side': p['side'],
        'order_id': p['order_id'],
      }).toList();

      final prefs = await SharedPreferences.getInstance();
      final configStr = prefs.getString('kis_config');
      Map<String, dynamic> config = {};
      if (configStr != null) {
        config = jsonDecode(configStr);
      }

      return {
        'status': 'success',
        'running': engine?.isRunning ?? true,
        'balance': balance,
        'total_profit': _cachedProfit,
        'trade_count': 0, // 별도 집계 필요 시 DatabaseService.instance.getTradeHistory로 확장
        'positions': positions,
        'exchange_connected': true,
        'config': config,
      };
    } catch (e) {
      return {'status': 'error', 'message': e.toString()};
    }
  }

  @override
  Future<double> getPrice(String exchange, String symbol) async {
    try {
      final price = await kisApi.getCurrentPrice(symbol);
      return price.toDouble();
    } catch (e) {
      return 0.0;
    }
  }

  @override
  Future<Map<String, dynamic>> sendOrder(String side, String symbol, double quantity, double price) async {
    try {
      final res = await kisApi.placeOrder(orderType: side, symbol: symbol, price: price.toInt(), qty: quantity.toInt());
      if (res['rt_cd'] == '0') {
        String orderId = res['output']?['ODNO'] ?? '';
        await DatabaseService.instance.savePosition(symbol, quantity, price, side, 'kis_real', orderId);
        return {'status': 'success', 'data': res};
      } else {
        return {'status': 'error', 'message': res['msg1'] ?? '알 수 없는 주문 에러'};
      }
    } catch (e) {
      return {'status': 'error', 'message': e.toString()};
    }
  }

  @override
  Future<Map<String, dynamic>> sendBatchOrder(List<Map<String, dynamic>> orders) async {
    List<Map<String, dynamic>> results = [];
    int successCount = 0;
    
    final dbPositions = await DatabaseService.instance.getPositions('kis_real');
    Set<double> existingPrices = dbPositions.map((p) => double.parse(p['buy_price'].toString())).toSet();

    for (var o in orders) {
      double price = double.parse(o['price'].toString());
      if (existingPrices.contains(price)) {
         results.add({'status': 'error', 'message': '중복 가격 제외됨'});
         continue;
      }
      
      try {
        final symbol = o['symbol'] ?? '042660';
        final res = await kisApi.placeOrder(orderType: o['side'], symbol: symbol, price: price.toInt(), qty: double.parse(o['quantity'].toString()).toInt());
        
        if (res['rt_cd'] == '0') {
          String orderId = res['output']?['ODNO'] ?? '';
          await DatabaseService.instance.savePosition(symbol, double.parse(o['quantity'].toString()), price, o['side'], 'kis_real', orderId);
          results.add({'status': 'success'});
          successCount++;
        } else {
          String errMsg = res['msg1'] ?? '알 수 없는 주문 에러';
          results.add({'status': 'error', 'message': errMsg});
        }
        
        // API 속도 제한 방어 (429 에러 방지용 300ms 딜레이)
        await Future.delayed(const Duration(milliseconds: 300));
      } catch (e) {
        results.add({'status': 'error', 'message': e.toString()});
      }
    }
    
    return {
      'status': successCount > 0 ? 'success' : 'error',
      'message': '성공 $successCount건, 실패 ${orders.length - successCount}건',
      'total': orders.length,
      'success_count': successCount,
      'fail_count': orders.length - successCount,
      'results': results
    };
  }

  @override
  Future<Map<String, dynamic>> cancelOrder(String id) async {
    try {
      final dbPos = await DatabaseService.instance.getPositions('kis_real');
      final pos = dbPos.firstWhere((p) => p['id'].toString() == id, orElse: () => {});
      if (pos.isEmpty) return {'status': 'error', 'message': '포지션을 찾을 수 없음'};

      String orderId = pos['order_id'] ?? '';
      String symbol = pos['symbol'] ?? '042660';
      
      if (orderId.isNotEmpty) {
        final res = await kisApi.cancelOrder(orderId, symbol: symbol);
        if (res['rt_cd'] != '0') {
          return {'status': 'error', 'message': 'API 취소 거부: ${res['msg1']}'};
        }
      }
      
      await DatabaseService.instance.recordTrade(
        symbol,
        (pos['quantity'] ?? 0).toDouble(),
        (pos['price'] ?? 0).toDouble(),
        pos['side'] ?? 'buy',
        'kis_real',
        'canceled',
      );
      await DatabaseService.instance.deletePosition(int.parse(id));
      return {'status': 'success', 'message': '주문 취소 및 DB 정리 완료'};
    } catch (e) {
      return {'status': 'error', 'message': e.toString()};
    }
  }

  @override
  Future<Map<String, dynamic>> cancelAllOrders() async {
    try {
      final dbPositions = await DatabaseService.instance.getPositions('kis_real');
      int successCount = 0;
      int failCount = 0;
      for (var p in dbPositions) {
         String orderId = p['order_id'] ?? '';
         String symbol = p['symbol'] ?? '042660';
         int pId = p['id'];
         
         bool apiOk = false;
         if (orderId.isNotEmpty) {
             final res = await kisApi.cancelOrder(orderId, symbol: symbol);
             if (res['rt_cd'] == '0') {
               apiOk = true;
               successCount++;
             } else {
               failCount++;
             }
             await Future.delayed(const Duration(milliseconds: 300));
         } else {
             apiOk = true;
             successCount++;
         }
         
         if (apiOk) {
            await DatabaseService.instance.recordTrade(
              symbol,
              (p['quantity'] ?? 0).toDouble(),
              (p['price'] ?? 0).toDouble(),
              p['side'] ?? 'buy',
              'kis_real',
              'canceled',
            );
            await DatabaseService.instance.deletePosition(pId);
         }
      }
      return {'status': 'success', 'message': '증권사 주문 $successCount건 취소 완료 (실패 $failCount건 보류)'};
    } catch (e) {
       return {'status': 'error', 'message': e.toString()};
    }
  }

  @override
  Future<Map<String, dynamic>> cancelList(List<int> ids) async {
    int successCount = 0;
    int failCount = 0;
    for (var id in ids) {
      final res = await cancelOrder(id.toString());
      if (res['status'] == 'success') successCount++;
      else failCount++;
    }
    return {'status': 'success', 'message': '$successCount건 취소 성공, 실패 $failCount건'};
  }

  @override
  Future<Map<String, dynamic>> refreshBalance() async {
    return getStatus();
  }

  /// 윈도우 앱의 _place_pingpong_order()와 동일한 핑퐁 공식을 적용하여 반대 방향 주문을 생성합니다.
  /// - 매수 체결 → 위로 (gridInterval * 2)원 매도 / 매도 체결 → 아래로 (gridInterval * 2)원 매수
  /// - KIS 틱 보정: 매도는 끝자리 900원, 매수는 끝자리 100원
  Future<void> _placePingpongOrder({
    required String symbol,
    required String filledSide,
    required double filledPrice,
    required double qty,
    double gridInterval = 2000,
  }) async {
    // 핑퐁 타겟 가격: 그리드 간격의 2배
    final double pingpongMargin = gridInterval * 2;
    double targetPrice = 0;
    String sideToPlace = 'buy';

    if (filledSide == 'buy') {
      // 매수 체결 → 위로 (pingpongMargin)원 매도 핑퐁
      targetPrice = filledPrice + pingpongMargin;
      // KIS 틱 보정: 매도 끝자리 900원으로 보정
      targetPrice = ((targetPrice - 900) / 1000).round() * 1000 + 900;
      sideToPlace = 'sell';
    } else if (filledSide == 'sell') {
      // 매도 체결 → 아래로 (pingpongMargin)원 매수 핑퐁
      targetPrice = filledPrice - pingpongMargin;
      if (targetPrice <= 0) {
        // 계산된 매수 가격이 0 이하이면 핑퐁 주문을 발송하지 않음 (비정상 가격 방어)
        return;
      }
      // KIS 틱 보정: 매수 끝자리 100원으로 보정
      targetPrice = ((targetPrice - 100) / 1000).round() * 1000 + 100;
      sideToPlace = 'buy';
    }

    // API Rate Limit 방어: 윈도우 앱의 time.sleep(1.0)에 대응
    await Future.delayed(const Duration(seconds: 1));

    try {
      final res = await kisApi.placeOrder(
        orderType: sideToPlace,
        symbol: symbol,
        price: targetPrice.toInt(),
        qty: qty.toInt(),
      );
      final orderId = res['output']?['ODNO'] ?? '';
      await DatabaseService.instance.savePosition(symbol, qty, targetPrice, sideToPlace, 'kis_real', orderId);
    } catch (e) {
      // 핑퐁 주문 실패는 치명적 오류이므로 rethrow하지 않고 로깅만 수행
      // 포지션이 꼬이지 않도록 별도 로그로 추적 가능하게 처리
      // ignore: avoid_print
      print('[핑퐁 오류] $filledSide 체결($filledPrice) 후 $sideToPlace 핑퐁 주문 실패: $e');
    }
  }

  /// 윈도우 앱의 sync_orders() 메서드와 동일한 스마트 동기화 로직입니다.
  /// - 미체결 주문 목록(getOpenOrders)과 체결 내역(getExecutionHistory)을 이중 조회합니다.
  /// - 매수 상위 2건, 매도 최하위 2건만 탐색하여 API 호출 최소화합니다.
  /// - 체결 확인 시 핑퐁 반대 주문을 자동 발송합니다.
  @override
  Future<Map<String, dynamic>> syncOrders() async {
    final now = DateTime.now();
    if (now.hour < 8 || now.hour >= 20) {
      return {'status': 'ignored', 'message': 'Outside trading hours (08:00~20:00)'};
    }

    if (_isSyncing) return {'status': 'ignored', 'message': 'Already syncing'};
    _isSyncing = true;
    try {
      final dbPositions = await DatabaseService.instance.getPositions('kis_real');
      
      if (dbPositions.isEmpty) {
        _isSyncing = false;
        return {'status': 'ignored', 'message': '활성화된 포지션이 없어 동기화를 건너뜁니다.'};
      }

      // 매수/매도 분리 후 현재가에 가장 가까운 순서로 정렬
      // 매수(buy)는 비쌀수록 현재가에 가까움 (내림차순)
      List<Map<String, dynamic>> buys = dbPositions.where((p) => p['side'] == 'buy').toList();
      // 매도(sell)는 쌀수록 현재가에 가까움 (오름차순)
      List<Map<String, dynamic>> sells = dbPositions.where((p) => p['side'] == 'sell').toList();
      buys.sort((a, b) => (b['buy_price'] as num).compareTo(a['buy_price'] as num));
      sells.sort((a, b) => (a['buy_price'] as num).compareTo(b['buy_price'] as num));

      // 탐색 대상: 매수 상위 2건 + 매도 최하위 2건
      final List<Map<String, dynamic>> targets = [
        ...buys.take(2),
        ...sells.take(2),
      ];

      if (targets.isEmpty) {
        return {'status': 'success', 'message': '동기화할 포지션 없음'};
      }

      // 1. 미체결 주문 목록 조회 (현재 살아있는 주문의 ODNO 집합)
      final openRes = await kisApi.getOpenOrders();
      // 2. 전일~당일 체결 내역 조회 (어제 체결된 것도 포함)
      final filledRes = await kisApi.getExecutionHistory();

      if (openRes['rt_cd'] != '0') {
        return {'status': 'error', 'message': '미체결 조회 실패: ${openRes['msg1']}'};
      }

      final List openList = openRes['output'] ?? [];
      // output1 우선, 없으면 output으로 폴백 (윈도우 앱과 동일한 파싱 로직)
      final List filledList = (filledRes['output1'] ?? filledRes['output'] ?? []) as List;

      // 주문번호(odno) 기반으로 미체결/체결 집합 구성 (가격 의존 탈피)
      final Set<String> openOdnos = openList.map((o) => o['odno']?.toString().trim() ?? '').toSet();
      final Set<String> filledOdnos = {
        ...filledList.map((o) => o['odno']?.toString().trim() ?? ''),
        ...filledList.map((o) => o['orgn_odno']?.toString().trim() ?? ''),
      }..remove('');

      int removedCount = 0;

      // 스마트 동기화: 최대 2건의 미체결 주문을 허용하고, 체결되면 핑퐁 주문 발송
      // 매수/매도 각각 max_check=2 기준으로 처리 (윈도우 _smart_sync_kis()와 동일)
      Future<void> smartSync(List<Map<String, dynamic>> sortedPos, {int maxCheck = 2}) async {
        int unfilledChecked = 0;
        for (final pos in sortedPos) {
          if (unfilledChecked >= maxCheck) break;

          final String orderId = (pos['order_id'] ?? '').toString().trim();
          if (orderId.isEmpty) continue;

          if (openOdnos.contains(orderId)) {
            // 아직 체결되지 않은 주문 → 카운트 증가 후 다음으로
            unfilledChecked++;
          } else {
            if (filledOdnos.contains(orderId)) {
              // 체결 확인: 거래내역에 기록하고 DB 포지션에서 제거 후 핑퐁 발송
              await DatabaseService.instance.recordTrade(
                pos['symbol'] ?? '042660',
                double.parse(pos['quantity'].toString()),
                double.parse(pos['buy_price'].toString()),
                pos['side'] ?? 'buy',
                'kis_real',
                'filled',
              );
              await DatabaseService.instance.deletePosition(pos['id'] as int);
              removedCount++;

              // 설정에서 grid_interval 읽어오기
              final prefs = await SharedPreferences.getInstance();
              final configStr = prefs.getString('kis_config');
              double currentGridInterval = 2000;
              if (configStr != null) {
                final cfg = jsonDecode(configStr);
                if (cfg['kis'] != null && cfg['kis']['grid_interval'] != null) {
                  currentGridInterval = (cfg['kis']['grid_interval'] as num).toDouble();
                }
              }

              // 핑퐁(Ping-Pong) 반대 주문 자동 발송 (윈도우 _place_pingpong_order와 동일)
              await _placePingpongOrder(
                symbol: pos['symbol'] ?? '042660',
                filledSide: pos['side'] ?? 'buy',
                filledPrice: double.parse(pos['buy_price'].toString()),
                qty: double.parse(pos['quantity'].toString()),
                gridInterval: currentGridInterval,
              );
            } else {
              // 미체결/체결 어디에도 없음 → 취소된 주문으로 처리
              await DatabaseService.instance.recordTrade(
                pos['symbol'] ?? '042660',
                double.parse(pos['quantity'].toString()),
                double.parse(pos['buy_price'].toString()),
                pos['side'] ?? 'buy',
                'kis_real',
                'canceled',
              );
              await DatabaseService.instance.deletePosition(pos['id'] as int);
              removedCount++;
            }
          }
        }
      }

      await smartSync(buys, maxCheck: 2);
      await smartSync(sells, maxCheck: 2);

      return {'status': 'success', 'message': '한투 스마트 동기화 완료 (체결/취소 $removedCount건 업데이트)'};
    } catch (e) {
      return {'status': 'error', 'message': e.toString()};
    } finally {
      _isSyncing = false;
    }
  }

  @override
  Future<Map<String, dynamic>> updateConfig(Map<String, dynamic> payload) async {
    try {
      final prefs = await SharedPreferences.getInstance();
      
      // 기존 설정과 병합
      final existingStr = prefs.getString('kis_config');
      Map<String, dynamic> merged = {};
      if (existingStr != null) {
        merged = jsonDecode(existingStr);
      }
      payload.forEach((k, v) => merged[k] = v);
      
      await prefs.setString('kis_config', jsonEncode(merged));
      return {'status': 'success'};
    } catch (e) {
      return {'status': 'error', 'message': e.toString()};
    }
  }

  @override
  Future<Map<String, dynamic>> startBot() async {
    engine?.startListening();
    return {'status': 'success'};
  }

  @override
  Future<Map<String, dynamic>> stopBot() async {
    engine?.stopListening();
    return {'status': 'success'};
  }

  @override
  Future<Map<String, dynamic>> restartBot() async {
    engine?.stopListening();
    await Future.delayed(const Duration(seconds: 1));
    engine?.startListening();
    return {'status': 'success'};
  }

  @override
  Future<List<dynamic>> getHistory({int limit = 50}) async {
    final history = await DatabaseService.instance.getTradeHistory('kis_real', limit: limit);
    return history.map((h) => <String, dynamic>{
      'filled_at': h['filled_at'],
      'side': h['side'],
      'price': h['price'],
      'quantity': h['quantity'],
      'status': h['status'],
    }).toList();
  }

  @override
  Future<Map<String, dynamic>> clearHistory() async {
    // 윈도우 앱의 clear_history()와 동일하게 SQLite 거래내역 영구 삭제
    _cachedProfit = 0;
    await DatabaseService.instance.clearTradeHistory('kis_real');
    return {'status': 'success'};
  }
}
