# coding=utf-8

def main():
    with open('app/dashboard.py', 'r', encoding='utf-8') as f:
        c = f.read()

    # 1. 탭 선언 부분 찾기
    tab_order_idx = c.find('        # 2. 매도 간격 / 매도주문 개수 (입력창 가로 2개)')
    end_idx = c.find('st.session_state.confirm_batch_order = False', tab_order_idx)
    
    if tab_order_idx != -1 and end_idx != -1:
        # st.session_state.confirm_batch_order = False가 두 번 나옴 (하나는 균등, 하나는 계단식)
        # 계단식 뒤에 나오는 두 번째 것을 찾기
        first_end_idx = c.find('st.session_state.confirm_batch_order = False', tab_order_idx) + 40
        second_end_idx = c.find('st.session_state.confirm_batch_order = False', first_end_idx)
        if second_end_idx != -1:
            second_end_idx = c.find('\n', second_end_idx) + 1
            
            original_block = c[tab_order_idx:second_end_idx]
            
            # Indent original block by 4 spaces
            indented_lines = []
            for line in original_block.split('\n'):
                if line.strip() == '':
                    indented_lines.append('')
                else:
                    indented_lines.append('    ' + line)
            
            indented_block = '\n'.join(indented_lines)
            
            # Add expander header
            expander_header = '        with st.expander("⚙️ 그리드 파라미터 설정 (펼치기/접기)", expanded=not st.session_state.get("show_grid_preview", False)):\n'
            
            new_block = expander_header + indented_block
            
            c = c.replace(original_block, new_block)
            
            with open('app/dashboard.py', 'w', encoding='utf-8') as f:
                f.write(c)
            print("Successfully wrapped in expander.")
        else:
            print("Second end not found.")
    else:
        print("Start or end not found.")

if __name__ == '__main__':
    main()

