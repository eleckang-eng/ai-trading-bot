import codecs
import re

with codecs.open('d:/aiworkspace/app/dashboard.py', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. 파라미터 블록 추출
# st.subheader("🎛️ 매매 알고리즘 파라미터 (그리드 설정)") 부터 
# st.session_state.show_grid_preview = True 다음의 
# with c_btn_save: 블록까지

pattern = re.compile(
    r'(st\.subheader\("🎛️ 매매 알고리즘 파라미터 \(그리드 설정\)"\).*?st\.session_state\.show_grid_preview = True\s*'
    r'with c_btn_save:\n\s*if st\.button\("💾 이 파라미터 봇에 저장", width="stretch"\):\n\s*try:\n.*?except Exception as e:\n\s*st\.error\(f"서버 통신 실패: \{e\}"\))',
    re.DOTALL
)

match = pattern.search(text)
if match:
    param_code = match.group(1)
    
    # 2. 파라미터 블록을 메인에서 삭제
    text = text.replace(param_code, "")
    
    # 3. 파라미터 블록의 들여쓰기를 하나 늘리고 (with st.sidebar: 에 맞추기 위함)
    # 사이드바의 맨 아래(봇 자동 매매 제어 끝나는 부분, 혹은 메인 대시보드 시작 바로 위)에 삽입한다.
    
    indented_param_code = "\n".join(["    " + line if line.strip() else line for line in param_code.split('\n')])
    
    # 사이드바 블록이 끝나는 지점 찾기
    sidebar_end_marker = "# --- 메인 대시보드 ---"
    
    new_sidebar_addition = "    st.divider()\n" + indented_param_code + "\n\n"
    
    text = text.replace(sidebar_end_marker, new_sidebar_addition + sidebar_end_marker)
    
    with codecs.open('d:/aiworkspace/app/dashboard.py', 'w', encoding='utf-8') as f:
        f.write(text)
    print("Moved parameters to sidebar successfully.")
else:
    print("Could not find the parameter block.")
