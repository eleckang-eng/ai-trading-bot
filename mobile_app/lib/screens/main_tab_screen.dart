import 'package:flutter/material.dart';
import '../services/base_api_service.dart';
import 'dashboard_view.dart';
import 'grid_order_view.dart';
import 'history_view.dart';
import 'settings_view.dart';

class MainTabScreen extends StatefulWidget {
  final BaseApiService apiService;
  final String title;

  const MainTabScreen({super.key, required this.apiService, required this.title});

  @override
  State<MainTabScreen> createState() => _MainTabScreenState();
}

class _MainTabScreenState extends State<MainTabScreen> {
  int _selectedIndex = 0;
  
  void _onItemTapped(int index) {
    setState(() {
      _selectedIndex = index;
    });
  }

  @override
  Widget build(BuildContext context) {
    final List<Widget> screens = [
      DashboardView(apiService: widget.apiService),
      GridOrderView(apiService: widget.apiService),
      HistoryView(apiService: widget.apiService),
      SettingsView(apiService: widget.apiService),
    ];

    return Scaffold(
      body: screens[_selectedIndex],
      bottomNavigationBar: BottomNavigationBar(
        type: BottomNavigationBarType.fixed,
        items: const <BottomNavigationBarItem>[
          BottomNavigationBarItem(icon: Icon(Icons.dashboard), label: '📊 현황'),
          BottomNavigationBarItem(icon: Icon(Icons.add_shopping_cart), label: '🛒 주문 생성'),
          BottomNavigationBarItem(icon: Icon(Icons.history), label: '💸 거래 내역'),
          BottomNavigationBarItem(icon: Icon(Icons.settings), label: '⚙️ 설정'),
        ],
        currentIndex: _selectedIndex,
        selectedItemColor: Colors.amber[800],
        onTap: _onItemTapped,
      ),
    );
  }
}
