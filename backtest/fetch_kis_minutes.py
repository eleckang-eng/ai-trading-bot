import os
import sys
import json
import time
import requests
import pandas as pd
from dotenv import load_dotenv

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
load_dotenv()

URL_BASE = os.getenv("KIS_URL_BASE")
APP_KEY = os.getenv("KIS_APP_KEY")
APP_SECRET = os.getenv("KIS_APP_SECRET")

def get_access_token():
    headers = {"content-type": "application/json"}
    body = {"grant_type": "client_credentials", "appkey": APP_KEY, "appsecret": APP_SECRET}
    res = requests.post(f"{URL_BASE}/oauth2/tokenP", headers=headers, data=json.dumps(body))
    return res.json().get("access_token")

def fetch_minute_data_safe(symbol):
    token = get_access_token()
    url = f"{URL_BASE}/uapi/domestic-stock/v1/quotations/inquire-time-itemchartprice"
    
    headers = {
        "content-type": "application/json",
        "authorization": f"Bearer {token}",
        "appkey": APP_KEY,
        "appsecret": APP_SECRET,
        "tr_id": "FHKST03010200"
    }
    
    all_records = []
    # KIS API 연속 조회를 위한 시간 파라미터 (15:30:00부터 시작)
    last_time = "153000"
    
    print("안전한 연속 호출 백그라운드 수집을 시작합니다...")
    
    # 예시: 최근 30회 호출 (약 900분어치 데이터 수집)
    for i in range(30):
        params = {
            "FID_ETC_CLS_CODE": "",
            "FID_COND_MRKT_DIV_CODE": "J",
            "FID_INPUT_ISCD": symbol,
            "FID_INPUT_HOUR_1": last_time,
            "FID_PW_DATA_INCU_YN": "Y"
        }
        
        res = requests.get(url, headers=headers, params=params)
        data = res.json()
        
        if data['rt_cd'] != '0':
            break
            
        records = data.get('output2', [])
        if not records:
            break
            
        all_records.extend(records)
        last_time = records[-1]['stck_cntg_hour'] # 마지막 수신 데이터의 시간으로 갱신
        
        # Rate Limit 방어를 위한 안전한 대기 (0.5초)
        time.sleep(0.5)

    df = pd.DataFrame(all_records)
    df = df[['stck_bsop_date', 'stck_cntg_hour', 'stck_prpr', 'stck_oprc', 'stck_hgpr', 'stck_lwpr', 'cntg_vol']]
    df.columns = ['Date', 'Time', 'Close', 'Open', 'High', 'Low', 'Volume']
    
    numeric_cols = ['Close', 'Open', 'High', 'Low', 'Volume']
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')
        
    df = df.dropna().drop_duplicates(subset=['Date', 'Time']).sort_values(by=['Date', 'Time']).reset_index(drop=True)
    
    filename = f"{symbol}_minute_data_full.csv"
    csv_path = os.path.join(os.path.dirname(__file__), filename)
    df.to_csv(csv_path, index=False, encoding='utf-8-sig')
    print(f"안전 대량 수집 완료: {csv_path} (총 {len(df)}건)")

if __name__ == "__main__":
    fetch_minute_data_safe("042660")
