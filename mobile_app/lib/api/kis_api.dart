import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

class KisApi {
  final String appKey;
  final String appSecret;
  final String cano;
  final bool isMock;
  final String baseUrl;

  String? _token;
  DateTime? _tokenExpiry;

  KisApi({
    required this.appKey,
    required this.appSecret,
    required this.cano,
    this.isMock = true,
  }) : baseUrl = isMock 
          ? 'https://openapivts.koreainvestment.com:29443'
          : 'https://openapi.koreainvestment.com:9443';

  /// KIS OAuth2 토큰 발급 및 캐싱
  /// 토큰 만료 1시간 전까지는 캐시된 토큰을 재사용하여 Rate Limit(1분 1회) 방어
  Future<void> auth() async {
    // API 키가 미등록이면 토큰 발급 시도 자체를 하지 않음
    if (appKey.isEmpty || appSecret.isEmpty) return;

    final prefs = await SharedPreferences.getInstance();
    final cacheKey = isMock ? 'kis_token_mock' : 'kis_token_real';
    final expiryKey = isMock ? 'kis_token_expiry_mock' : 'kis_token_expiry_real';

    // SharedPreferences에 캐싱된 토큰이 있으면 메모리로 복원
    if (_token == null) {
      _token = prefs.getString(cacheKey);
      final expStr = prefs.getString(expiryKey);
      if (expStr != null) _tokenExpiry = DateTime.tryParse(expStr);
    }

    // 유효 기간이 1시간 이상 남아있으면 캐시 토큰 사용
    if (_token != null && _tokenExpiry != null) {
      if (DateTime.now().isBefore(_tokenExpiry!.subtract(const Duration(hours: 1)))) {
        return;
      }
    }

    // 신규 토큰 발급
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
      _tokenExpiry = DateTime.now().add(const Duration(hours: 23));
      
      await prefs.setString(cacheKey, _token!);
      await prefs.setString(expiryKey, _tokenExpiry!.toIso8601String());
    } else {
      throw Exception('토큰 발급 실패: ${response.body}');
    }
  }

  /// API 요청용 공통 헤더 생성 (토큰 자동 갱신 포함)
  Future<Map<String, String>> _buildHeaders(String trId) async {
    await auth();
    if (_token == null) throw Exception('토큰이 발급되지 않았습니다.');
    return {
      "Content-Type": "application/json",
      "authorization": "Bearer $_token",
      "appkey": appKey,
      "appsecret": appSecret,
      "tr_id": trId,
      "custtype": "P",
    };
  }

  /// 잔고 조회
  Future<Map<String, dynamic>> getBalance() async {
    final trId = isMock ? 'VTTC8434R' : 'TTTC8434R';
    final url = Uri.parse('$baseUrl/uapi/domestic-stock/v1/trading/inquire-balance'
        '?CANO=$cano&ACNT_PRDT_CD=01&AFHR_FLPR_YN=N&OFL_YN=N&INQR_DVSN=02&UNPR_DVSN=01&FUND_STTL_ICLD_YN=N&FNCG_AMT_AUTO_RDPT_YN=N&PRCS_DVSN=00&CTX_AREA_FK100=&CTX_AREA_NK100=');
    
    final response = await http.get(url, headers: await _buildHeaders(trId));
    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else {
      throw Exception('잔고 조회 실패: ${response.body}');
    }
  }

  /// 지정가 매수/매도 주문
  /// EXG_DVSN_CD: NXT(넥스트레이드 직접 지정)로 프리마켓/정규장 모두 대응
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
      headers: await _buildHeaders(trId),
      body: jsonEncode({
        "CANO": cano,
        "ACNT_PRDT_CD": "01",
        "PDNO": symbol,
        "ORD_DVSN": "00", // 00: 지정가
        "ORD_QTY": qty.toString(),
        "ORD_UNPR": price.toString(),
        // 넥스트레이드(NXT) 전용 시장 코드로 강제 지정
        "EXG_DVSN_CD": "NXT"
      }),
    );

    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else {
      throw Exception('주문 실패: ${response.body}');
    }
  }

  /// 미체결 주문 내역 조회
  Future<Map<String, dynamic>> getOpenOrders() async {
    final trId = isMock ? 'VTTC8036R' : 'TTTC8036R';
    final url = Uri.parse('$baseUrl/uapi/domestic-stock/v1/trading/inquire-psbl-rvsecncl'
        '?CANO=$cano&ACNT_PRDT_CD=01&CTX_AREA_FK100=&CTX_AREA_NK100=&INQR_DVSN_1=0&INQR_DVSN_2=0');
    final response = await http.get(url, headers: await _buildHeaders(trId));
    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else {
      throw Exception('미체결 조회 실패: ${response.body}');
    }
  }

  /// 당일 체결 내역 조회
  Future<Map<String, dynamic>> getExecutionHistory() async {
    final trId = isMock ? 'VTTC8001R' : 'TTTC8001R';
    final now = DateTime.now();
    final todayStr = "${now.year}${now.month.toString().padLeft(2, '0')}${now.day.toString().padLeft(2, '0')}";
    final url = Uri.parse('$baseUrl/uapi/domestic-stock/v1/trading/inquire-daily-ccld'
        '?CANO=$cano&ACNT_PRDT_CD=01&INQR_STRT_DT=$todayStr&INQR_END_DT=$todayStr&SLL_BUY_DVSN_CD=00&INQR_DVSN=00&PDNO=&CCLD_DVSN=01&ORD_GNO_BRNO=&ODNO=&INQR_DVSN_3=00&INQR_DVSN_1=&CTX_AREA_FK100=&CTX_AREA_NK100=');
    final response = await http.get(url, headers: await _buildHeaders(trId));
    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else {
      throw Exception('체결 내역 조회 실패: ${response.body}');
    }
  }

  /// 기간별 실현 손익 조회
  Future<Map<String, dynamic>> getRealizedProfit({
    required String startDate,
    required String endDate,
  }) async {
    final trId = isMock ? 'VTTC8495R' : 'TTTC8495R';
    final url = Uri.parse('$baseUrl/uapi/domestic-stock/v1/trading/inquire-period-trade-profit'
        '?CANO=$cano&ACNT_PRDT_CD=01&INQR_STRT_DT=$startDate&INQR_END_DT=$endDate&SLL_BUY_DVSN_CD=00&INQR_DVSN=00&PDNO=&CTX_AREA_FK100=&CTX_AREA_NK100=');
    final response = await http.get(url, headers: await _buildHeaders(trId));
    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else {
      throw Exception('실현 손익 조회 실패: ${response.body}');
    }
  }

  /// 주식 주문 취소 (TTTC0803U: 실전 / VTTC0803U: 모의)
  Future<Map<String, dynamic>> cancelOrder(String orderId, {String symbol = "042660"}) async {
    final trId = isMock ? 'VTTC0803U' : 'TTTC0803U';
    final url = Uri.parse('$baseUrl/uapi/domestic-stock/v1/trading/order-rvsecncl');
    final body = jsonEncode({
      "CANO": cano,
      "ACNT_PRDT_CD": "01",
      "KRX_FWDG_ORD_ORGNO": "",
      "ORGN_ODNO": orderId,
      "ORD_DVSN": "00",
      "RVSE_CNCL_DVSN_CD": "02",
      "ORD_QTY": "0",
      "ORD_UNPR": "0",
      "QTY_ALL_ORD_YN": "Y",
      "PDNO": symbol
    });

    final response = await http.post(url, headers: await _buildHeaders(trId), body: body);
    if (response.body.trim().isEmpty) {
      return {"rt_cd": "9", "msg_cd": "EMPTY", "msg1": "빈 응답 (HTTP ${response.statusCode})"};
    }
    try {
      return jsonDecode(response.body);
    } catch (e) {
      return {"rt_cd": "9", "msg_cd": "PARSE_ERROR", "msg1": "파싱 에러: ${response.statusCode}"};
    }
  }

  /// 현재가 조회
  Future<int> getCurrentPrice(String symbol) async {
    final trId = 'FHKST01010100'; // 시세 조회는 실전/모의 동일
    final url = Uri.parse('$baseUrl/uapi/domestic-stock/v1/quotations/inquire-price?FID_COND_MRKT_DIV_CODE=J&FID_INPUT_ISCD=$symbol');
    final response = await http.get(url, headers: await _buildHeaders(trId));
    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      return int.tryParse(data['output']?['stck_prpr']?.toString() ?? '0') ?? 0;
    } else {
      throw Exception('현재가 조회 실패: ${response.body}');
    }
  }
}
