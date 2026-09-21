import 'package:flutter/material.dart';
import 'main_tab_screen.dart';
import '../services/remote_api_service.dart';
import '../services/kis_standalone_service.dart';
import '../services/secure_settings.dart';
import '../core/trading_engine.dart';

class LandingScreen extends StatelessWidget {
  const LandingScreen({super.key});

  void _goRemote(BuildContext context) {
    // 실제로는 설정화면에서 IP를 입력받아야 하지만 여기서는 데모용 하드코딩
    final service = RemoteApiService(baseUrl: "http://192.168.0.10:8000", exchange: "kis");
    Navigator.push(context, MaterialPageRoute(builder: (_) => MainTabScreen(apiService: service, title: "리모컨 모드 (PC)")));
  }

  void _goStandalone(BuildContext context) async {
    // 보안 저장소에서 키 불러오기
    final keys = await SecureSettings.getKisKeys();
    String appKey = keys['appKey']!;
    String appSecret = keys['appSecret']!;
    String cano = keys['cano']!;

    if (appKey.isEmpty) {
      // 데모를 위해 임시 키 삽입 (실제로는 설정 UI가 필요함)
      appKey = "DEMO_APP_KEY";
      appSecret = "DEMO_SECRET";
      cano = "12345678";
    }

    // 엔진 초기화
    final engine = TradingEngine();
    await engine.init(appKey, appSecret, cano);
    engine.startListening(); // 엔진 로그 시작

    final service = KisStandaloneService(engine.kisApi!, engine: engine);
    Navigator.push(context, MaterialPageRoute(builder: (_) => MainTabScreen(apiService: service, title: "단독 봇 모드 (KIS)")));
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('모드 선택')),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            ElevatedButton.icon(
              style: ElevatedButton.styleFrom(padding: const EdgeInsets.all(24), backgroundColor: Colors.teal),
              icon: const Icon(Icons.wifi_tethering, size: 36, color: Colors.white),
              label: const Text('리모컨 모드 (PC 봇 연결)', style: TextStyle(fontSize: 20, color: Colors.white)),
              onPressed: () => _goRemote(context),
            ),
            const SizedBox(height: 32),
            ElevatedButton.icon(
              style: ElevatedButton.styleFrom(padding: const EdgeInsets.all(24), backgroundColor: Colors.deepOrangeAccent),
              icon: const Icon(Icons.smart_toy, size: 36, color: Colors.white),
              label: const Text('KIS 단독 봇 모드', style: TextStyle(fontSize: 20, color: Colors.white)),
              onPressed: () => _goStandalone(context),
            ),
          ],
        ),
      ),
    );
  }
}
