import 'package:flutter/material.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart';
import 'screens/main_tab_screen.dart';
import 'services/kis_standalone_service.dart';
import 'services/secure_settings.dart';
import 'core/trading_engine.dart';
import 'api/kis_api.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  try {
    await dotenv.load(fileName: ".env");
  } catch (e) {
    debugPrint(".env 파일 로드 실패 (파일이 없을 수 있음): $e");
  }
  runApp(const TradingBotApp());
}

class TradingBotApp extends StatefulWidget {
  const TradingBotApp({super.key});
  @override
  State<TradingBotApp> createState() => _TradingBotAppState();
}

class _TradingBotAppState extends State<TradingBotApp> {
  KisStandaloneService? _service;
  String? _errorMsg;

  @override
  void initState() {
    super.initState();
    _initApp();
  }

  /// 앱 초기화: KIS API 키 로드 → 엔진 초기화 → 서비스 생성
  /// 키가 미등록이거나 인증 실패 시에도 앱 자체는 진입 가능하도록 방어 처리
  Future<void> _initApp() async {
    try {
      final keys = await SecureSettings.getKisKeys();
      String appKey = keys['appKey'] ?? '';
      String appSecret = keys['appSecret'] ?? '';
      String cano = keys['cano'] ?? '';

      final engine = TradingEngine();

      // API 키가 비어있어도 일단 엔진 생성 후 설정 화면에서 입력할 수 있게 함
      if (appKey.isNotEmpty && appSecret.isNotEmpty && cano.isNotEmpty) {
        await engine.init(appKey, appSecret, cano);
        engine.startListening();
      } else {
        // 키 미등록 상태: 기본 모의투자 KisApi로 초기화
        engine.kisApi = KisApi(appKey: '', appSecret: '', cano: '', isMock: true);
        engine.log("API 키가 등록되지 않았습니다. 설정에서 등록해주세요.");
      }

      setState(() {
        _service = KisStandaloneService(
          engine.kisApi ?? KisApi(appKey: '', appSecret: '', cano: '', isMock: true),
          engine: engine,
        );
      });
    } catch (e) {
      // 인증 실패 등 예외 발생 시에도 기본 서비스로 진입
      debugPrint("앱 초기화 실패: $e");
      final engine = TradingEngine();
      engine.kisApi = KisApi(appKey: '', appSecret: '', cano: '', isMock: true);
      engine.log("초기화 실패: $e");

      setState(() {
        _service = KisStandaloneService(engine.kisApi!, engine: engine);
        _errorMsg = e.toString();
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'AI 핑퐁 봇',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.blue),
        useMaterial3: true,
      ),
      home: _service == null
          ? const Scaffold(body: Center(child: CircularProgressIndicator()))
          : MainTabScreen(apiService: _service!, title: "AI 핑퐁 봇 (단독)"),
    );
  }
}
