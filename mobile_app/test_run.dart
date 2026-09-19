import 'dart:async';
import 'package:http/http.dart' as http;
import 'lib/api/kis_api.dart';

void main() async {
  print("=== KIS API 모듈 테스트 시작 ===");
  final api = KisApi(
    appKey: 'PSRarsiYPgAaSaIIdJRxcTib2mmirEBR24dH',
    appSecret: 'Zhk3qhtp5jTRZ+yO/HY3pUrmOIp6jmC1WeKSb5l8uThwLCGI6o7Ty7b8GwohVxDnNEO8TaDVWo7VXNb1zq2/50BJ+dY1MvsNv65yu0+bslYNEoNuP4vnvYmdd+DylKy8LJ5e4DBdbe4nsJpI7i78wQ4gAP8jwIZ39asIxzCiFz4qNg5opGw=',
    cano: '50206484',
    isMock: true
  );

  try {
    print("1. OAuth2 토큰 발급 테스트...");
    await api.auth();
    print("-> 토큰 발급 성공!");

    print("2. 잔고 조회 테스트...");
    final balance = await api.getBalance();
    print("-> 잔고 조회 성공: \${balance['output1'][0]['dnca_tot_amt']} 원 (예수금)");
    
  } catch(e) {
    print("에러 발생: \$e");
  }

  print("\n=== 정규식 알림 파싱 로직 테스트 ===");
  // TradingEngine 내부 정규식만 테스트 (ChangeNotifier 의존성 때문에 직접 추출해서 테스트)
  final RegExp buyRegex = RegExp(r'매수.*체결.*(\d+)주.*(\d+,\d+)원');
  final RegExp sellRegex = RegExp(r'매도.*체결.*(\d+)주.*(\d+,\d+)원');
  
  final sampleNotifications = [
    "[한국투자증권] 한화오션 매수체결 50주 28,000원",
    "체결통보 [한국투자증권] 삼성전자 매도 체결 10주 75,000원",
    "단순 광고 알림입니다"
  ];

  for (var msg in sampleNotifications) {
    if (msg.contains("매수") && msg.contains("체결")) {
      final match = buyRegex.firstMatch(msg);
      if (match != null) {
        print("-> [매수 매칭 성공] 원문: \$msg | 수량: \${match.group(1)}주, 가격: \${match.group(2)}원");
      } else {
        print("-> [매수 감지되었으나 파싱 실패] 원문: \$msg");
      }
    } else if (msg.contains("매도") && msg.contains("체결")) {
      final match = sellRegex.firstMatch(msg);
      if (match != null) {
        print("-> [매도 매칭 성공] 원문: \$msg | 수량: \${match.group(1)}주, 가격: \${match.group(2)}원");
      } else {
        print("-> [매도 감지되었으나 파싱 실패] 원문: \$msg");
      }
    } else {
      print("-> [무시됨] \$msg");
    }
  }
}
