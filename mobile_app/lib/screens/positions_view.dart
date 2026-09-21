import 'package:flutter/material.dart';
import '../services/base_api_service.dart';

class PositionsView extends StatefulWidget {
  final BaseApiService apiService;
  const PositionsView({super.key, required this.apiService});

  @override
  State<PositionsView> createState() => _PositionsViewState();
}

class _PositionsViewState extends State<PositionsView> {
  List<dynamic> allPositions = [];
  List<int> selectedIds = [];
  
  bool isLoading = true;
  String currentExchange = "kis";
  double balance = 0;
  int totalProfit = 0;
  int tradeCount = 0;
  bool isRunning = false;
  List<dynamic> history = [];

  @override
  void initState() {
    super.initState();
    _loadPositions();
    _loadHistory();
  }

  Future<void> _loadPositions() async {
    setState(() => isLoading = true);
    final data = await widget.apiService.getStatus();
    
    if (data['status'] == 'error' && data['message'] != null) {
        setState(() => isLoading = false);
        return;
    }

    setState(() {
      currentExchange = data['config']?['exchange'] ?? "kis";
      balance = (data['balance'] ?? 0).toDouble();
      totalProfit = data['total_profit'] ?? 0;
      tradeCount = data['trade_count'] ?? 0;
      isRunning = data['running'] ?? false;
      
      // Backend uses 'positions' key
      allPositions = List<dynamic>.from(data['positions'] ?? []);
      
      // clear selected if they don't exist anymore
      final existingIds = allPositions.map((p) => p['id'] as int).toList();
      selectedIds.removeWhere((id) => !existingIds.contains(id));
      
      isLoading = false;
    });
  }

  Future<void> _loadHistory() async {
    final hist = await widget.apiService.getHistory(limit: 50);
    setState(() {
      history = hist;
    });
  }

  Future<void> _toggleBot(bool start) async {
    setState(() => isLoading = true);
    if (start) {
      await widget.apiService.startBot();
    } else {
      await widget.apiService.stopBot();
    }
    await _loadPositions();
  }

  Future<void> _restartBot() async {
    final bool? confirm = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('서버 재시작'),
        content: const Text('봇 코어 루프를 재시작하시겠습니까?'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('취소')),
          TextButton(onPressed: () => Navigator.pop(ctx, true), child: const Text('재시작')),
        ],
      )
    );
    if (confirm != true) return;
    
    setState(() => isLoading = true);
    await widget.apiService.restartBot();
    await Future.delayed(const Duration(seconds: 2));
    await _loadPositions();
  }

  Future<void> _syncServer() async {
    setState(() => isLoading = true);
    await widget.apiService.syncOrders();
    await _loadPositions();
  }

  Future<void> _cancelOrder(String id) async {
    final bool? confirm = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('주문 취소'),
        content: const Text('정말 해당 주문을 취소하시겠습니까?'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('아니오')),
          TextButton(onPressed: () => Navigator.pop(ctx, true), style: TextButton.styleFrom(foregroundColor: Colors.red), child: const Text('네, 취소합니다')),
        ],
      )
    );
    if (confirm != true) return;

    try {
      final res = await widget.apiService.cancelOrder(id);
      if (!mounted) return;
      if (res['status'] == 'success') {
        await showDialog(
          context: context,
          builder: (ctx) => AlertDialog(
            title: const Text('주문 취소 결과'),
            content: Text(res['message'] ?? '주문이 취소되었습니다.'),
            actions: [TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('확인'))],
          )
        );
        _loadPositions();
      } else {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('주문 취소 실패: ${res['message']}'), backgroundColor: Colors.red));
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('에러: $e'), backgroundColor: Colors.red));
    }
  }

  Future<void> _cancelSelected() async {
    if (selectedIds.isEmpty) return;
    final bool? confirm = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('선택 주문 취소'),
        content: Text('${selectedIds.length}건의 주문을 취소하시겠습니까?'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('아니오')),
          TextButton(onPressed: () => Navigator.pop(ctx, true), style: TextButton.styleFrom(foregroundColor: Colors.red), child: const Text('네, 취소합니다')),
        ],
      )
    );
    if (confirm != true) return;

    try {
      final res = await widget.apiService.cancelList(selectedIds);
      if (!mounted) return;
      if (res['status'] == 'success' || (res['message'] != null && res['message'].toString().contains("성공"))) {
        await showDialog(
          context: context,
          builder: (ctx) => AlertDialog(
            title: const Text('주문 취소 결과'),
            content: Text(res['message'] ?? '선택 주문이 취소되었습니다.'),
            actions: [TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('확인'))],
          )
        );
        _loadPositions();
      } else {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('주문 취소 실패: ${res['message']}'), backgroundColor: Colors.red));
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('에러: $e'), backgroundColor: Colors.red));
    }
  }

  Future<void> _cancelAllPositions() async {
    final bool? confirm = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('⚠️ 전체 포지션 취소'),
        content: const Text('현재 거래소의 모든 미체결 주문을 일괄 취소하시겠습니까? 이 작업은 되돌릴 수 없습니다.'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('닫기')),
          TextButton(onPressed: () => Navigator.pop(ctx, true), style: TextButton.styleFrom(foregroundColor: Colors.red), child: const Text('네, 일괄 취소합니다')),
        ],
      )
    );
    if (confirm != true) return;

    try {
      final res = await widget.apiService.cancelAllOrders();
      if (!mounted) return;
      if (res['status'] == 'success' || res['status'] == 'partial') {
        await showDialog(
          context: context,
          builder: (ctx) => AlertDialog(
            title: const Text('주문 일괄 취소 결과'),
            content: Text(res['message'] ?? '전체 주문 일괄 취소가 처리되었습니다.'),
            actions: [TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('확인'))],
          )
        );
        _loadPositions();
      } else {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('❌ 일괄 취소 실패: ${res['message']}'), backgroundColor: Colors.red));
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('에러: $e'), backgroundColor: Colors.red));
    }
  }

  Future<void> _clearHistory() async {
    final bool? confirm = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('⚠️ 내역 초기화'),
        content: const Text('거래 내역을 영구 삭제하시겠습니까?'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('닫기')),
          TextButton(onPressed: () => Navigator.pop(ctx, true), style: TextButton.styleFrom(foregroundColor: Colors.red), child: const Text('영구 삭제')),
        ],
      )
    );
    if (confirm != true) return;
    
    await widget.apiService.clearHistory();
    _loadHistory();
  }

  Widget _buildAssetCard() {
    return Card(
      elevation: 3,
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text("💰 총 자산 (예수금)", style: TextStyle(fontSize: 16)),
                Text("${balance.toStringAsFixed(0)} 원", style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
              ],
            ),
            const Divider(),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text("누적 실현 수익", style: TextStyle(fontSize: 14)),
                Text("${totalProfit} 원", style: const TextStyle(fontSize: 14, fontWeight: FontWeight.bold, color: Colors.blue)),
              ],
            ),
            const SizedBox(height: 8),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text("금일 체결 횟수", style: TextStyle(fontSize: 14)),
                Text("${tradeCount} 회", style: const TextStyle(fontSize: 14, fontWeight: FontWeight.bold)),
              ],
            ),
            const SizedBox(height: 8),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text("활성 거래중 노드", style: TextStyle(fontSize: 14)),
                Text("${allPositions.length} 개", style: const TextStyle(fontSize: 14, fontWeight: FontWeight.bold)),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildControlCard() {
    return Card(
      elevation: 3,
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceEvenly,
          children: [
            ElevatedButton.icon(
              onPressed: isRunning ? null : () => _toggleBot(true),
              icon: const Icon(Icons.play_arrow),
              label: const Text("시작"),
              style: ElevatedButton.styleFrom(backgroundColor: Colors.green),
            ),
            ElevatedButton.icon(
              onPressed: !isRunning ? null : () => _toggleBot(false),
              icon: const Icon(Icons.stop),
              label: const Text("정지"),
              style: ElevatedButton.styleFrom(backgroundColor: Colors.orange),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildPositionsList() {
    if (allPositions.isEmpty) {
      return const Center(child: Text("활성화된 포지션이 없습니다."));
    }
    return ListView.builder(
      itemCount: allPositions.length,
      itemBuilder: (context, index) {
        final pos = allPositions[index];
        final id = pos['id'] as int;
        final isSell = pos['side'] == 'sell';
        final color = isSell ? Colors.blue.shade50 : Colors.pink.shade50;
        
        return Card(
          color: color,
          child: CheckboxListTile(
            value: selectedIds.contains(id),
            onChanged: (bool? checked) {
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
            secondary: IconButton(
              icon: const Icon(Icons.cancel, color: Colors.red),
              onPressed: () => _cancelOrder(id.toString()), // SQLite ID for accurate cancel
            ),
          ),
        );
      },
    );
  }

  Widget _buildHistoryList() {
    if (history.isEmpty) {
      return const Center(child: Text("거래 내역이 없습니다."));
    }
    return ListView.builder(
      itemCount: history.length,
      itemBuilder: (context, index) {
        final hist = history[index];
        final isSell = hist['side'] == 'sell';
        return Card(
          child: ListTile(
            leading: Icon(isSell ? Icons.arrow_upward : Icons.arrow_downward, color: isSell ? Colors.blue : Colors.red),
            title: Text("${hist['price']} 원 (${hist['quantity']} 주)"),
            subtitle: Text("${hist['filled_at'] ?? ''} - ${hist['status']}"),
          ),
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    return DefaultTabController(
      length: 2,
      child: Scaffold(
        appBar: AppBar(
          title: Text('$currentExchange 현황'),
          actions: [
            IconButton(icon: const Icon(Icons.sync), onPressed: _syncServer),
            IconButton(icon: const Icon(Icons.refresh), onPressed: () { _loadPositions(); _loadHistory(); })
          ],
          bottom: const TabBar(
            tabs: [
              Tab(text: "활성 포지션"),
              Tab(text: "거래 내역"),
            ],
          ),
        ),
        body: isLoading
          ? const Center(child: CircularProgressIndicator())
          : TabBarView(
              children: [
                // Tab 1: Positions
                Column(
                  children: [
                    _buildAssetCard(),
                    _buildControlCard(),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                      children: [
                        ElevatedButton(
                          onPressed: selectedIds.isEmpty ? null : _cancelSelected,
                          child: Text("선택 취소 (${selectedIds.length})"),
                        ),
                        ElevatedButton(
                          onPressed: _cancelAllPositions,
                          style: ElevatedButton.styleFrom(backgroundColor: Colors.red),
                          child: const Text("⚠️ 전체 취소", style: TextStyle(color: Colors.white)),
                        ),
                      ],
                    ),
                    Expanded(child: _buildPositionsList()),
                  ],
                ),
                // Tab 2: History
                Column(
                  children: [
                    Padding(
                      padding: const EdgeInsets.all(8.0),
                      child: ElevatedButton.icon(
                        onPressed: _clearHistory,
                        icon: const Icon(Icons.delete_forever),
                        label: const Text("내역 영구 삭제"),
                        style: ElevatedButton.styleFrom(backgroundColor: Colors.redAccent),
                      ),
                    ),
                    Expanded(child: _buildHistoryList()),
                  ],
                )
              ],
            ),
      ),
    );
  }
}
