      debugPrint("--- Mobile Sync Cycle Completed ---");
    } catch (e) {
      debugPrint("Error in Mobile Sync Cycle: \$e");
    }
  }

  Future<void> _placeOrderWithBackoff(String symbol, String side, int targetPrice, int qty) async {
    int maxRetries = 3;
    for (int i = 0; i < maxRetries; i++) {
      try {
        final res = await kisApi.placeOrder(orderType: side, symbol: symbol, price: targetPrice, qty: qty);
        if (res['rt_cd'] == '0') {
          // 성공 시 DB 저장 및 1초 딜레이(다중 체결 방어)
          await db.addOpenOrder(res['output']['KRX_FWDG_ORD_ORGNO'] ?? '', symbol, side, targetPrice, qty);
          await Future.delayed(const Duration(seconds: 1));
          return;
        }
      } catch (e) {
        debugPrint("Order failed. Attempt \${i + 1}");
      }
      // Exponential Backoff (1초, 2초, 4초)
      await Future.delayed(Duration(seconds: 1 << i));
    }
  }
}

