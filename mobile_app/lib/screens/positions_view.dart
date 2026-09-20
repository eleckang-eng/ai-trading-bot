import 'package:flutter/material.dart';
import '../services/base_api_service.dart';

class PositionsView extends StatefulWidget {
  final BaseApiService apiService;
  const PositionsView({super.key, required this.apiService});

  @override
  State<PositionsView> createState() => _PositionsViewState();
}

class _PositionsViewState extends State<PositionsView> {
  List<dynamic> positions = [];
  bool isLoading = true;

  @override
  void initState() {
    super.initState();
    _fetch();
  }

  void _fetch() async {
    setState(() => isLoading = true);
    final res = await widget.apiService.getStatus();
    setState(() {
      isLoading = false;
      if (res['status'] == 'success') {
        positions = res['positions'] ?? [];
      }
    });
  }

  void _cancelAll() async {
    showDialog(
      context: context, barrierDismissible: false,
      builder: (ctx) => AlertDialog(content: Row(children: const [CircularProgressIndicator(), SizedBox(width: 16), Text("취소 중...")])),
    );
    final res = await widget.apiService.cancelAllOrders();
    Navigator.pop(context);
    
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(res['status'] == 'success' ? '취소 완료' : '취소 실패: ${res["message"]}')));
    _fetch();
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.all(16.0),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text("거미줄 현황 (${positions.length}건)", style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
              ElevatedButton.icon(
                onPressed: positions.isEmpty ? null : _cancelAll,
                icon: const Icon(Icons.delete), label: const Text("일괄 취소"),
                style: ElevatedButton.styleFrom(backgroundColor: Colors.redAccent, foregroundColor: Colors.white),
              )
            ],
          ),
        ),
        Expanded(
          child: isLoading
            ? const Center(child: CircularProgressIndicator())
            : positions.isEmpty
              ? const Center(child: Text("미체결 주문이 없습니다."))
              : ListView.builder(
                  itemCount: positions.length,
                  itemBuilder: (ctx, idx) {
                    final pos = positions[idx];
                    return ListTile(
                      leading: const CircleAvatar(child: Icon(Icons.show_chart)),
                      title: Text("${pos['avg_price'] ?? 0} 원"),
                      subtitle: Text("종목: ${pos['symbol']} | 수량: ${pos['quantity']}"),
                    );
                  },
                ),
        )
      ],
    );
  }
}
