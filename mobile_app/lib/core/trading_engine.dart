import 'dart:async';
import 'package:flutter/material.dart';
import 'package:notification_listener_service/notification_listener_service.dart';
import 'package:notification_listener_service/notification_event.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../api/kis_api.dart';

class TradingEngine extends ChangeNotifier {
  KisApi? kisApi;
  bool isRunning = false;
  String logMessages = "";
  StreamSubscription<ServiceNotificationEvent>? _subscription;

  // 알림 파싱 정규식 예시
  // "[한국투자증권] 한화오션 매수체결 50주 28,000원"
  // 실 구현 시 실제 앱의 알림 포맷에 맞춰야 함.
  final RegExp buyRegex = RegExp(r'매수.*체결.*(?:한화오션)?.*(\d+)주.*(\d+,\d+)원');
  final RegExp sellRegex = RegExp(r'매도.*체결.*(?:한화오션)?.*(\d+)주.*(\d+,\d+)원');

  Future<void> init(String appKey, String appSecret, String cano) async {
    kisApi = KisApi(appKey: appKey, appSecret: appSecret, cano: cano, isMock: true);
    await kisApi!.auth();
    log("KIS API 인증 성공");
  }

  void log(String msg) {
    debugPrint(msg);
    logMessages = "$msg\n$logMessages";
    notifyListeners();
  }

  Future<void> startListening() async {
    if (kisApi == null) {
      log("API 정보가 초기화되지 않았습니다.");
      return;
    }

    bool status = await NotificationListenerService.isPermissionGranted();
    if (!status) {
      log("알림 접근 권한이 없습니다. 권한을 요청합니다.");
      await NotificationListenerService.requestPermission();
      return;
    }

    isRunning = true;
    log("알림 감시 및 매매 엔진 시작됨");
    notifyListeners();

    _subscription = NotificationListenerService.notificationsStream.listen((event) {
      if (!isRunning) return;
      _handleNotification(event);
    });
  }

  void stopListening() {
    isRunning = false;
    _subscription?.cancel();
    log("알림 감시 중지");
    notifyListeners();
  }

  Future<void> _handleNotification(ServiceNotificationEvent event) async {
    // 패키지명이 한국투자증권인 경우 필터링 (com.truefriend.android.secuxray 등)
    // 현재는 테스트를 위해 모든 알림 중 텍스트가 일치하는지 확인
    String title = event.title ?? "";
    String content = event.content ?? "";
    String fullText = "$title $content";

    // 매수 체결 감지
    if (fullText.contains("매수") && fullText.contains("체결")) {
      log("매수 체결 알림 감지: $fullText");
      // TODO: 정규식 파싱 후, 매수 평단가 + 이익마진(예: 2000원) 설정하여 매도 주문 발송
      try {
        await kisApi!.placeOrder(
          orderType: 'sell',
          symbol: '042660', // 한화오션
          price: 30000,     // 하드코딩 (실제로는 정규식으로 파싱한 가격 + 마진)
          qty: 1,           // 하드코딩
        );
        log("=> [익절 매도] 자동 주문 접수 완료");
      } catch (e) {
        log("주문 에러: $e");
      }
    }
    // 매도 체결 감지
    else if (fullText.contains("매도") && fullText.contains("체결")) {
      log("매도 체결 알림 감지: $fullText");
      // TODO: 매도 완료 시 하락 물타기 그리드 주문 발송 로직 추가 가능
    }
  }
}

