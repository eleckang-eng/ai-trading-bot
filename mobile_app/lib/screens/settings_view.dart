import 'package:flutter/material.dart';
import '../services/base_api_service.dart';
import '../services/secure_settings.dart';

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
  Map<String, dynamic>? _currentStatusData;

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
        _currentStatusData = data;
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

    double fetchedP = 0;
    try {
      fetchedP = await widget.apiService.getPrice(newExchange, newSymbol);
    } catch (e) {
      // 가격 조회가 실패하더라도 모드 변경은 진행되도록 예외 무시
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

    try {
      final postRes = await widget.apiService.updateConfig(payload);

      if (postRes['status'] == 'success') {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('✅ 모드가 변경되었습니다.'), backgroundColor: Colors.green));
        await widget.apiService.refreshBalance();
        await widget.apiService.syncOrders();
        _fetchConfig();
      } else {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('❌ 모드 변경 실패: ${postRes['message']}'), backgroundColor: Colors.red));
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('❌ 모드 변경 에러: $e'), backgroundColor: Colors.red));
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
      double fetchedP = await widget.apiService.getPrice(_currentExchange, newSym);
      if (fetchedP > 0) {
        Map<String, dynamic> payload = {
          "symbol": newSym,
          _currentExchange: {"base_price": fetchedP}
        };
        final postRes = await widget.apiService.updateConfig(payload);
        if (postRes['status'] == 'success') {
          ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('✅ 종목 변경 성공 (현재가: $fetchedP)'), backgroundColor: Colors.green));
          _fetchConfig();
        } else {
          ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('❌ 종목 변경 실패: ${postRes['message']}'), backgroundColor: Colors.red));
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
      final res = await widget.apiService.updateConfig({"auto_sync_interval": val});
      if (res['status'] == 'success') {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('✅ 동기화 간격 변경 성공'), backgroundColor: Colors.green));
        _fetchConfig();
      } else {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('❌ 에러: ${res['message']}'), backgroundColor: Colors.red));
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('❌ 예외 발생: $e'), backgroundColor: Colors.red));
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) return const Scaffold(body: Center(child: CircularProgressIndicator()));
    
    final bool isRunning = _currentStatusData?['running'] ?? false;
    final Map<String, dynamic> config = _currentStatusData?['config'] ?? {};
    final String currExDisp = config['exchange'] ?? 'kis';
    final Map<String, dynamic> exConfig = config[currExDisp] ?? {};
    
    String modeBadge = "알 수 없음";
    if (currExDisp == "kis") {
      if (config['paper_trading'] == true) { modeBadge = "🧪 테스트"; }
      else if (config['mock_mode'] == true) { modeBadge = "🟢 모의 계좌"; }
      else { modeBadge = "🔴 실전"; }
    } else {
      if (config['paper_trading'] == true) { modeBadge = "🧪 테스트"; }
      else { modeBadge = "🔴 실전"; }
    }

    return Scaffold(
      appBar: AppBar(title: const Text('⚙️ 시스템 제어')),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const Text("거래소 / 모드 선택", style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            Row(
              children: [
                Expanded(
                  child: DropdownButtonFormField<String>(
                    value: _selectedMode,
                    items: _modes.map((m) => DropdownMenuItem(value: m, child: Text(m, style: const TextStyle(fontSize: 14)))).toList(),
                    onChanged: (val) => setState(() => _selectedMode = val!),
                  ),
                ),
                const SizedBox(width: 8),
                ElevatedButton(onPressed: _applyMode, child: const Text("적용")),
              ],
            ),
            const Divider(height: 32),
            
            const Text("시스템 공통 설정", style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
            const SizedBox(height: 16),
            const Text("종목 변경 (코드/심볼)", style: TextStyle(fontSize: 14, fontWeight: FontWeight.bold)),
            Row(
              children: [
                Expanded(child: TextField(controller: _symCtrl, decoration: const InputDecoration(hintText: 'ex: 042660 또는 ONDO'))),
                const SizedBox(width: 10),
                ElevatedButton(onPressed: _applySymbol, child: const Text("입력")),
              ],
            ),
            const SizedBox(height: 16),
            const Text("자동동기화 간격 (분)", style: TextStyle(fontSize: 14, fontWeight: FontWeight.bold)),
            Row(
              children: [
                Expanded(child: TextField(controller: _syncCtrl, keyboardType: TextInputType.number)),
                const SizedBox(width: 10),
                ElevatedButton(onPressed: _applySyncInterval, child: const Text("입력")),
              ],
            ),
            const SizedBox(height: 16),
            const Text("한국투자증권 API 키 설정 (단독 모드용)", style: TextStyle(fontSize: 14, fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            ElevatedButton(
              onPressed: () {
                _showApiKeyDialog();
              },
              child: const Text("API 키 입력"),
            ),
            const Divider(height: 32),

            const Text("🤖 시스템 상태", style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            Card(
              color: isRunning ? Colors.green.shade50 : Colors.red.shade50,
              child: Padding(
                padding: const EdgeInsets.all(16.0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      isRunning ? "🟢 시스템 정상 가동 중" : "🔴 시스템 정지됨",
                      style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
                    ),
                    const SizedBox(height: 8),
                    Text("거래소: ${currExDisp.toUpperCase()}"),
                    Text("모드: $modeBadge"),
                    Text("기준가: ${exConfig['base_price'] ?? 0}"),
                    Text("그리드 간격: ${exConfig['grid_interval'] ?? '-'}"),
                    Text("익절 간격: ${exConfig['take_profit'] ?? '-'}"),
                    Text("1회 주문 수량: ${exConfig['order_quantity'] ?? '-'}"),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 16),
            const Text("🤖 봇 자동 매매 제어", style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            if (isRunning)
              const Padding(
                padding: EdgeInsets.only(bottom: 8.0),
                child: Text("🟢 봇 코어 루프가 실행 중입니다.", style: TextStyle(color: Colors.green)),
              )
            else
              const Padding(
                padding: EdgeInsets.only(bottom: 8.0),
                child: Text("🔴 봇 코어 루프가 정지되어 있습니다.", style: TextStyle(color: Colors.red)),
              ),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceEvenly,
              children: [
                ElevatedButton.icon(
                  onPressed: isRunning ? null : () async {
                    await widget.apiService.startBot();
                    if (mounted) ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('봇 코어 루프가 시작되었습니다.')));
                    _fetchConfig();
                  },
                  icon: const Icon(Icons.play_arrow),
                  label: const Text("▶️ 시작"),
                  style: ElevatedButton.styleFrom(backgroundColor: Colors.green, foregroundColor: Colors.white),
                ),
                ElevatedButton.icon(
                  onPressed: !isRunning ? null : () async {
                    await widget.apiService.stopBot();
                    if (mounted) ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('봇 코어 루프가 정지되었습니다.')));
                    _fetchConfig();
                  },
                  icon: const Icon(Icons.stop),
                  label: const Text("⏹️ 정지"),
                  style: ElevatedButton.styleFrom(backgroundColor: Colors.orange, foregroundColor: Colors.white),
                ),
              ],
            ),
            const SizedBox(height: 8),
            ElevatedButton.icon(
              onPressed: () async {
                await widget.apiService.restartBot();
                ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('재시작 명령을 전송했습니다.')));
                _fetchConfig();
              },
              icon: const Icon(Icons.refresh),
              label: const Text("🔄 봇 서버 재시작"),
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _showApiKeyDialog() async {
    final TextEditingController appKeyCtrl = TextEditingController();
    final TextEditingController appSecretCtrl = TextEditingController();
    final TextEditingController canoCtrl = TextEditingController();

    final keys = await SecureSettings.getKisKeys();
    appKeyCtrl.text = keys['appKey'] ?? '';
    appSecretCtrl.text = keys['appSecret'] ?? '';
    canoCtrl.text = keys['cano'] ?? '';

    if (!mounted) return;

    await showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('API 키 설정'),
        content: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextField(controller: appKeyCtrl, decoration: const InputDecoration(labelText: 'App Key')),
              TextField(controller: appSecretCtrl, decoration: const InputDecoration(labelText: 'App Secret')),
              TextField(controller: canoCtrl, decoration: const InputDecoration(labelText: '계좌번호 (CANO)')),
            ],
          ),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('취소')),
          TextButton(
            onPressed: () async {
              await SecureSettings.saveKisKeys(appKeyCtrl.text, appSecretCtrl.text, canoCtrl.text);
              if (mounted) Navigator.pop(ctx);
              if (mounted) ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('API 키 저장 완료. 앱을 재시작해 주세요.')));
            },
            child: const Text('저장'),
          ),
        ],
      )
    );
  }
}

