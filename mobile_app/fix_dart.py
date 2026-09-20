with open('lib/services/remote_api_service.dart', 'w', encoding='utf-8') as f:
    f.write('''import 'dart:convert';
import 'package:http/http.dart' as http;
import 'base_api_service.dart';

class RemoteApiService implements BaseApiService {
  final String baseUrl;
  final String exchange;

  RemoteApiService({required this.baseUrl, required this.exchange});

  @override
  Future<Map<String, dynamic>> getStatus() async {
    try {
      final res = await http.get(Uri.parse('\/status?exchange=\')).timeout(const Duration(seconds: 5));
      if (res.statusCode == 200) return jsonDecode(res.body);
      return {'status': 'error', 'message': 'HTTP \'};
    } catch (e) {
      return {'status': 'error', 'message': e.toString()};
    }
  }

  @override
  Future<double> getPrice(String symbol) async {
    try {
      final res = await http.get(Uri.parse('\/price?exchange=\&symbol=\')).timeout(const Duration(seconds: 3));
      if (res.statusCode == 200) {
        final data = jsonDecode(res.body);
        return (data['price'] ?? 0).toDouble();
      }
      return 0.0;
    } catch (e) {
      return 0.0;
    }
  }

  @override
  Future<Map<String, dynamic>> sendOrder(String side, String symbol, double quantity, double price) async {
    try {
      final res = await http.post(
        Uri.parse('\/order/manual'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({"exchange": exchange, "side": side, "symbol": symbol, "quantity": quantity, "price": price}),
      ).timeout(const Duration(seconds: 10));
      if (res.statusCode == 200) return jsonDecode(res.body);
      return {'status': 'error', 'message': 'HTTP \'};
    } catch (e) {
      return {'status': 'error', 'message': e.toString()};
    }
  }

  @override
  Future<Map<String, dynamic>> cancelAllOrders() async {
    try {
      final res = await http.post(
        Uri.parse('\/order/cancel_all'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({"exchange": exchange}),
      ).timeout(const Duration(seconds: 15));
      if (res.statusCode == 200) return jsonDecode(res.body);
      return {'status': 'error', 'message': 'HTTP \'};
    } catch (e) {
      return {'status': 'error', 'message': e.toString()};
    }
  }
}
''')

with open('lib/screens/dashboard_view.dart', 'w', encoding='utf-8') as f:
    f.write('''import 'package:flutter/material.dart';
import '../services/base_api_service.dart';

class DashboardView extends StatefulWidget {
  final BaseApiService apiService;
  const DashboardView({super.key, required this.apiService});

  @override
  State<DashboardView> createState() => _DashboardViewState();
}

class _DashboardViewState extends State<DashboardView> {
  int balance = 0;
  bool isLoading = true;
  String errMsg = "";

  @override
  void initState() {
    super.initState();
    _fetch();
  }

  void _fetch() async {
    setState(() { isLoading = true; errMsg = ""; });
    final res = await widget.apiService.getStatus();
    setState(() {
      isLoading = false;
      if (res['status'] == 'success') {
        balance = res['balance'] ?? 0;
      } else {
        errMsg = res['message'] ?? 'Unknown Error';
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    if (isLoading) return const Center(child: CircularProgressIndicator());
    
    return Padding(
      padding: const EdgeInsets.all(16.0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          const Text("💰 현재 계좌 상태", style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold)),
          const SizedBox(height: 16),
          Card(
            color: Colors.blueGrey[900],
            child: Padding(
              padding: const EdgeInsets.all(24.0),
              child: errMsg.isNotEmpty
                  ? Text("조회 실패: \", style: const TextStyle(color: Colors.redAccent))
                  : Text("예수금: \ 원", style: const TextStyle(fontSize: 24, fontWeight: FontWeight.bold)),
            ),
          ),
          const SizedBox(height: 24),
          ElevatedButton.icon(
            onPressed: _fetch,
            icon: const Icon(Icons.refresh),
            label: const Text("새로고침"),
            style: ElevatedButton.styleFrom(padding: const EdgeInsets.symmetric(vertical: 16)),
          )
        ],
      ),
    );
  }
}
''')

with open('lib/screens/grid_order_view.dart', 'w', encoding='utf-8') as f:
    f.write('''import 'package:flutter/material.dart';
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
        content: Text('총 \건 중\\n✅ 성공: \건\\n❌ 실패: \건'),
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
                Text("🚀 순차 전송 중... \%"),
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
''')

with open('lib/screens/positions_view.dart', 'w', encoding='utf-8') as f:
    f.write('''import 'package:flutter/material.dart';
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
    
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(res['status'] == 'success' ? '취소 완료' : '취소 실패: \')));
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
              Text("거미줄 현황 (\건)", style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
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
                      title: Text("\ 원"),
                      subtitle: Text("종목: \ | 수량: \"),
                    );
                  },
                ),
        )
      ],
    );
  }
}
''')
