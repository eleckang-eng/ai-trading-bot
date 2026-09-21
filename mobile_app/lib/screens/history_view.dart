import 'package:flutter/material.dart';
import '../services/base_api_service.dart';

class HistoryView extends StatefulWidget {
  final BaseApiService apiService;
  const HistoryView({super.key, required this.apiService});

  @override
  State<HistoryView> createState() => _HistoryViewState();
}

class _HistoryViewState extends State<HistoryView> {
  List<dynamic> _history = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _fetchHistory();
  }

  Future<void> _fetchHistory() async {
    setState(() => _isLoading = true);
    final data = await widget.apiService.getHistory(limit: 100);
    setState(() {
      _history = data;
      _isLoading = false;
    });
  }

  Future<void> _clearHistory() async {
    final bool? confirm = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('🗑️ 내역 초기화'),
        content: const Text('정말 모든 거래 내역을 영구 삭제하시겠습니까?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: const Text('취소'),
          ),
          TextButton(
            onPressed: () => Navigator.pop(ctx, true),
            style: TextButton.styleFrom(foregroundColor: Colors.red),
            child: const Text('영구 삭제'),
          ),
        ],
      ),
    );

    if (confirm == true) {
      final res = await widget.apiService.clearHistory();
      if (res['status'] == 'success') {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('✅ 거래 내역이 성공적으로 초기화되었습니다.'), backgroundColor: Colors.green),
        );
        _fetchHistory();
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('❌ 초기화 실패: ${res['message']}'), backgroundColor: Colors.red),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('💸 실시간 거래 내역')),
      body: Column(
        children: [
        Padding(
          padding: const EdgeInsets.all(8.0),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.end,
            children: [
              ElevatedButton.icon(
                onPressed: _fetchHistory,
                icon: const Icon(Icons.refresh),
                label: const Text('새로고침'),
              ),
              const SizedBox(width: 8),
              ElevatedButton.icon(
                onPressed: _clearHistory,
                icon: const Icon(Icons.delete_outline),
                label: const Text('내역 초기화'),
                style: ElevatedButton.styleFrom(foregroundColor: Colors.red),
              ),
            ],
          ),
        ),
        Expanded(
          child: _isLoading
              ? const Center(child: CircularProgressIndicator())
              : _history.isEmpty
                  ? const Center(child: Text('아직 기록된 체결 또는 취소 내역이 없습니다.'))
                  : ListView.builder(
                      itemCount: _history.length,
                      itemBuilder: (context, index) {
                        final item = _history[index];
                        final bool isBuy = item['side'] == 'buy';
                        final bool isFilled = item['status'] == 'filled';

                        return Card(
                          margin: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                          child: ListTile(
                            leading: CircleAvatar(
                              backgroundColor: isBuy ? Colors.red.shade100 : Colors.blue.shade100,
                              child: Text(
                                isBuy ? '매수' : '매도',
                                style: TextStyle(color: isBuy ? Colors.red : Colors.blue, fontWeight: FontWeight.bold),
                              ),
                            ),
                            title: Text('${item['price']} 원', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                            subtitle: Text('수량: ${item['quantity']} | 시간: ${item['filled_at']}'),
                            trailing: Chip(
                              label: Text(isFilled ? '체결' : '취소'),
                              backgroundColor: isFilled ? Colors.green.shade100 : Colors.grey.shade300,
                            ),
                          ),
                        );
                      },
                    ),
        ),
      ],
      ),
    );
  }
}
