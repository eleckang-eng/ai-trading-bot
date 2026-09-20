import 'dart:convert';
import 'package:http/http.dart' as http;

class KisApi {
  final String appKey;
  final String appSecret;
  final String cano;
  final bool isMock;
  final String baseUrl;

  String? _token;
  DateTime? _tokenExpiry; // 24시간 토큰 만료 관리

  KisApi({
    required this.appKey,
    required this.appSecret,
    required this.cano,
    this.isMock = true,
  }) : baseUrl = isMock 
          ? 'https://openapivts.koreainvestment.com:29443'
          : 'https://openapi.koreainvestment.com:9443';

  Future<void> auth() async {
    // 이미 발급받았고 만료까지 1시간(3600초) 이상 남았다면 재발급하지 않음
    if (_token != null && _tokenExpiry != null) {
      if (DateTime.now().isBefore(_tokenExpiry!.subtract(const Duration(hours: 1)))) {
        return;
      }
    }

    final url = Uri.parse('\$baseUrl/oauth2/tokenP');
    final response = await http.post(
      url,
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        "grant_type": "client_credentials",
        "appkey": appKey,
        "appsecret": appSecret
      }),
    );

    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      _token = data['access_token'];
      // 발급받은 시간으로부터 24시간 유효하지만 23시간으로 안전하게 설정
      _tokenExpiry = DateTime.now().add(const Duration(hours: 23));
    } else {
      throw Exception('Failed to get token: \${response.body}');
    }
  }

  Future<Map<String, String>> _buildHeaders(String trId) async {
    await auth(); // API 호출 전 항상 토큰 만료 여부 검사 및 갱신
    if (_token == null) throw Exception('Token is not issued.');
    return {
      "Content-Type": "application/json",
      "authorization": "Bearer \$_token",
      "appkey": appKey,
      "appsecret": appSecret,
      "tr_id": trId,
      "custtype": "P",
    };
  }

  // 잔고 조회
  Future<Map<String, dynamic>> getBalance() async {
    final trId = isMock ? 'VTTC8434R' : 'TTTC8434R';
    final url = Uri.parse('\$baseUrl/uapi/domestic-stock/v1/trading/inquire-balance'
        '?CANO=\$cano&ACNT_PRDT_CD=01&AFHR_FLPR_YN=N&OFL_YN=N&INQR_DVSN=02&UNPR_DVSN=01&FUND_STTL_ICLD_YN=N&FNCG_AMT_AUTO_RDPT_YN=N&PRCS_DVSN=00&CTX_AREA_FK100=&CTX_AREA_NK100=');
    
    final response = await http.get(url, headers: await _buildHeaders(trId));
    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else {
      throw Exception('Failed to get balance: \${response.body}');
    }
  }

  // 지정가 매수/매도 주문
  Future<Map<String, dynamic>> placeOrder({
    required String orderType,
    required String symbol,
    required int price,
    required int qty,
  }) async {
    String trId;
    if (orderType == 'buy') {
      trId = isMock ? 'VTTC0802U' : 'TTTC0802U';
    } else {
      trId = isMock ? 'VTTC0801U' : 'TTTC0801U';
    }

    final url = Uri.parse('\$baseUrl/uapi/domestic-stock/v1/trading/order-cash');
    final response = await http.post(
      url,
      headers: await _buildHeaders(trId),
      body: jsonEncode({
        "CANO": cano,
        "ACNT_PRDT_CD": "01",
        "PDNO": symbol,
        "ORD_DVSN": "00", // 00: 지정가
        "ORD_QTY": qty.toString(),
        "ORD_UNPR": price.toString()
      }),
    );

    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else {
      throw Exception('Order failed: \${response.body}');
    }
  }

  // 미체결 주문 목록 조회
  Future<Map<String, dynamic>> getOpenOrders() async {
    final trId = isMock ? 'VTTC8036R' : 'TTTC8036R';
    final url = Uri.parse('\$baseUrl/uapi/domestic-stock/v1/trading/inquire-psbl-rvsecncl'
        '?CANO=\$cano&ACNT_PRDT_CD=01&CTX_AREA_FK100=&CTX_AREA_NK100=&INQR_DVSN_1=0&INQR_DVSN_2=0');
    final response = await http.get(url, headers: await _buildHeaders(trId));
    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else {
      throw Exception('Failed to get open orders: \${response.body}');
    }
  }

  // 당일 체결 내역 조회
  Future<Map<String, dynamic>> getExecutionHistory() async {
    final trId = isMock ? 'VTTC8001R' : 'TTTC8001R';
    // 오늘 날짜 구하기 YYYYMMDD
    final now = DateTime.now();
    final todayStr = "\${now.year}\${now.month.toString().padLeft(2, '0')}\${now.day.toString().padLeft(2, '0')}";
    final url = Uri.parse('\$baseUrl/uapi/domestic-stock/v1/trading/inquire-daily-ccld'
        '?CANO=\$cano&ACNT_PRDT_CD=01&INQR_STRT_DT=\$todayStr&INQR_END_DT=\$todayStr&SLL_BUY_DVSN_CD=00&INQR_DVSN=00&PDNO=&CCLD_DVSN=01&ORD_GNO_BRNO=&ODNO=&INQR_DVSN_3=00&INQR_DVSN_1=&CTX_AREA_FK100=&CTX_AREA_NK100=');
    final response = await http.get(url, headers: await _buildHeaders(trId));
    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else {
      throw Exception('Failed to get execution history: \${response.body}');
    }
  }
}

