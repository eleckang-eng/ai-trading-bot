# coding=utf-8

def main():
    with open('app/dashboard.py', 'r', encoding='utf-8') as f:
        c = f.read()

    tab_order_idx = c.find('        # 2.')
    if tab_order_idx == -1:
        print("Could not find start")
        return
        
    first_end_idx = c.find('st.session_state.confirm_batch_order = False', tab_order_idx)
    second_end_idx = c.find('st.session_state.confirm_batch_order = False', first_end_idx + 10)
    
    if second_end_idx != -1:
        second_end_idx = c.find('\n', second_end_idx) + 1
        
        original_block = c[tab_order_idx:second_end_idx]
        
        indented_lines = []
        for line in original_block.split('\n'):
            if line == '':
                indented_lines.append('')
            else:
                indented_lines.append('    ' + line)
        
        indented_block = '\n'.join(indented_lines)[:-4] # remove last trailing spaces on the empty line
        
        expander_header = '        with st.expander("⚙️ 그리드 파라미터 설정 (펼치기/접기)", expanded=not st.session_state.get("show_grid_preview", False)):\n'
        
        new_block = expander_header + indented_block
        
        c = c.replace(original_block, new_block)
        
        with open('app/dashboard.py', 'w', encoding='utf-8') as f:
            f.write(c)
        print("Successfully wrapped in expander.")
    else:
        print("End not found.")

if __name__ == '__main__':
    main()

