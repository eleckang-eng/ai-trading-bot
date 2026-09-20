import 'package:flutter/material.dart';
import '../services/base_api_service.dart';

class GridOrderView extends StatefulWidget {
  final BaseApiService apiService;
  const GridOrderView({super.key, required this.apiService});

  @override
  State<GridOrderView> createState() => _GridOrderViewState();
}

class _GridOrderViewState extends State<GridOrderView> {
  String _exchange = "kis";
  double _basePrice = 0.0;
  double _cachedPrice = 0.0;
  double _gridInterval = 2000;
  double _takeProfit = 2000;
  double _orderQuantity = 10;
  String _symbol = "042660";

  String _gridDirection = '양방향';
  int _sellCount = 10;
  int _buyCount = 10;

  int _stairSteps = 3;
  double _stairAddQty = 5;
  String _stairDirection = '매수매도계단';

  bool _isLoading = true;
  bool _isSending = false;
  double _progress = 0.0;

  List<Map<String, dynamic>> _previewList = [];

  final TextEditingController _basePriceCtrl = TextEditingController();
  final TextEditingController _tpCtrl = TextEditingController();
  final TextEditingController _giCtrl = TextEditingController();
  final TextEditingController _qtyCtrl = TextEditingController();
  final TextEditingController _scCtrl = TextEditingController();
  final TextEditingController _bcCtrl = TextEditingController();

  @override
  void initState() {
    super.initState();
    _fetchConfig();
  }

  Future<void> _fetchConfig() async {
    final data = await widget.apiService.getStatus();
    if (data['status'] == 'success') {
      final conf = data['config'] ?? {};
      setState(() {
        _exchange = conf['exchange'] ?? "kis";
        _symbol = conf['symbol'] ?? "042660";
        final exCfg = conf[_exchange] ?? {};
        _gridInterval = (exCfg['grid_interval'] ?? 2000).toDouble();
        _takeProfit = (exCfg['take_profit'] ?? 2000).toDouble();
        _orderQuantity = (exCfg['order_quantity'] ?? 10).toDouble();
        _basePrice = (exCfg['base_price'] ?? 0).toDouble();
        _stairAddQty = _exchange == "kis" ? 5 : 500;
        
        _tpCtrl.text = _takeProfit.toStringAsFixed(0);
        _giCtrl.text = _gridInterval.toStringAsFixed(0);
        _qtyCtrl.text = _orderQuantity.toStringAsFixed(0);
        _scCtrl.text = _sellCount.toString();
        _bcCtrl.text = _buyCount.toString();
        if (_basePrice > 0) _basePriceCtrl.text = _basePrice.toStringAsFixed(0);
        
        _isLoading = false;
      });
    }
  }

  Future<void> _fetchCurrentPrice() async {
    try {
      final price = await widget.apiService.getPrice(_exchange, _symbol);
      if (price > 0) {
        setState(() {
          _cachedPrice = price;
          ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('현재가 조회 성공: $_cachedPrice원')));
        });
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('현재가 조회 실패: $e')));
    }
  }

  double _calcBasePrice() {
    if (_basePrice > 0) return _basePrice;
    if (_cachedPrice > 0) return _cachedPrice;
    return _exchange == "kis" ? 80000 : 1000;
  }

  void _generateUniformGrid() {
    FocusScope.of(context).unfocus();
    double bp = _calcBasePrice();
    List<Map<String, dynamic>> orders = [];

    if (['매도만', '양방향'].contains(_gridDirection)) {
      for (int i = 1; i <= _sellCount; i++) {
        double sPrice = bp + (_takeProfit * i);
        sPrice = _exchange == "kis" ? ((sPrice - 900) / 1000).round() * 1000 + 900 : ((sPrice - 9) / 10).round() * 10 + 9;
        orders.add({'side': 'sell', 'price': sPrice, 'quantity': _orderQuantity});
      }
    }
    if (['매수만', '양방향'].contains(_gridDirection)) {
      for (int i = 1; i <= _buyCount; i++) {
        double bPrice = bp - (_gridInterval * i);
        if (bPrice <= 0) break;
        bPrice = _exchange == "kis" ? ((bPrice - 100) / 1000).round() * 1000 + 100 : ((bPrice - 1) / 10).round() * 10 + 1;
        orders.add({'side': 'buy', 'price': bPrice, 'quantity': _orderQuantity});
      }
    }
    setState(() { _previewList = orders; });
  }

  void _generateStairGrid() {
    FocusScope.of(context).unfocus();
    double bp = _calcBasePrice();
    List<Map<String, dynamic>> orders = [];

    if (['매도만', '양방향'].contains(_gridDirection)) {
      for (int i = 1; i <= _sellCount; i++) {
        double sPrice = bp + (_takeProfit * i);
        sPrice = _exchange == "kis" ? ((sPrice - 900) / 1000).round() * 1000 + 900 : ((sPrice - 9) / 10).round() * 10 + 9;
        double qty = _orderQuantity;
        if (['매수매도계단', '매도계단'].contains(_stairDirection)) {
          qty += ((i - 1) ~/ _stairSteps) * _stairAddQty;
        }
        orders.add({'side': 'sell', 'price': sPrice, 'quantity': qty});
      }
    }
    if (['매수만', '양방향'].contains(_gridDirection)) {
      for (int i = 1; i <= _buyCount; i++) {
        double bPrice = bp - (_gridInterval * i);
        if (bPrice <= 0) break;
        bPrice = _exchange == "kis" ? ((bPrice - 100) / 1000).round() * 1000 + 100 : ((bPrice - 1) / 10).round() * 10 + 1;
        double qty = _orderQuantity;
        if (['매수매도계단', '매수계단'].contains(_stairDirection)) {
          qty += ((i - 1) ~/ _stairSteps) * _stairAddQty;
        }
        orders.add({'side': 'buy', 'price': bPrice, 'quantity': qty});
      }
    }
    setState(() { _previewList = orders; });
  }

  void _executeBatchOrder() async {
    if (_previewList.isEmpty) return;
    setState(() { _isSending = true; _progress = 0.0; });
    
    int total = _previewList.length;
    int success = 0;
    int fail = 0;

    for (int i = 0; i < total; i++) {
      setState(() => _progress = (i + 1) / total);
      final res = await widget.apiService.sendOrder(
        _previewList[i]['side'], _symbol, _previewList[i]['quantity'], _previewList[i]['price']);
      if (res['status'] == 'success') success++; else fail++;
      await Future.delayed(const Duration(milliseconds: 250));
    }
    setState(() { _isSending = false; });
    
    if (mounted) {
      showDialog(
        context: context,
        builder: (ctx) => AlertDialog(
          title: const Text('일괄 주문 결과'),
          content: Text('총 $total건 중\n✅ 성공: $success건\n❌ 실패: $fail건'),
          actions: [TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('확인'))],
        )
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) return const Center(child: CircularProgressIndicator());

    return Scaffold(
      appBar: AppBar(title: Text('$_exchange 그리드 주문')),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            ElevatedButton.icon(
              onPressed: _fetchCurrentPrice,
              icon: const Icon(Icons.refresh),
              label: Text("서버조회 (현재가: ${_cachedPrice > 0 ? _cachedPrice : '알수없음'})"),
            ),
            const SizedBox(height: 16),
            Row(
              children: [
                Expanded(child: TextField(controller: _tpCtrl, decoration: const InputDecoration(labelText: '매도 간격 (수익폭)'), keyboardType: TextInputType.number, onChanged: (v) => _takeProfit = double.tryParse(v) ?? 2000)),
                const SizedBox(width: 8),
                Expanded(child: TextField(controller: _scCtrl, decoration: const InputDecoration(labelText: '매도주문 개수'), keyboardType: TextInputType.number, onChanged: (v) => _sellCount = int.tryParse(v) ?? 10)),
              ],
            ),
            Row(
              children: [
                Expanded(child: TextField(controller: _basePriceCtrl, decoration: const InputDecoration(labelText: '기준가 (비워두면 현재가)'), keyboardType: TextInputType.number, onChanged: (v) => _basePrice = double.tryParse(v) ?? 0)),
                const SizedBox(width: 8),
                Expanded(child: TextField(controller: _qtyCtrl, decoration: const InputDecoration(labelText: '1회 매수 수량'), keyboardType: TextInputType.number, onChanged: (v) => _orderQuantity = double.tryParse(v) ?? 10)),
              ],
            ),
            Row(
              children: [
                Expanded(child: TextField(controller: _giCtrl, decoration: const InputDecoration(labelText: '매수 간격 (하락폭)'), keyboardType: TextInputType.number, onChanged: (v) => _gridInterval = double.tryParse(v) ?? 2000)),
                const SizedBox(width: 8),
                Expanded(child: TextField(controller: _bcCtrl, decoration: const InputDecoration(labelText: '매수주문 개수'), keyboardType: TextInputType.number, onChanged: (v) => _buyCount = int.tryParse(v) ?? 10)),
              ],
            ),
            const SizedBox(height: 10),
            DropdownButtonFormField<String>(
              value: _gridDirection,
              decoration: const InputDecoration(labelText: '주문 방향'),
              items: ['양방향', '매수만', '매도만'].map((s) => DropdownMenuItem(value: s, child: Text(s))).toList(),
              onChanged: (val) => setState(() => _gridDirection = val!),
            ),
            const SizedBox(height: 16),
            ElevatedButton(onPressed: _generateUniformGrid, child: const Text("📝 균등 그리드 생성")),
            const Divider(height: 32),
            const Text("계단형 설정", style: TextStyle(fontWeight: FontWeight.bold)),
            Row(
              children: [
                Expanded(child: TextField(decoration: InputDecoration(labelText: '증액 단계 수 (기본 $_stairSteps)'), keyboardType: TextInputType.number, onChanged: (v) => _stairSteps = int.tryParse(v) ?? 3)),
                const SizedBox(width: 8),
                Expanded(child: TextField(decoration: InputDecoration(labelText: '증액 수량 (기본 $_stairAddQty)'), keyboardType: TextInputType.number, onChanged: (v) => _stairAddQty = double.tryParse(v) ?? 5)),
              ],
            ),
            DropdownButtonFormField<String>(
              value: _stairDirection,
              decoration: const InputDecoration(labelText: '계단 적용 방향'),
              items: ['매수매도계단', '매수계단', '매도계단'].map((s) => DropdownMenuItem(value: s, child: Text(s))).toList(),
              onChanged: (val) => setState(() => _stairDirection = val!),
            ),
            const SizedBox(height: 10),
            ElevatedButton(onPressed: _generateStairGrid, style: ElevatedButton.styleFrom(backgroundColor: Colors.orange), child: const Text("📈 계단형 그리드 생성", style: TextStyle(color: Colors.white))),
            const Divider(height: 32),
            if (_previewList.isNotEmpty) ...[
              Text("주문 미리보기 (${_previewList.length}건)", style: const TextStyle(fontWeight: FontWeight.bold)),
              Container(
                height: 200, decoration: BoxDecoration(border: Border.all(color: Colors.grey)),
                child: ListView.builder(itemCount: _previewList.length, itemBuilder: (ctx, i) {
                  final o = _previewList[i];
                  return ListTile(dense: true, leading: Icon(o['side'] == 'sell' ? Icons.arrow_upward : Icons.arrow_downward, color: o['side'] == 'sell' ? Colors.blue : Colors.red), title: Text("${o['price']}원"), trailing: Text("${o['quantity']}주/개"));
                }),
              ),
              const SizedBox(height: 16),
              if (_isSending) LinearProgressIndicator(value: _progress),
              ElevatedButton(onPressed: _isSending ? null : _executeBatchOrder, style: ElevatedButton.styleFrom(backgroundColor: Colors.redAccent, padding: const EdgeInsets.symmetric(vertical: 16)), child: Text(_isSending ? "🚀 전송 중..." : "🚀 일괄 주문 전송", style: const TextStyle(fontSize: 18, color: Colors.white)))
            ]
          ],
        ),
      ),
    );
  }
}
