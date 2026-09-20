import 'package:flutter/material.dart';
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
                  ? Text("조회 실패: ${errMsg}", style: const TextStyle(color: Colors.redAccent))
                  : Text("예수금: ${balance} 원", style: const TextStyle(fontSize: 24, fontWeight: FontWeight.bold)),
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
