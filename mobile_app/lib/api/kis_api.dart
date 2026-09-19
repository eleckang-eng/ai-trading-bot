import 'dart:convert';
import 'package:http/http.dart' as http;

class KisApi {
  final String appKey;
  final String appSecret;
  final String cano;
  final bool isMock;
  final String baseUrl;

  String? _token;

  KisApi({
    required this.appKey,
    required this.appSecret,
    required this.cano,
    this.isMock = true,
  }) : baseUrl = isMock 
          ? 'https://openapivts.koreainvestment.com:29443'
          : 'https://openapi.koreainvestment.com:9443';

  Future<void> auth() async {
    final url = Uri.parse('$baseUrl/oauth2/tokenP');
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
    } else {
      throw Exception('Failed to get token: ${response.body}');
    }
  }

  Map<String, String> _buildHeaders(String trId) {
    if (_token == null) throw Exception('Token is not issued. Call auth() first.');
    return {
      "Content-Type": "application/json",
      "authorization": "Bearer $_token",
      "appkey": appKey,
      "appsecret": appSecret,
      "tr_id": trId,
      "custtype": "P",
    };
  }

  // 잔고 조회
  Future<Map<String, dynamic>> getBalance() async {
    final trId = isMock ? 'VTTC8434R' : 'TTTC8434R';
    final url = Uri.parse('$baseUrl/uapi/domestic-stock/v1/trading/inquire-balance'
        '?CANO=$cano&ACNT_PRDT_CD=01&AFHR_FLPR_YN=N&OFL_YN=N&INQR_DVSN=02&UNPR_DVSN=01&FUND_STTL_ICLD_YN=N&FNCG_AMT_AUTO_RDPT_YN=N&PRCS_DVSN=00&CTX_AREA_FK100=&CTX_AREA_NK100=');
    
    final response = await http.get(url, headers: _buildHeaders(trId));
    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else {
      throw Exception('Failed to get balance: ${response.body}');
    }
  }

  // 지정가 매수/매도 주문
  // orderType: "buy" or "sell"
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

    final url = Uri.parse('$baseUrl/uapi/domestic-stock/v1/trading/order-cash');
    final response = await http.post(
      url,
      headers: _buildHeaders(trId),
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
      throw Exception('Order failed: ${response.body}');
    }
  }
}

