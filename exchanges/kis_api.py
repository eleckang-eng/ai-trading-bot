import json
import requests
from .base import BaseExchange

class KISClient(BaseExchange):
    def __init__(self, url_base, app_key, app_secret, cano, acnt_prdt_cd):
        self.url_base = url_base
        self.app_key = app_key
        self.app_secret = app_secret
        self.cano = cano
        self.acnt_prdt_cd = acnt_prdt_cd
        self.access_token = None
        self.token_expiry = 0
        self._auth()

    def _auth(self):
        """
        Access Token 발급 및 캐싱
        단독 모바일 구동 시 서버가 며칠씩 켜져 있을 때 24시간 이후 토큰이 만료되어 401 오류가 발생하는 것을 방지하기 위해,
        안전하게 23시간(82800초) 경과 시 토큰을 자동 재발급받도록 만료 시간(token_expiry)을 함께 관리합니다.
        """
        import os, time
        # URL에 vts가 포함되면 모의투자용 토큰 파일 사용
        prefix = "mock_" if "vts" in self.url_base else "real_"
        token_file = f"kis_token_{prefix}.txt"
        
        # 1. 파일에 유효한 토큰이 있으면 재사용 (유효기간 24시간, 넉넉히 23시간으로 계산)
        if os.path.exists(token_file):
            file_mtime = os.path.getmtime(token_file)
            if time.time() - file_mtime < 82800:
                with open(token_file, "r") as f:
                    self.access_token = f.read().strip()
                    self.token_expiry = file_mtime + 82800
                    return

        # 2. 토큰이 없거나 만료되었으면 새로 발급
        headers = {"content-type": "application/json"}
        body = {
            "grant_type": "client_credentials",
            "appkey": self.app_key,
            "appsecret": self.app_secret,
        }
        url = f"{self.url_base}/oauth2/tokenP"
        res = requests.post(url, headers=headers, data=json.dumps(body), timeout=5)
        if res.status_code == 200:
            self.access_token = res.json().get("access_token")
            # 24시간 토큰이므로 23시간(82800초) 뒤를 만료 시점으로 기록하여 사전 갱신 유도
            self.token_expiry = time.time() + 82800
            # 발급받은 토큰을 파일에 저장
            with open(token_file, "w") as f:
                f.write(self.access_token)
        else:
            raise Exception(f"KIS Auth Failed: {res.text}")

    def _get_headers(self, tr_id: str):
        """
        API 요청 시 공통으로 사용되는 헤더를 반환합니다.
        요청 직전에 현재 시간과 token_expiry를 비교하여, 만료 시점이 지났으면 즉각 _auth()를 재호출합니다.
        이를 통해 며칠 동안 봇을 켜두어도 토큰 만료 에러 없이 무중단으로 동작할 수 있습니다.
        """
        import time
        if not self.access_token or time.time() >= self.token_expiry:
            self._auth()
            
        # 모의투자인 경우 TR_ID의 첫 글자 'T'를 'V'로 변경 (예: TTTC8434R -> VTTC8434R)
        if "vts" in self.url_base and tr_id.startswith("T"):
            tr_id = "V" + tr_id[1:]
            
        return {
            "content-type": "application/json",
            "authorization": f"Bearer {self.access_token}",
            "appkey": self.app_key,
            "appsecret": self.app_secret,
            "tr_id": tr_id,
        }

    def get_balance(self):
        """주식 잔고 조회 (TTTC8434R / VTTC8434R)"""
        path = "/uapi/domestic-stock/v1/trading/inquire-balance"
        url = f"{self.url_base}{path}"
        headers = self._get_headers("TTTC8434R")
        params = {
            "CANO": self.cano,
            "ACNT_PRDT_CD": self.acnt_prdt_cd,
            "AFHR_FLPR_YN": "N",
            "OFL_YN": "",
            "INQR_DVSN": "02",
            "UNPR_DVSN": "01",
            "FUND_STTL_ICLD_YN": "N",
            "FNCG_AMT_AUTO_RDPT_YN": "N",
            "PRCS_DVSN": "01",
            "CTX_AREA_FK100": "",
            "CTX_AREA_NK100": "",
        }
        res = requests.get(url, headers=headers, params=params)
        return res.json()

    def get_current_price(self, symbol: str):
        """현재가 조회. FHKST01010100 TR_ID는 실전/모의투자에 공통으로 사용됩니다."""
        path = "/uapi/domestic-stock/v1/quotations/inquire-price"
        url = f"{self.url_base}{path}"
        headers = self._get_headers("FHKST01010100")
        params = {"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": symbol}
        res = requests.get(url, headers=headers, params=params)
        return res.json()

    def _place_order(self, symbol: str, price: int, quantity: int, is_buy: bool):
        """
        주문 접수 로직.
        초당 요청 횟수 제한(Rate Limit) 등 일시적인 API 서버 거부나 오류 발생 시,
        즉시 실패 처리하지 않고 점진적으로 대기 시간(Incremental Backoff)을 늘려가며 재시도하여 안정성을 극대화합니다.
        """
        import time
        path = "/uapi/domestic-stock/v1/trading/order-cash"
        url = f"{self.url_base}{path}"
        tr_id = "TTTC0802U" if is_buy else "TTTC0801U"
        headers = self._get_headers(tr_id)
        body = {
            "CANO": self.cano,
            "ACNT_PRDT_CD": self.acnt_prdt_cd,
            "PDNO": symbol,
            "ORD_DVSN": "00", # 00: 지정가
            "ORD_QTY": str(quantity),
            "ORD_UNPR": str(price),
        }
        
        max_retries = 5
        base_wait = 1.0
        for attempt in range(max_retries):
            res = requests.post(url, headers=headers, data=json.dumps(body))
            data = res.json()
            
            rt_cd = str(data.get("rt_cd", "0"))
            msg1 = data.get("msg1", "")
            msg_cd = data.get("msg_cd", "")
            
            # KIS Rate Limit에 도달했을 때 점진적 대기(Exponential/Incremental Backoff)를 수행합니다.
            # 서버 과부하를 막고, 일정 시간 뒤 정상적으로 요청이 수락되도록 유도합니다.
            if rt_cd != "0" and ("초과" in msg1 or "건수" in msg1 or "EGW00" in msg_cd):
                wait_time = base_wait + (attempt * 0.8) # 1.0, 1.8, 2.6, 3.4, 4.2초...
                print(f"[Rate Limit] KIS API 제한 도달 ({msg1}). {wait_time:.1f}초 대기 후 재시도... ({attempt+1}/{max_retries})")
                time.sleep(wait_time)
                continue
                
            return data
            
        return res.json()

    def buy_limit(self, symbol: str, price: int, quantity: int):
        return self._place_order(symbol, price, quantity, is_buy=True)

    def sell_limit(self, symbol: str, price: int, quantity: int):
        return self._place_order(symbol, price, quantity, is_buy=False)

    def get_open_orders(self):
        """주식 정정/취소 가능 주문(미체결) 조회 (TTTC8036R / VTTC8036R)"""
        path = "/uapi/domestic-stock/v1/trading/inquire-psbl-rvsecnl"
        url = f"{self.url_base}{path}"
        headers = self._get_headers("TTTC8036R")
        params = {
            "CANO": self.cano,
            "ACNT_PRDT_CD": self.acnt_prdt_cd,
            "CTX_AREA_FK100": "",
            "CTX_AREA_NK100": "",
            "INQR_DVSN_1": "0",  # 0:전체
            "INQR_DVSN_2": "0",  # 0:전체
        }
        res = requests.get(url, headers=headers, params=params)
        return res.json()
        
    def get_daily_orders(self, start_dt: str, end_dt: str):
        """국내주식 일별 주문체결조회 (TTTC8001R / VTTC8001R)"""
        path = "/uapi/domestic-stock/v1/trading/inquire-daily-ccld"
        url = f"{self.url_base}{path}"
        headers = self._get_headers("TTTC8001R")
        params = {
            "CANO": self.cano,
            "ACNT_PRDT_CD": self.acnt_prdt_cd,
            "INQR_STRT_DT": start_dt,
            "INQR_END_DT": end_dt,
            "SLL_BUY_DVSN_CD": "00",  # 00:전체
            "INQR_DVSN": "00",        # 00:역순
            "PDNO": "",
            "CCLD_DVSN": "01",        # 01:체결, 02:미체결
            "ORD_GNO_BRNO": "",
            "ODNO": "",
            "INQR_DVSN_3": "00",
            "INQR_DVSN_1": "",
            "CTX_AREA_FK100": "",
            "CTX_AREA_NK100": "",
        }
        res = requests.get(url, headers=headers, params=params)
        return res.json()

    def cancel_order(self, order_id: str, symbol: str = "042660"):
        """
        주식 주문 취소 (TTTC0803U / VTTC0803U)
        - order_id: 취소할 원주문번호 (ODNO)
        """
        path = "/uapi/domestic-stock/v1/trading/order-rvsecnml"
        url = f"{self.url_base}{path}"
        headers = self._get_headers("TTTC0803U")
        body = {
            "CANO": self.cano,
            "ACNT_PRDT_CD": self.acnt_prdt_cd,
            "KRX_FWDG_ORD_ORGNO": "",
            "ORGN_ODNO": order_id,
            "ORD_DVSN": "00",          # 00: 지정가
            "RVSE_CNCL_DVSN_CD": "02", # 02: 취소 (01: 정정)
            "ORD_QTY": "0",            # 0: 전량 취소
            "ORD_UNPR": "0",
            "QTY_ALL_ORD_YN": "Y",
            "PDNO": symbol
        }
        import json
        res = requests.post(url, headers=headers, data=json.dumps(body))
        print(f"KIS Cancel Response: {res.text}")
        return res.json()
