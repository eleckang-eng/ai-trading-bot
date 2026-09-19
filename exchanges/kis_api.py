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
        self._auth()

    def _auth(self):
        """Access Token 발급 및 캐싱"""
        import os, time
        # URL에 vts가 포함되면 모의투자용 토큰 파일 사용
        prefix = "mock_" if "vts" in self.url_base else "real_"
        token_file = f"kis_token_{prefix}.txt"
        
        # 1. 파일에 유효한 토큰이 있으면 재사용 (유효기간 24시간, 넉넉히 23시간으로 계산)
        if os.path.exists(token_file):
            if time.time() - os.path.getmtime(token_file) < 82800:
                with open(token_file, "r") as f:
                    self.access_token = f.read().strip()
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
            # 발급받은 토큰을 파일에 저장
            with open(token_file, "w") as f:
                f.write(self.access_token)
        else:
            raise Exception(f"KIS Auth Failed: {res.text}")

    def _get_headers(self, tr_id: str):
        if not self.access_token:
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
        path = "/uapi/domestic-stock/v1/quotations/inquire-price"
        url = f"{self.url_base}{path}"
        # 가격 조회 TR_ID는 실전/모의 공통
        headers = self._get_headers("FHKST01010100")
        params = {"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": symbol}
        res = requests.get(url, headers=headers, params=params)
        return res.json()

    def _place_order(self, symbol: str, price: int, quantity: int, is_buy: bool):
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
            
            # KIS Rate Limit 점진적 대기(Exponential/Incremental Backoff)
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

    def cancel_order(self, order_id: str):
        # 취소 로직 구현 필요
        pass
