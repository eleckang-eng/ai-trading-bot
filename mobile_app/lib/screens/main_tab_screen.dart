import 'package:flutter/material.dart';
import '../services/base_api_service.dart';
import 'dashboard_view.dart';
import 'grid_order_view.dart';
import 'positions_view.dart';

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
      PositionsView(apiService: widget.apiService),
    ];

    return Scaffold(
      appBar: AppBar(
        title: Text(widget.title),
        backgroundColor: Theme.of(context).colorScheme.inversePrimary,
      ),
      body: screens[_selectedIndex],
      bottomNavigationBar: BottomNavigationBar(
        items: const <BottomNavigationBarItem>[
          BottomNavigationBarItem(icon: Icon(Icons.account_balance), label: '상태/잔고'),
          BottomNavigationBarItem(icon: Icon(Icons.rocket_launch), label: '그리드 주문'),
          BottomNavigationBarItem(icon: Icon(Icons.list_alt), label: '거미줄 현황'),
        ],
        currentIndex: _selectedIndex,
        selectedItemColor: Colors.amber[800],
        onTap: _onItemTapped,
      ),
    );
  }
}
