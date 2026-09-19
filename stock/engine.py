import json
import os
import requests
import sys
import io
from dotenv import load_dotenv

# 윈도우 터미널 한글 깨짐 방지
sys.stdout = io.TextIOWrapper(sys.stdout.detach(), encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.detach(), encoding='utf-8')

load_dotenv()

URL_BASE = os.getenv("KIS_URL_BASE", "https://openapi.koreainvestment.com:9443")
APP_KEY = os.getenv("KIS_APP_KEY")
APP_SECRET = os.getenv("KIS_APP_SECRET")

# 실전 계좌 정보 설정 (.env에서 불러오기)
CANO = os.getenv("KIS_CANO", "")
ACNT_PRDT_CD = os.getenv("KIS_ACNT_PRDT_CD", "01")

def get_access_token():
  print("1. Access Token 발급 함수 진입...")
  headers = {"content-type": "application/json"}
  body = {
      "grant_type": "client_credentials",
      "appkey": APP_KEY,
      "appsecret": APP_SECRET,
  }
  url = f"{URL_BASE}/oauth2/tokenP"
  print("2. KIS 서버로 토큰 요청 전송 중...")

  try:
    res = requests.post(url, headers=headers, data=json.dumps(body), timeout=5)
    print(f"3. 서버 응답 수신 완료 (상태 코드: {res.status_code})")

    if res.status_code == 200:
      token = res.json().get("access_token")
      print("4. Access Token 획득 성공!")
      return token
    else:
      print("토큰 발급 실패 응답:", res.text)
      return None
  except Exception as e:
    print("토큰 요청 중 에러 발생:", e)
    return None


def get_stock_balance(access_token):
  print("5. 잔고 조회 함수 진입...")
  path = "/uapi/domestic-stock/v1/trading/inquire-balance"
  url = f"{URL_BASE}{path}"

  headers = {
      "content-type": "application/json",
      "authorization": f"Bearer {access_token}",
      "appkey": APP_KEY,
      "appsecret": APP_SECRET,
      "tr_id": "TTTC8434R",  # 실전투자 주식잔고조회 TR ID
  }

  params = {
      "CANO": CANO,
      "ACNT_PRDT_CD": ACNT_PRDT_CD,
      "AFHR_FLG": "N",
      "OFL_YN": "",
      "INQR_DVSN": "02",
      "UNPR_DVSN": "01",
      "FUND_STTL_ICLD_YN": "N",
      "FNCG_AMT_AUTO_RDPT_YN": "N",
      "PRC_DVSN": "01",
      "CTX_AREA_FK100": "",
      "CTX_AREA_NK100": "",
  }

  print("6. 잔고 조회 요청 전송 중...")
  res = requests.get(url, headers=headers, params=params)
  print(f"7. 잔고 응답 수신 완료 (상태 코드: {res.status_code})")

  if res.status_code == 200:
    print("잔고 조회 성공:")
    print(json.dumps(res.json(), indent=2, ensure_ascii=False))
    return res.json()
  else:
    print("잔고 조회 실패:", res.text)
    return None


if __name__ == "__main__":
  print("한국투자증권 API 연동 테스트 시작...")
  token = get_access_token()
  if token:
    get_stock_balance(token)
  else:
    print("토큰이 없어 잔고 조회를 건너뜁니다.")