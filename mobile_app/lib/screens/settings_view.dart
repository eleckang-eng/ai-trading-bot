import 'package:flutter/material.dart';
import '../services/base_api_service.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';

class SettingsView extends StatefulWidget {
  final BaseApiService apiService;
  const SettingsView({super.key, required this.apiService});

  @override
  State<SettingsView> createState() => _SettingsViewState();
}

class _SettingsViewState extends State<SettingsView> {
  String _currentExchange = "kis";
  bool _mockMode = true;
  bool _paperTrading = false;
  String _symbol = "042660";
  int _autoSyncInterval = 1;
  bool _isLoading = true;

  final TextEditingController _symCtrl = TextEditingController();
  final TextEditingController _syncCtrl = TextEditingController();

  final List<String> _modes = [
    "🔴 한국투자증권 (실전)",
    "🔴 빗썸 (실전)",
    "🟢 한국투자증권 (모의 계좌)",
    "🧪 한국투자증권 (테스트)",
    "🧪 빗썸 (테스트)"
  ];
  String _selectedMode = "🟢 한국투자증권 (모의 계좌)";

  @override
  void initState() {
    super.initState();
    _fetchConfig();
  }

  Future<void> _fetchConfig() async {
    setState(() => _isLoading = true);
    final data = await widget.apiService.getStatus();
    if (data['status'] == 'success') {
      final conf = data['config'] ?? {};
      setState(() {
        _currentExchange = conf['exchange'] ?? "kis";
        _mockMode = conf['mock_mode'] ?? true;
        _paperTrading = conf['paper_trading'] ?? false;
        _symbol = conf['symbol'] ?? "042660";
        _autoSyncInterval = conf['auto_sync_interval'] ?? 1;

        _symCtrl.text = _symbol;
        _syncCtrl.text = _autoSyncInterval.toString();

        if (_paperTrading) {
          _selectedMode = _currentExchange == "kis" ? "🧪 한국투자증권 (테스트)" : "🧪 빗썸 (테스트)";
        } else if (_mockMode) {
          _selectedMode = "🟢 한국투자증권 (모의 계좌)";
        } else {
          _selectedMode = _currentExchange == "kis" ? "🔴 한국투자증권 (실전)" : "🔴 빗썸 (실전)";
        }
        _isLoading = false;
      });
    } else {
      setState(() => _isLoading = false);
    }
  }

  Future<void> _applyMode() async {
    final bool? confirm = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('모드 변경'),
        content: Text('$_selectedMode(으)로 변경하시겠습니까?'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('취소')),
          TextButton(onPressed: () => Navigator.pop(ctx, true), child: const Text('적용')),
        ],
      )
    );
    if (confirm != true) return;

    String newExchange = _selectedMode.contains("빗썸") ? "bithumb" : "kis";
    bool isMock = _selectedMode.contains("모의 계좌");
    bool isPaper = _selectedMode.contains("테스트");
    String newSymbol = newExchange == "bithumb" ? "ONDO" : "042660";

    try {
      final res = await http.get(Uri.parse('http://127.0.0.1:8000/price?exchange=$newExchange&symbol=$newSymbol'));
      double fetchedP = 0;
      if (res.statusCode == 200) {
        final d = json.decode(res.body);
        fetchedP = (d['price'] ?? 0).toDouble();
      }

      Map<String, dynamic> payload = {
        "exchange": newExchange,
        "symbol": newSymbol,
        "mock_mode": isMock,
        "paper_trading": isPaper,
      };
      if (fetchedP > 0) {
        payload[newExchange] = {"base_price": fetchedP};
      }

      final postRes = await http.post(
        Uri.parse('http://127.0.0.1:8000/config'),
        headers: {'Content-Type': 'application/json'},
        body: json.encode(payload)
      );

      if (postRes.statusCode == 200) {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('✅ 모드가 변경되었습니다.'), backgroundColor: Colors.green));
        await http.post(Uri.parse('http://127.0.0.1:8000/refresh_balance'));
        await http.post(Uri.parse('http://127.0.0.1:8000/order/sync'));
        _fetchConfig();
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('❌ 모드 변경 실패: $e'), backgroundColor: Colors.red));
    }
  }

  Future<void> _applySymbol() async {
    final newSym = _symCtrl.text.trim();
    if (newSym.isEmpty) return;

    final bool? confirm = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('종목 변경'),
        content: Text('종목을 $newSym(으)로 변경하시겠습니까?'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('취소')),
          TextButton(onPressed: () => Navigator.pop(ctx, true), child: const Text('적용')),
        ],
      )
    );
    if (confirm != true) return;

    try {
      final res = await http.get(Uri.parse('http://127.0.0.1:8000/price?exchange=$_currentExchange&symbol=$newSym'));
      double fetchedP = 0;
      if (res.statusCode == 200) {
        final d = json.decode(res.body);
        fetchedP = (d['price'] ?? 0).toDouble();
      }

      if (fetchedP > 0) {
        Map<String, dynamic> payload = {
          "symbol": newSym,
          _currentExchange: {"base_price": fetchedP}
        };
        final postRes = await http.post(
          Uri.parse('http://127.0.0.1:8000/config'),
          headers: {'Content-Type': 'application/json'},
          body: json.encode(payload)
        );
        if (postRes.statusCode == 200) {
          ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('✅ 종목 변경 성공 (현재가: $fetchedP)'), backgroundColor: Colors.green));
          _fetchConfig();
        }
      } else {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('❌ 잘못된 종목이거나 가격을 조회할 수 없습니다.'), backgroundColor: Colors.red));
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('❌ 종목 변경 에러: $e'), backgroundColor: Colors.red));
    }
  }

  Future<void> _applySyncInterval() async {
    final int val = int.tryParse(_syncCtrl.text) ?? 1;
    final bool? confirm = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('자동동기화 설정'),
        content: Text('동기화 간격을 $val분으로 변경하시겠습니까?'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('취소')),
          TextButton(onPressed: () => Navigator.pop(ctx, true), child: const Text('적용')),
        ],
      )
    );
    if (confirm != true) return;

    try {
      final res = await http.post(
        Uri.parse('http://127.0.0.1:8000/config'),
        headers: {'Content-Type': 'application/json'},
        body: json.encode({"auto_sync_interval": val})
      );
      if (res.statusCode == 200) {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('✅ 동기화 간격 변경 성공'), backgroundColor: Colors.green));
        _fetchConfig();
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('❌ 에러: $e'), backgroundColor: Colors.red));
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) return const Scaffold(body: Center(child: CircularProgressIndicator()));

    return Scaffold(
      appBar: AppBar(title: const Text('시스템 공통 설정')),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const Text("거래소 및 투자 모드", style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            DropdownButtonFormField<String>(
              value: _selectedMode,
              items: _modes.map((s) => DropdownMenuItem(value: s, child: Text(s))).toList(),
              onChanged: (val) => setState(() => _selectedMode = val!),
            ),
            const SizedBox(height: 16),
            ElevatedButton(
              onPressed: _applyMode,
              style: ElevatedButton.styleFrom(backgroundColor: Colors.blueAccent, padding: const EdgeInsets.symmetric(vertical: 16)),
              child: const Text("🔄 모드 적용", style: TextStyle(color: Colors.white, fontSize: 16)),
            ),
            const Divider(height: 40),
            
            const Text("종목 변경 (코드/심볼)", style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
            Row(
              children: [
                Expanded(child: TextField(controller: _symCtrl, decoration: const InputDecoration(hintText: 'ex: 042660 또는 ONDO'))),
                const SizedBox(width: 10),
                ElevatedButton(onPressed: _applySymbol, child: const Text("입력")),
              ],
            ),
            const Divider(height: 40),

            const Text("자동동기화 간격 (분)", style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
            Row(
              children: [
                Expanded(child: TextField(controller: _syncCtrl, keyboardType: TextInputType.number)),
                const SizedBox(width: 10),
                ElevatedButton(onPressed: _applySyncInterval, child: const Text("입력")),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
