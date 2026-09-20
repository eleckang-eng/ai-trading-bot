import codecs

with codecs.open('d:/aiworkspace/app/dashboard.py', 'r', encoding='utf-8') as f:
    text = f.read()

old_main = '''# --- 메인 컨트롤 (사이드바에서 메인으로 이동) ---
if True:
    st.header("⚙️ 봇 시스템 및 모드 제어")'''

new_sidebar = '''# --- 사이드바 제어 ---
with st.sidebar:
    st.header("⚙️ 시스템 제어")'''

text = text.replace(old_main, new_sidebar)

with codecs.open('d:/aiworkspace/app/dashboard.py', 'w', encoding='utf-8') as f:
    f.write(text)
print('Sidebar restored.')
