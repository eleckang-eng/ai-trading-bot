import codecs

with codecs.open('d:/aiworkspace/app/dashboard.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 1. 탭 콘텐츠 시작점 찾기
tab_start = -1
for i, line in enumerate(lines):
    if 'tab1, tab2, tab3 = st.tabs([' in line:
        tab_start = i
        break

# 2. 파라미터 설정 시작점 찾기
param_start = -1
for i, line in enumerate(lines):
    if 'st.subheader("🎛️ 매매 알고리즘 파라미터 (그리드 설정)")' in line:
        param_start = i
        break

if tab_start != -1 and param_start != -1:
    # 파라미터 영역은 param_start 부터 파일 끝까지
    # 파라미터 영역 앞에 있는 st.divider() 도 같이 가져오자
    actual_param_start = param_start - 2 if 'st.divider()' in lines[param_start-2] else param_start - 1
    
    # 탭 콘텐츠 영역은 tab_start 부터 actual_param_start 전까지
    
    top_part = lines[:tab_start]
    tab_part = lines[tab_start:actual_param_start]
    param_part = lines[actual_param_start:]
    
    # 새로운 순서: 상단 -> 파라미터 -> 탭
    new_lines = top_part + param_part + ['\n', 'st.divider()\n', '\n'] + tab_part
    
    with codecs.open('d:/aiworkspace/app/dashboard.py', 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    print('Reordered dashboard successfully.')
else:
    print('Could not find sections.')
