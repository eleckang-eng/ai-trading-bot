import 'package:flutter/material.dart';
import '../services/base_api_service.dart';

class PositionsView extends StatefulWidget {
  final BaseApiService apiService;
  const PositionsView({super.key, required this.apiService});

  @override
  State<PositionsView> createState() => _PositionsViewState();
}

class _PositionsViewState extends State<PositionsView> {
  List<dynamic> sellPositions = [];
  List<dynamic> buyPositions = [];
  bool isLoading = true;
  String currentExchange = "kis";

  @override
  void initState() {
    super.initState();
    _loadPositions();
  }

  Future<void> _loadPositions() async {
    setState(() => isLoading = true);
    final data = await widget.apiService.getStatus();
    
    setState(() {
      if (data['status'] == 'success') {
        currentExchange = data['config']?['exchange'] ?? "kis";
        final bullets = List<dynamic>.from(data['bullets'] ?? []);
        sellPositions = bullets.where((p) => p['side'] == 'sell').toList();
        buyPositions = bullets.where((p) => p['side'] == 'buy').toList();
        
        sellPositions.sort((a, b) => (b['price'] as num).compareTo(a['price'] as num));
        buyPositions.sort((a, b) => (b['price'] as num).compareTo(a['price'] as num));
      } else {
        sellPositions = [];
        buyPositions = [];
      }
      isLoading = false;
    });
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
      if (res['status'] == 'success') {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('주문이 취소되었습니다.')));
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
      if (res['status'] == 'success') {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('✅ 전체 주문 일괄 취소가 서버로 요청되었습니다.'), backgroundColor: Colors.green));
        _loadPositions();
      } else {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('❌ 일괄 취소 실패: ${res['message']}'), backgroundColor: Colors.red));
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('에러: $e'), backgroundColor: Colors.red));
    }
  }

  Widget _buildPositionTable(String title, List<dynamic> positions, Color headerColor) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Container(
          padding: const EdgeInsets.all(8),
          color: headerColor,
          child: Text("$title (${positions.length}건)", style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
        ),
        if (positions.isEmpty)
          const Padding(padding: EdgeInsets.all(16.0), child: Text("포지션 없음", textAlign: TextAlign.center))
        else
          ListView.builder(
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            itemCount: positions.length,
            itemBuilder: (context, index) {
              final pos = positions[index];
              return Card(
                child: ListTile(
                  title: Text("진입가: ${pos['price']}원"),
                  subtitle: Text("수량: ${pos['quantity']}주"),
                  trailing: IconButton(
                    icon: const Icon(Icons.cancel, color: Colors.red),
                    onPressed: () => _cancelOrder(pos['order_id'].toString()),
                  ),
                ),
              );
            },
          ),
      ],
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('$currentExchange 호가창 현황'),
        actions: [
          IconButton(icon: const Icon(Icons.refresh), onPressed: _loadPositions)
        ],
      ),
      body: isLoading
        ? const Center(child: CircularProgressIndicator())
        : SingleChildScrollView(
            padding: const EdgeInsets.all(8.0),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                ElevatedButton.icon(
                  onPressed: _cancelAllPositions,
                  icon: const Icon(Icons.warning, color: Colors.white),
                  label: const Text("⚠️ 전체 포지션 취소", style: TextStyle(color: Colors.white)),
                  style: ElevatedButton.styleFrom(backgroundColor: Colors.red, padding: const EdgeInsets.all(16)),
                ),
                const SizedBox(height: 16),
                LayoutBuilder(
                  builder: (context, constraints) {
                    if (constraints.maxWidth > 600) {
                      return Row(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Expanded(child: _buildPositionTable("🔵 매도 포지션", sellPositions, Colors.blue.shade100)),
                          const SizedBox(width: 8),
                          Expanded(child: _buildPositionTable("🔴 매수 포지션", buyPositions, Colors.pink.shade100)),
                        ],
                      );
                    } else {
                      return Column(
                        crossAxisAlignment: CrossAxisAlignment.stretch,
                        children: [
                          _buildPositionTable("🔵 매도 포지션", sellPositions, Colors.blue.shade100),
                          const SizedBox(height: 16),
                          _buildPositionTable("🔴 매수 포지션", buyPositions, Colors.pink.shade100),
                        ],
                      );
                    }
                  }
                )
              ],
            ),
          ),
    );
  }
}
