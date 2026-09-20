import codecs
import re

with codecs.open('d:/aiworkspace/app/dashboard.py', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. 맨 위 "최초 1회 자산 동기화" 블록 완전 삭제
sync_block = '''# 최초 1회 자산 동기화
if status_data and "initial_balance_refreshed" not in st.session_state:
    try:
        requests.post(f"{API_URL}/refresh_balance", timeout=5)
    except:
        pass
    st.session_state.initial_balance_refreshed = True
    st.rerun()'''

text = text.replace(sync_block, "")


# 2. 파라미터 쪽 "현재가 무조건 조회" 로직 완전 삭제 및 교체
price_block = '''    current_market_price = 0
    try:
        sym = cfg.get("symbol", "ONDO" if current_exchange == "bithumb" else "042660")
        p_res = requests.get(f"{API_URL}/price?exchange={current_exchange}&symbol={sym}", timeout=2)
        if p_res.status_code == 200:
            current_market_price = p_res.json().get("price", 0)
    except:
        pass'''

fast_price = '''    current_market_price = st.session_state.get("manual_price", 0)'''
text = text.replace(price_block, fast_price)


# 3. fetch_status timeout 축소
text = text.replace('requests.get(f"{API_URL}/status", timeout=10)', 'requests.get(f"{API_URL}/status", timeout=3)')


with codecs.open('d:/aiworkspace/app/dashboard.py', 'w', encoding='utf-8') as f:
    f.write(text)
print('All blocking requests removed successfully!')
