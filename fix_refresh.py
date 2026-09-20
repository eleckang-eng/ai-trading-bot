# coding=utf-8
import re

def main():
    with open('app/dashboard.py', 'r', encoding='utf-8') as f:
        c = f.read()

    # If the button was deleted, add it back under 'st.header("🤖 시스템 제어")'
    if 'refresh_balance' not in c:
        pattern = r'(st\.header\("🤖 시스템 제어"\)\n)'
        new_btn = r'\1    if st.button("🔄 잔고 동기화 (전체 포지션 및 예수금 반영)", use_container_width=True):\n        try: requests.post(f"{API_URL}/refresh_balance", timeout=15); st.rerun()\n        except: st.error("동기화 실패")\n'
        c = re.sub(pattern, new_btn, c)

    with open('app/dashboard.py', 'w', encoding='utf-8') as f:
        f.write(c)

if __name__ == '__main__':
    main()

