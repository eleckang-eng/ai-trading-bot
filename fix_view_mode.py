# coding=utf-8
import re

def main():
    with open('app/dashboard.py', 'r', encoding='utf-8') as f:
        c = f.read()

    # Fix view_mode
    c = re.sub(r'view_mode = st\.radio\("보기 방식",\s*\["📈 차트 뷰", "📊 호가창 정렬", "📋 주문순 정렬"\],\s*horizontal=True\)', 
               'view_mode = st.radio("보기 방식", ["📈 차트 뷰", "📊 호가창 정렬", "📋 주문순 정렬"], label_visibility="collapsed", horizontal=True)', c)
               
    # Check if 잔고 동기화 moved successfully.
    if 'st.button("🔄 잔고 동기화 (전체 포지션 및 예수금 반영)' not in c:
        # try again
        c = re.sub(r'\s*if st\.button\("🔄 잔고 동기화", use_container_width=True\):\s*try: requests\.post\(f"\{API_URL\}/refresh_balance", timeout=15\); st\.rerun\(\)\s*except: st\.error\("동기화 실패"\)\n', '\n', c)
        header = 'st.header("🤖 시스템 제어")\n'
        c = c.replace(header, header + '    if st.button("🔄 잔고 동기화 (전체 포지션 및 예수금 반영)", use_container_width=True):\n        try: requests.post(f"{API_URL}/refresh_balance", timeout=15); st.rerun()\n        except: st.error("동기화 실패")\n')
        
    with open('app/dashboard.py', 'w', encoding='utf-8') as f:
        f.write(c)

if __name__ == '__main__':
    main()

