# coding=utf-8
with open('app/dashboard_backup.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()
for i, line in enumerate(lines):
    if 'with st.sidebar:' in line: print(f'sidebar_start: {i}')
    if '그리드 주문 확인 및 편집' in line: print(f'grid_preview_start: {i}')
    if 'c1, c2, c3, c4 = st.columns(4)' in line: print(f'metrics_start: {i}')
    if 'tab1, tab2, tab3 = st.tabs' in line: print(f'bottom_tabs_start: {i}')
    if '에이전트 시스템 제어' in line: print(f'system_control_start: {i}')
    if '매매 알고리즘 파라미터' in line: print(f'grid_params_start: {i}')
    if 'def fetch_status():' in line: print(f'functions_start: {i}')
    if 'status_data = fetch_status()' in line: print(f'status_data_start: {i}')
    if 'st.session_state.show_grid_preview = False' in line and 'elif not has_sell and not has_buy' in line: print(f'grid_preview_end: {i}')

