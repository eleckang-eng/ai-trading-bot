import codecs
import re

with codecs.open('d:/aiworkspace/app/dashboard.py', 'r', encoding='utf-8') as f:
    text = f.read()

# 렌더링마다 무조건 실행되는 현재가 조회 로직을 버튼 클릭 시에만 동작하도록(또는 캐싱) 변경
slow_code = '''    current_market_price = 0
    try:
        sym = cfg.get("symbol", "ONDO" if current_exchange == "bithumb" else "042660")
        p_res = requests.get(f"{API_URL}/price?exchange={current_exchange}&symbol={sym}", timeout=2)
        if p_res.status_code == 200:
            current_market_price = p_res.json().get("price", 0)
    except:
        pass'''

fast_code = '''    # 현재가는 수동으로 '현재가 조회' 버튼을 눌렀을 때 저장된 session_state 값을 사용 (매번 API 호출 방지)
    current_market_price = st.session_state.get("manual_price", 0)'''

if slow_code in text:
    text = text.replace(slow_code, fast_code)

# timeout 최적화
text = text.replace('requests.get(f"{API_URL}/status", timeout=10)', 'requests.get(f"{API_URL}/status", timeout=3)')

with codecs.open('d:/aiworkspace/app/dashboard.py', 'w', encoding='utf-8') as f:
    f.write(text)
print('Optimized API calls in dashboard.')
