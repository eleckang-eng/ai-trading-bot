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

  List<Map<String, dynamic>> _previewList = [];

  final TextEditingController _basePriceCtrl = TextEditingController();
  final TextEditingController _tpCtrl = TextEditingController();
  final TextEditingController _giCtrl = TextEditingController();
  final TextEditingController _qtyCtrl = TextEditingController();
  final TextEditingController _scCtrl = TextEditingController();
  final TextEditingController _bcCtrl = TextEditingController();
  
  final TextEditingController _manualPriceCtrl = TextEditingController();
  final TextEditingController _manualQtyCtrl = TextEditingController();

  @override
  void initState() {
    super.initState();
    _fetchConfig();
  }

  Future<void> _fetchConfig() async {
    try {
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
        });
      } else {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('상태 조회 실패: ${data['message']}')));
        }
      }
    } finally {
      if (mounted) {
        setState(() {
          _isLoading = false;
        });
      }
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
        orders.add({'side': 'sell', 'symbol': _symbol, 'price': sPrice, 'quantity': _orderQuantity});
      }
    }
    if (['매수만', '양방향'].contains(_gridDirection)) {
      for (int i = 1; i <= _buyCount; i++) {
        double bPrice = bp - (_gridInterval * i);
        if (bPrice <= 0) break;
        bPrice = _exchange == "kis" ? ((bPrice - 100) / 1000).round() * 1000 + 100 : ((bPrice - 1) / 10).round() * 10 + 1;
        orders.add({'side': 'buy', 'symbol': _symbol, 'price': bPrice, 'quantity': _orderQuantity});
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
        orders.add({'side': 'sell', 'symbol': _symbol, 'price': sPrice, 'quantity': qty});
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
        orders.add({'side': 'buy', 'symbol': _symbol, 'price': bPrice, 'quantity': qty});
      }
    }
    setState(() { _previewList = orders; });
  }

  bool _removeDup = true;

  void _executeBatchOrder() async {
    if (_previewList.isEmpty) return;
    
    List<Map<String, dynamic>> finalOrders = List.from(_previewList);
    if (_removeDup) {
      // Fetch active positions to filter out duplicates by price
      final data = await widget.apiService.getStatus();
      if (data['status'] == 'success') {
        final existing = List<dynamic>.from(data['positions'] ?? []);
        final Set<double> existingPrices = existing.map<double>((e) => (e['price'] ?? e['avg_price'] ?? 0.0).toDouble()).toSet();
        finalOrders.removeWhere((o) => existingPrices.contains((o['price'] as num).toDouble()));
      }
    }
    
    if (finalOrders.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('중복을 제거했더니 전송할 주문이 없습니다.')));
      return;
    }

    if (_cachedPrice > 0) {
      List<String> badBuys = [];
      List<String> badSells = [];
      for (var o in finalOrders) {
        if (o['side'] == 'buy' && o['price'] > _cachedPrice) {
          badBuys.add("${o['price']}원");
        } else if (o['side'] == 'sell' && o['price'] < _cachedPrice) {
          badSells.add("${o['price']}원");
        }
      }

      if (badBuys.isNotEmpty || badSells.isNotEmpty) {
        bool? proceed = await showDialog<bool>(
          context: context,
          builder: (ctx) => AlertDialog(
            title: const Text('🚨 즉시 체결 위험 경고', style: TextStyle(color: Colors.red)),
            content: SingleChildScrollView(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('현재가(${_cachedPrice}원) 대비 불리한 가격이 포함되어 있습니다.\n'),
                  if (badBuys.isNotEmpty) Text('🔴 비싸게 매수: ${badBuys.join(", ")}'),
                  if (badSells.isNotEmpty) Text('🔵 싸게 매도: ${badSells.join(", ")}'),
                  const SizedBox(height: 10),
                  const Text('시장에 즉시 체결될 수 있습니다. 그래도 전송하시겠습니까?'),
                ],
              ),
            ),
            actions: [
              TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('취소')),
              TextButton(onPressed: () => Navigator.pop(ctx, true), style: TextButton.styleFrom(foregroundColor: Colors.red), child: const Text('무시하고 전송')),
            ],
          )
        );
        if (proceed != true) return;
      }
    }

    setState(() { _isSending = true; });
    
    try {
      final res = await widget.apiService.sendBatchOrder(finalOrders);
      setState(() { _isSending = false; });
      
      if (res['status'] == 'success' || res['status'] == 'accepted') {
        if (mounted) {
          await showDialog(
            context: context,
            builder: (ctx) => AlertDialog(
              title: const Text('일괄 주문 접수 완료'),
              content: Text('총 ${finalOrders.length}건 ' + (res['message'] ?? '주문이 전송/접수되었습니다.')),
              actions: [TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('확인'))],
            )
          );
        }
      } else {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('주문 실패: ${res['message']}'), backgroundColor: Colors.red));
      }
    } catch (e) {
      setState(() { _isSending = false; });
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('에러: $e'), backgroundColor: Colors.red));
    }
  }

  Future<void> _saveParams() async {
    final payload = {
      _exchange: {
        "take_profit": _takeProfit,
        "grid_interval": _gridInterval,
        "order_quantity": _orderQuantity,
        "base_price": _basePrice,
        "sell_count": _sellCount,
        "buy_count": _buyCount,
        "grid_direction": _gridDirection,
        "stair_steps": _stairSteps,
        "stair_add_qty": _stairAddQty,
        "stair_direction": _stairDirection,
      }
    };
    final res = await widget.apiService.updateConfig(payload);
    if (res['status'] == 'success') {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('파라미터가 저장되었습니다.'), backgroundColor: Colors.green));
    } else {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('저장 실패: ${res['message']}'), backgroundColor: Colors.red));
    }
  }

  Future<void> _resetParams() async {
    setState(() {
      _gridInterval = 2000;
      _takeProfit = 2000;
      _orderQuantity = 10;
      _basePrice = 0.0;
      _sellCount = 10;
      _buyCount = 10;
      _stairSteps = 3;
      _stairAddQty = 5;

      _tpCtrl.text = '2000';
      _giCtrl.text = '2000';
      _qtyCtrl.text = '10';
      _scCtrl.text = '10';
      _bcCtrl.text = '10';
      _basePriceCtrl.text = '';
    });
    ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('파라미터가 초기화되었습니다. (저장하려면 파라미터 저장 클릭)')));
  }

  Future<void> _sendManualOrder(String side) async {
    double price = double.tryParse(_manualPriceCtrl.text) ?? 0;
    double qty = double.tryParse(_manualQtyCtrl.text) ?? 0;
    
    if (price <= 0 || qty <= 0) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('가격과 수량을 올바르게 입력하세요.')));
      return;
    }
    
    final res = await widget.apiService.sendBatchOrder([
      {'side': side, 'symbol': _symbol, 'price': price, 'quantity': qty}
    ]);
    
    if (res['status'] == 'success' || res['status'] == 'accepted') {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('수동 주문 전송 완료')));
      }
      _manualPriceCtrl.clear();
      _manualQtyCtrl.clear();
    } else {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('주문 실패: ${res['message']}')));
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) return const Center(child: CircularProgressIndicator());

    return Scaffold(
      appBar: AppBar(title: const Text('🎛️ 매매 알고리즘 파라미터')),
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
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceEvenly,
              children: [
                ElevatedButton.icon(
                  onPressed: _saveParams,
                  icon: const Icon(Icons.save),
                  label: const Text("파라미터 저장"),
                ),
                ElevatedButton.icon(
                  onPressed: _resetParams,
                  icon: const Icon(Icons.refresh),
                  label: const Text("초기화"),
                  style: ElevatedButton.styleFrom(backgroundColor: Colors.grey),
                ),
              ],
            ),
            const SizedBox(height: 16),
            DropdownButtonFormField<String>(
              value: _gridDirection,
              decoration: const InputDecoration(labelText: '주문 방향'),
              items: ['양방향', '매수만', '매도만'].map((s) => DropdownMenuItem(value: s, child: Text(s))).toList(),
              onChanged: (val) => setState(() => _gridDirection = val!),
            ),
            const SizedBox(height: 8),

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
            SwitchListTile(
              title: const Text("중복 주문 자동 제거", style: TextStyle(fontWeight: FontWeight.bold)),
              subtitle: const Text("기존 활성 포지션과 동일한 가격의 주문은 일괄 전송 시 제외합니다."),
              value: _removeDup,
              onChanged: (val) => setState(() => _removeDup = val),
            ),
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
              if (_isSending) const LinearProgressIndicator(),
              ElevatedButton(onPressed: _isSending ? null : _executeBatchOrder, style: ElevatedButton.styleFrom(backgroundColor: Colors.redAccent, padding: const EdgeInsets.symmetric(vertical: 16)), child: Text(_isSending ? "🚀 전송 중..." : "🚀 일괄 주문 전송", style: const TextStyle(fontSize: 18, color: Colors.white)))
            ],
            const SizedBox(height: 32),
            const Text("🕹️ 수동 주문 (지정가)", style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16.0),
                child: Column(
                  children: [
                    Row(
                      children: [
                        Expanded(
                          child: TextField(
                            controller: _manualPriceCtrl,
                            keyboardType: TextInputType.number,
                            decoration: const InputDecoration(labelText: '주문 가격', border: OutlineInputBorder()),
                          ),
                        ),
                        const SizedBox(width: 8),
                        Expanded(
                          child: TextField(
                            controller: _manualQtyCtrl,
                            keyboardType: TextInputType.number,
                            decoration: const InputDecoration(labelText: '주문 수량', border: OutlineInputBorder()),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 16),
                    Row(
                      children: [
                        Expanded(
                          child: ElevatedButton(
                            onPressed: () => _sendManualOrder('buy'),
                            style: ElevatedButton.styleFrom(backgroundColor: Colors.redAccent, padding: const EdgeInsets.symmetric(vertical: 16)),
                            child: const Text('지정가 매수', style: TextStyle(fontSize: 18, color: Colors.white)),
                          ),
                        ),
                        const SizedBox(width: 8),
                        Expanded(
                          child: ElevatedButton(
                            onPressed: () => _sendManualOrder('sell'),
                            style: ElevatedButton.styleFrom(backgroundColor: Colors.blueAccent, padding: const EdgeInsets.symmetric(vertical: 16)),
                            child: const Text('지정가 매도', style: TextStyle(fontSize: 18, color: Colors.white)),
                          ),
                        ),
                      ],
                    )
                  ],
                ),
              ),
            ),
            const SizedBox(height: 24),
            ElevatedButton.icon(
              onPressed: () async {
                final res = await widget.apiService.cancelAllOrders();
                if (mounted) {
                  await showDialog(
                    context: context,
                    builder: (ctx) => AlertDialog(
                      title: const Text('주문 취소 결과'),
                      content: Text(res['message'] ?? '취소 완료'),
                      actions: [TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('확인'))],
                    )
                  );
                }
              },
              icon: const Icon(Icons.delete),
              label: const Text("🗑️ 미체결 전체 취소"),
              style: ElevatedButton.styleFrom(
                backgroundColor: Colors.redAccent,
                foregroundColor: Colors.white,
                padding: const EdgeInsets.symmetric(vertical: 16),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
