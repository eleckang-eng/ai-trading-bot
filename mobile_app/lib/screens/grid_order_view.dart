import 'package:flutter/material.dart';
import '../services/base_api_service.dart';

class GridOrderView extends StatefulWidget {
  final BaseApiService apiService;
  const GridOrderView({super.key, required this.apiService});

  @override
  State<GridOrderView> createState() => _GridOrderViewState();
}

class _GridOrderViewState extends State<GridOrderView> {
  String _direction = 'both';
  int _count = 5;
  String symbol = "005930"; // 삼성전자 고정(데모)
  bool _isSending = false;
  double _progress = 0.0;
  
  void _executeBatchOrder() async {
    setState(() { _isSending = true; _progress = 0.0; });
    
    // 데모: 현재가 30000원 기준 500원 간격
    double curPrice = 30000;
    List<Map<String, dynamic>> orders = [];
    double gap = 500;
    double qty = 1;

    if (_direction == 'sell' || _direction == 'both') {
      for (int i = 1; i <= _count; i++) orders.add({'side': 'sell', 'price': curPrice + (i * gap), 'quantity': qty});
    }
    if (_direction == 'buy' || _direction == 'both') {
      for (int i = 1; i <= _count; i++) orders.add({'side': 'buy', 'price': curPrice - (i * gap), 'quantity': qty});
    }

    int total = orders.length;
    int success = 0;
    int fail = 0;

    for (int i = 0; i < total; i++) {
      setState(() => _progress = (i + 1) / total);
      final res = await widget.apiService.sendOrder(orders[i]['side'], symbol, orders[i]['quantity'], orders[i]['price']);
      if (res['status'] == 'success') {
        success++;
      } else {
        fail++;
      }
      await Future.delayed(const Duration(milliseconds: 250));
    }

    setState(() { _isSending = false; });
    
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('일괄 주문 완료'),
        content: Text('총 ${total}건 중\n✅ 성공: ${success}건\n❌ 실패: ${fail}건'),
        actions: [TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('확인'))],
      )
    );
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(16.0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          const Text("그리드 방향", style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
          Row(
            children: [
              Radio(value: 'both', groupValue: _direction, onChanged: (v) => setState(() => _direction = v.toString())), const Text("양방향"),
              Radio(value: 'buy', groupValue: _direction, onChanged: (v) => setState(() => _direction = v.toString())), const Text("매수"),
              Radio(value: 'sell', groupValue: _direction, onChanged: (v) => setState(() => _direction = v.toString())), const Text("매도"),
            ],
          ),
          const SizedBox(height: 16),
          const Text("한 방향당 주문 개수", style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
          Slider(
            value: _count.toDouble(), min: 1, max: 20, divisions: 19, label: _count.toString(),
            onChanged: (val) => setState(() => _count = val.toInt()),
          ),
          const Spacer(),
          if (_isSending)
            Column(
              children: [
                LinearProgressIndicator(value: _progress),
                const SizedBox(height: 8),
                Text("🚀 순차 전송 중... ${(_progress * 100).toStringAsFixed(0)}%"),
              ],
            ),
          const SizedBox(height: 16),
          ElevatedButton(
            onPressed: _isSending ? null : _executeBatchOrder,
            style: ElevatedButton.styleFrom(backgroundColor: Colors.blueAccent, padding: const EdgeInsets.symmetric(vertical: 20)),
            child: const Text("일괄 주문 전송", style: TextStyle(fontSize: 18, color: Colors.white)),
          )
        ],
      ),
    );
  }
}
