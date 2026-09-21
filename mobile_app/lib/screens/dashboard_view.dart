import 'dart:async';
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
  List<dynamic> allPositions = [];
  List<int> selectedIds = [];

  // 윈도우 앱의 run_loop와 동일하게 1분 주기로 상태 및 동기화를 자동 갱신하는 타이머
  Timer? _periodicTimer;

  @override
  void initState() {
    super.initState();
    _fetchStatus();
    // 윈도우 앱의 auto_sync_interval(기본 1분)과 동일한 주기로 상태 자동 갱신
    // syncOrders()는 getStatus() 내부에서 1분 경과 시 unawaited로 트리거됨
    _periodicTimer = Timer.periodic(const Duration(minutes: 1), (_) {
      _fetchStatus();
    });
  }

  @override
  void dispose() {
    // 화면이 파괴될 때 타이머를 반드시 취소하여 메모리 누수 방지
    _periodicTimer?.cancel();
    super.dispose();
  }

  Future<void> _fetchStatus() async {
    setState(() => _isLoading = true);
    final data = await widget.apiService.getStatus();
    if (mounted) {
      setState(() {
        _isLoading = false;
        if (data['status'] == 'success') {
          isRunning = data['running'] ?? false;
          balance = data['balance'] ?? 0;
          totalProfit = data['total_profit'] ?? 0;
          tradeCount = data['trade_count'] ?? 0;
          isConnected = data['exchange_connected'] ?? true;
          allPositions = List<dynamic>.from(data['positions'] ?? []);
        } else {
          ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('상태 갱신 실패: ${data['message']}')));
        }
      });
    }
  }

  Future<void> _refreshBalance() async {
    final res = await widget.apiService.refreshBalance();
    if (res['status'] == 'success') {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('✅ 잔고 갱신 완료'), backgroundColor: Colors.green),
      );
      _fetchStatus();
    } else {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text("❌ 잔고 갱신 실패: ${res['message']}"), backgroundColor: Colors.red),
      );
    }
  }

  Future<void> _cancelSelectedOrders() async {
    if (selectedIds.isEmpty) return;
    for (int id in selectedIds) {
      await widget.apiService.cancelOrder(id.toString());
    }
    setState(() {
      selectedIds.clear();
    });
    ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('선택한 주문 취소 요청 완료')));
    _fetchStatus();
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return const Center(child: CircularProgressIndicator());
    }
    
    return Scaffold(
      appBar: AppBar(
        title: const Text('📊 현황'),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text("📊 주문 현황", style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                if (selectedIds.isNotEmpty)
                  ElevatedButton.icon(
                    onPressed: _cancelSelectedOrders,
                    icon: const Icon(Icons.delete),
                    label: Text("선택한 ${selectedIds.length}건 주문 취소"),
                    style: ElevatedButton.styleFrom(backgroundColor: Colors.redAccent, foregroundColor: Colors.white),
                  )
              ],
            ),
            const SizedBox(height: 8),
            if (allPositions.isEmpty)
              const Center(child: Text("활성화된 포지션이 없습니다.", style: TextStyle(color: Colors.grey)))
            else
              ListView.builder(
                shrinkWrap: true,
                physics: const NeverScrollableScrollPhysics(),
                itemCount: allPositions.length,
                itemBuilder: (ctx, i) {
                  final pos = allPositions[i];
                  final id = pos['id'] as int;
                  final isSell = pos['side'] == 'sell';
                  return Card(
                    child: CheckboxListTile(
                      value: selectedIds.contains(id),
                      onChanged: (checked) {
                        setState(() {
                          if (checked == true) {
                            selectedIds.add(id);
                          } else {
                            selectedIds.remove(id);
                          }
                        });
                      },
                      title: Text("${isSell ? '🔵 매도' : '🔴 매수'} | 단가: ${pos['price'] ?? pos['avg_price']}"),
                      subtitle: Text("수량: ${pos['quantity']} | ID: $id"),
                    ),
                  );
                },
              ),
            const SizedBox(height: 24),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text("💰 내 자산 및 수익 현황", style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                IconButton(icon: const Icon(Icons.refresh), onPressed: _refreshBalance, tooltip: '잔고 갱신'),
              ],
            ),
            const SizedBox(height: 8),
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
                          Text("$balance 원", style: const TextStyle(fontSize: 24, fontWeight: FontWeight.bold)),
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
                          Text("+$totalProfit 원", style: const TextStyle(fontSize: 24, fontWeight: FontWeight.bold, color: Colors.redAccent)),
                          Text("금일 체결: $tradeCount 회", style: const TextStyle(color: Colors.grey, fontSize: 12)),
                        ],
                      ),
                    ),
                  ),
                )
              ],
            ),
        ],
      ),
    ),
    );
  }
}
