import codecs

with codecs.open('d:/aiworkspace/app/dashboard.py', 'r', encoding='utf-8') as f:
    text = f.read()

# 'with st.sidebar:' 안의 내용들을 밖으로 빼낸다.
old_sidebar_code = '''# --- 사이드바 제어 ---
with st.sidebar:
    st.header("⚙️ 시스템 제어")
'''

new_main_code = '''# --- 메인 컨트롤 (사이드바에서 메인으로 이동) ---
if True:
    st.header("⚙️ 봇 시스템 및 모드 제어")
'''

# 들여쓰기를 한 칸(4 spaces)씩 빼야 하지만, if True: 로 감싸면 안 빼도 된다! 꼼수다.
text = text.replace(old_sidebar_code, new_main_code)

with codecs.open('d:/aiworkspace/app/dashboard.py', 'w', encoding='utf-8') as f:
    f.write(text)
print('Moved sidebar to main display.')
