# coding=utf-8
import re

def build_new_dashboard():
    with open('app/dashboard_backup.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()

    new_lines = []
    
    i = 0
    in_grid_preview = False

    while i < len(lines):
        line = lines[i]
        
        # 1. Setup tabs at the very beginning of the sidebar
        if 'with st.sidebar:' in line:
            new_lines.append('tab_dash, tab_order, tab_settings = st.tabs(["📊 현황 대시보드", "🛒 주문 생성 및 전송", "⚙️ 시스템 설정"])\n\n')
            new_lines.append('with tab_settings:\n')
            i += 1
            continue
            
        # 2. Switch to tab_order for grid params
        if '매매 알고리즘 파라미터 (그리드 설정)' in line:
            new_lines.append('with tab_order:\n')
            new_lines.append(line)
            i += 1
            continue

        # 3. Switch to tab_dash for 4 metrics
        if 'c1, c2, c3, c4 = st.columns(4)' in line:
            new_lines.append('with tab_dash:\n')
            new_lines.append('    ' + line)
            i += 1
            continue
            
        # 4. Switch to tab_order for grid preview
        if 'if st.session_state.get("show_grid_preview", False):' in line:
            new_lines.append('with tab_order:\n')
            new_lines.append('    ' + line)
            in_grid_preview = True
            i += 1
            continue
            
        # 5. Switch to tab_dash for bottom tabs
        if 'tab1, tab2, tab3 = st.tabs' in line:
            in_grid_preview = False
            new_lines.append('with tab_dash:\n')
            i += 1
            continue
            
        if 'with tab1:' in line:
            new_lines.append('    st.markdown("---")\n')
            new_lines.append('    st.subheader("📊 진입 거래망 현황")\n')
            i += 1
            continue
            
        if 'with tab2:' in line:
            new_lines.append('    st.markdown("---")\n')
            new_lines.append('    st.subheader("💸 거래 내역")\n')
            i += 1
            continue
            
        if 'with tab3:' in line:
            new_lines.append('    st.markdown("---")\n')
            new_lines.append('    st.subheader("🤖 시스템 상태")\n')
            i += 1
            continue

        # Handle indentation for metrics and grid preview blocks
        # Wait, the metrics block is from c1..c4 (line 549) to grid preview (line ~570).
        # We need to add 4 spaces for metrics.
        # How do we know we are in metrics? It's between c1..c4 and grid preview.
        # Let's use line numbers for the unindented blocks that need +4 spaces.
        
        # In dashboard_backup.py:
        # 549: c1, c2, c3, c4 = st.columns(4) (Handled above)
        # 550 to 569: Metrics code (needs +4 spaces)
        # 570: if st.session_state.get("show_grid_preview", False): (Handled above)
        # 571 to 853: Grid preview code (needs +4 spaces)
        
        if i >= 550 and i <= 853:
            if line.strip() == '':
                new_lines.append(line)
            else:
                new_lines.append('    ' + line)
            i += 1
            continue
            
        new_lines.append(line)
        i += 1

    with open('app/dashboard.py', 'w', encoding='utf-8') as f:
        f.writelines(new_lines)

if __name__ == '__main__':
    build_new_dashboard()
