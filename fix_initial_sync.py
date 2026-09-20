import codecs

with codecs.open('d:/aiworkspace/app/dashboard.py', 'r', encoding='utf-8') as f:
    text = f.read()

bad_logic = '''# 최초 1회 자산 동기화
if status_data and "initial_balance_refreshed" not in st.session_state:
    try:
        requests.post(f"{API_URL}/refresh_balance", timeout=5)
    except:
        pass
    st.session_state.initial_balance_refreshed = True
    st.rerun()'''

if bad_logic in text:
    text = text.replace(bad_logic, "")
    
    # 파일 맨 끝에 붙임
    good_logic = '''
# ---------------------------------------------------------
# 화면 렌더링 후 최초 1회 자산 자동 동기화 (화면을 띄운 뒤 백그라운드 갱신)
if status_data and "initial_balance_refreshed" not in st.session_state:
    st.session_state.initial_balance_refreshed = True
    try:
        requests.post(f"{API_URL}/refresh_balance", timeout=3)
    except:
        pass
    st.rerun()
'''
    text += good_logic

    with codecs.open('d:/aiworkspace/app/dashboard.py', 'w', encoding='utf-8') as f:
        f.write(text)
    print('Initial sync logic moved to the bottom.')
else:
    print('Could not find the target logic to move.')
