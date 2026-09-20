# coding=utf-8
with open('app/dashboard.py', 'r', encoding='utf-8') as f:
    for i, line in enumerate(f):
        if '매매 알고리즘 파라미터' in line: print(f'params_start: {i}')
        if '시스템 공통 설정' in line: print(f'sys_start: {i}')
        if '파라미터 저장 / 초기화' in line: print(f'param_save: {i}')
        if 'if st.session_state.get("show_grid_preview", False):' in line: print(f'preview: {i}')

