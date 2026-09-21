import 'dart:async';
import 'package:flutter/material.dart';
import '../api/kis_api.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'dart:convert';

/// 모바일 단독 매매 엔진 (알림 푸시 방식 제거 → 추후 폴링 방식으로 체결 감지)
class TradingEngine extends ChangeNotifier {
  KisApi? kisApi;
  bool isRunning = false;
  String logMessages = "";

  Future<void> init(String appKey, String appSecret, String cano) async {
    final prefs = await SharedPreferences.getInstance();
    final configStr = prefs.getString('kis_config');
    bool isMock = false; // 기본값을 실전(false)으로 변경
    if (configStr != null) {
      final config = jsonDecode(configStr);
      isMock = config['mock_mode'] ?? false;
    }
    
    kisApi = KisApi(appKey: appKey, appSecret: appSecret, cano: cano, isMock: isMock);
    await kisApi!.auth();
    log("KIS API 인증 성공 (isMock: $isMock)");
  }

  void log(String msg) {
    debugPrint(msg);
    logMessages = "$msg\n$logMessages";
    notifyListeners();
  }

  /// 엔진 시작 (추후 체결 내역 폴링 루프 연결 예정)
  Future<void> startListening() async {
    if (kisApi == null) {
      log("API 정보가 초기화되지 않았습니다.");
      return;
    }
    isRunning = true;
    log("매매 엔진 시작됨");
    notifyListeners();
  }

  void stopListening() {
    isRunning = false;
    log("매매 엔진 중지");
    notifyListeners();
  }
}
