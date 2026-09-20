import 'package:flutter/material.dart';
import '../services/base_api_service.dart';
import '../services/database.dart';

class PositionsView extends StatefulWidget {
  final BaseApiService apiService;
  const PositionsView({super.key, required this.apiService});

  @override
  State<PositionsView> createState() => _PositionsViewState();
}

class _PositionsViewState extends State<PositionsView> {
  List<Map<String, dynamic>> sellPositions = [];
  List<Map<String, dynamic>> buyPositions = [];
  bool isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadPositions();
  }

  Future<void> _loadPositions() async {
    setState(() => isLoading = true);
    // 모바일 단독 DB에서 가져오기 (종목 기호 005930 임시 고정)
    final dbHelper = DatabaseHelper.instance;
    final allPos = await dbHelper.getActivePositions("005930");
    
    setState(() {
      sellPositions = allPos.where((p) => p['side'] == 'sell').toList();
      buyPositions = allPos.where((p) => p['side'] == 'buy').toList();
      
      // 가격 순 정렬 (매도는 높은 가격이 위로, 매수는 낮은 가격이 아래로 등 UI에 맞게 정렬)
      sellPositions.sort((a, b) => (b['price'] as num).compareTo(a['price'] as num));
      buyPositions.sort((a, b) => (b['price'] as num).compareTo(a['price'] as num));
      isLoading = false;
    });
  }

  Future<void> _cancelOrder(int id) async {
    // 실제 환경에서는 API 호출 후 성공 시 DB 삭제
    await DatabaseHelper.instance.deletePosition(id);
    ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('주문이 취소되었습니다.')));
    _loadPositions();
  }

  Widget _buildPositionTable(String title, List<Map<String, dynamic>> positions, Color headerColor) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Container(
          padding: const EdgeInsets.all(8),
          color: headerColor,
          child: Text("$title (${positions.length}건)", style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
        ),
        if (positions.isEmpty)
          const Padding(
            padding: EdgeInsets.all(16.0),
            child: Text("포지션 없음", textAlign: TextAlign.center),
          )
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
                    onPressed: () => _cancelOrder(pos['id']),
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
    return isLoading
      ? const Center(child: CircularProgressIndicator())
      : SingleChildScrollView(
          padding: const EdgeInsets.all(8.0),
          child: Column(
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  const Text("호가창 현황 (단독 모드)", style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                  IconButton(icon: const Icon(Icons.refresh), onPressed: _loadPositions)
                ],
              ),
              const SizedBox(height: 8),
              Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Expanded(child: _buildPositionTable("🔵 매도 포지션", sellPositions, Colors.blue.shade100)),
                  const SizedBox(width: 8),
                  Expanded(child: _buildPositionTable("🔴 매수 포지션", buyPositions, Colors.pink.shade100)),
                ],
              )
            ],
          ),
        );
  }
}
