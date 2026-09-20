import 'package:flutter/material.dart';
import '../services/base_api_service.dart';

class DashboardView extends StatefulWidget {
  final BaseApiService apiService;
  const DashboardView({super.key, required this.apiService});

  @override
  State<DashboardView> createState() => _DashboardViewState();
}

class _DashboardViewState extends State<DashboardView> {
  bool isRunning = false;
  int balance = 0;
  int totalProfit = 0;
  int tradeCount = 0;
  bool isConnected = false;
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _fetchStatus();
  }

  Future<void> _fetchStatus() async {
    setState(() => _isLoading = true);
    final data = await widget.apiService.getStatus();
    setState(() {
      _isLoading = false;
      if (data['status'] == 'success') {
        isRunning = data['running'] ?? false;
        balance = data['balance'] ?? 0;
        totalProfit = data['total_profit'] ?? 0;
        tradeCount = data['trade_count'] ?? 0;
        isConnected = data['exchange_connected'] ?? true;
      }
    });
  }

  Future<void> _refreshBalance() async {
    final res = await widget.apiService.refreshBalance();
    if (res['status'] == 'success') {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('✅ 잔고 동기화가 성공적으로 완료되었습니다.'), backgroundColor: Colors.green),
      );
      _fetchStatus();
    } else {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('❌ 잔고 갱신 실패: ${res['message']}'), backgroundColor: Colors.red),
      );
    }
  }

  void _toggleSystem() {
    setState(() {
      isRunning = !isRunning;
    });
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(isRunning ? '단독 모드 엔진 가동 시작!' : '비상 정지됨')),
    );
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return const Center(child: CircularProgressIndicator());
    }
    
    return Padding(
      padding: const EdgeInsets.all(16.0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Card(
            color: isRunning ? Colors.green.shade100 : Colors.red.shade100,
            child: Padding(
              padding: const EdgeInsets.all(16.0),
              child: Column(
                children: [
                  Text(
                    isRunning ? "🟢 시스템 정상 가동 중" : "🔴 시스템 정지됨",
                    style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
                  ),
                  const SizedBox(height: 16),
                  ElevatedButton.icon(
                    onPressed: _toggleSystem,
                    icon: Icon(isRunning ? Icons.stop : Icons.play_arrow, color: Colors.white),
                    label: Text(isRunning ? "비상 정지 (Kill Switch)" : "시스템 시작", style: const TextStyle(fontSize: 18, color: Colors.white)),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: isRunning ? Colors.red : Colors.green,
                      padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
                    ),
                  )
                ],
              ),
            ),
          ),
          const SizedBox(height: 24),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text("💰 내 자산 및 수익 현황", style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
              ElevatedButton.icon(
                onPressed: _refreshBalance,
                icon: const Icon(Icons.refresh),
                label: const Text("잔고 갱신"),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Row(
            children: [
              Expanded(
                child: Card(
                  child: Padding(
                    padding: const EdgeInsets.all(16.0),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text("총 자산 (예수금)", style: TextStyle(color: Colors.grey)),
                        const SizedBox(height: 8),
                        Text("${balance} 원", style: const TextStyle(fontSize: 24, fontWeight: FontWeight.bold)),
                        Text(isConnected ? "연동 완료" : "연동 실패/대기", style: TextStyle(color: isConnected ? Colors.green : Colors.red, fontSize: 12)),
                      ],
                    ),
                  ),
                ),
              ),
              Expanded(
                child: Card(
                  child: Padding(
                    padding: const EdgeInsets.all(16.0),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text("누적 실현 수익", style: TextStyle(color: Colors.grey)),
                        const SizedBox(height: 8),
                        Text("+${totalProfit} 원", style: const TextStyle(fontSize: 24, fontWeight: FontWeight.bold, color: Colors.redAccent)),
                        Text("금일 체결: $tradeCount 회", style: const TextStyle(color: Colors.grey, fontSize: 12)),
                      ],
                    ),
                  ),
                ),
              )
            ],
          )
        ],
      ),
    );
  }
}
