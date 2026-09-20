import 'package:flutter/material.dart';
import 'screens/landing_screen.dart';

void main() {
  runApp(const TradingBotApp());
}

class TradingBotApp extends StatelessWidget {
  const TradingBotApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: '한화오션 핑퐁 봇',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.blue),
        useMaterial3: true,
      ),
      home: const LandingScreen(),
    );
  }
}

  const DashboardScreen({super.key});

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  // 사용자 PC 고정 IP 적용 완료
  String apiUrl = "http://192.168.45.108:8000";
  
  bool isRunning = false;
  int balance = 0;
  int totalProfit = 0;
  List<dynamic> positions = [];
  Timer? _timer;

  @override
  void initState() {
    super.initState();
    _fetchStatus();
    // 5초마다 상태 자동 갱신
    _timer = Timer.periodic(const Duration(seconds: 5), (timer) {
      _fetchStatus();
    });
  }

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  Future<void> _fetchStatus() async {
    try {
      final response = await http.get(Uri.parse('$apiUrl/status'));
      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        setState(() {
          isRunning = data['running'] ?? false;
          balance = data['balance'] ?? 0;
          // 백엔드에 total_profit이 아직 없다면 0으로 처리
          totalProfit = data['total_profit'] ?? 0; 
          positions = data['positions'] ?? [];
        });
      }
    } catch (e) {
      debugPrint("통신 오류: $e");
    }
  }

  Future<void> _controlSystem(String action) async {
    try {
      final response = await http.post(Uri.parse('$apiUrl/$action'));
      if (response.statusCode == 200) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(action == 'start' ? '시스템이 시작되었습니다.' : '시스템이 정지되었습니다.')),
        );
        _fetchStatus();
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('서버 통신 실패: $e')),
      );
    }
  }

  void _showSettingsDialog() {
    TextEditingController urlController = TextEditingController(text: apiUrl);
    showDialog(
      context: context,
      builder: (context) {
        return AlertDialog(
          title: const Text('서버 설정'),
          content: TextField(
            controller: urlController,
            decoration: const InputDecoration(labelText: '백엔드 API 주소'),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text('취소'),
            ),
            TextButton(
              onPressed: () {
                setState(() {
                  apiUrl = urlController.text;
                });
                Navigator.pop(context);
                _fetchStatus();
              },
              child: const Text('저장'),
            ),
          ],
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('AI 핑퐁 봇'),
        backgroundColor: Theme.of(context).colorScheme.inversePrimary,
        actions: [
          IconButton(
            icon: const Icon(Icons.settings),
            onPressed: _showSettingsDialog,
          )
        ],
      ),
      body: RefreshIndicator(
        onRefresh: _fetchStatus,
        child: ListView(
          padding: const EdgeInsets.all(16.0),
          children: [
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16.0),
                child: Column(
                  children: [
                    Text('현재 상태', style: Theme.of(context).textTheme.titleLarge),
                    const SizedBox(height: 10),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Icon(
                          isRunning ? Icons.play_circle_fill : Icons.stop_circle,
                          color: isRunning ? Colors.green : Colors.red,
                          size: 32,
                        ),
                        const SizedBox(width: 10),
                        Text(
                          isRunning ? '가동 중' : '정지됨',
                          style: const TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 16),
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16.0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('계좌 현황', style: Theme.of(context).textTheme.titleLarge),
                    const Divider(),
                    ListTile(
                      title: const Text('예수금 (잔고)'),
                      trailing: Text('$balance 원', style: const TextStyle(fontSize: 18)),
                    ),
                    ListTile(
                      title: const Text('핑퐁 누적 수익'),
                      trailing: Text('$totalProfit 원', style: const TextStyle(fontSize: 18)),
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 16),
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16.0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('활성 포지션', style: Theme.of(context).textTheme.titleLarge),
                    const Divider(),
                    if (positions.isEmpty)
                      const Padding(
                        padding: EdgeInsets.all(16.0),
                        child: Text('보유 중인 포지션이 없습니다.'),
                      ),
                    for (var pos in positions)
                      ListTile(
                        title: Text('종목코드: ${pos['symbol']}'),
                        subtitle: Text('평단가: ${pos['avg_price']} 원'),
                        trailing: Text('수량: ${pos['quantity']}'),
                      ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 32),
            Row(
              children: [
                Expanded(
                  child: ElevatedButton.icon(
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.green,
                      foregroundColor: Colors.white,
                      padding: const EdgeInsets.symmetric(vertical: 16),
                    ),
                    icon: const Icon(Icons.play_arrow),
                    label: const Text('시스템 시작', style: TextStyle(fontSize: 18)),
                    onPressed: () => _controlSystem('start'),
                  ),
                ),
                const SizedBox(width: 16),
                Expanded(
                  child: ElevatedButton.icon(
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.red,
                      foregroundColor: Colors.white,
                      padding: const EdgeInsets.symmetric(vertical: 16),
                    ),
                    icon: const Icon(Icons.stop),
                    label: const Text('비상 정지', style: TextStyle(fontSize: 18)),
                    onPressed: () => _controlSystem('stop'),
                  ),
                ),
              ],
            )
          ],
        ),
      ),
    );
  }
}
