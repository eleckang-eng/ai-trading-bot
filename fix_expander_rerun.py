# coding=utf-8

def main():
    with open('app/dashboard.py', 'r', encoding='utf-8') as f:
        c = f.read()

    # 1. Fix the magic string comments by replacing with hash comments
    start_str = '"""\n============================================================================='
    end_str = '=============================================================================\n"""'
    start_idx = c.find(start_str)
    
    if start_idx != -1:
        end_idx = c.find(end_str, start_idx) + len(end_str)
        doc_block = c[start_idx:end_idx]
        
        # Replace """ with #
        hash_lines = []
        for line in doc_block.split('\n'):
            if line.strip() == '"""':
                continue
            hash_lines.append('# ' + line)
            
        hash_block = '\n'.join(hash_lines) + '\n'
        c = c.replace(doc_block, hash_block)

    # 2. Add st.rerun() to grid buttons
    btn1_target = 'st.session_state.confirm_batch_order = False\n'
    # There are two of these. We will replace both with:
    # st.session_state.confirm_batch_order = False\n                st.rerun()\n
    
    # But wait, one might be indented by 12 spaces, and another by 12 spaces.
    # Let's do a replace, but make sure we only replace inside the tab_order block.
    # Actually, we can just replace 'st.session_state.confirm_batch_order = False\n'
    # with 'st.session_state.confirm_batch_order = False\n                st.rerun()\n'
    # Wait, the exact indentation is:
    #                 st.session_state.confirm_batch_order = False
    # Let's find exactly `            st.session_state.confirm_batch_order = False\n`
    
    old_line1 = '            st.session_state.confirm_batch_order = False\n'
    new_line1 = '            st.session_state.confirm_batch_order = False\n            st.rerun()\n'
    c = c.replace(old_line1, new_line1)
    
    old_line2 = '                st.session_state.confirm_batch_order = False\n'
    new_line2 = '                st.session_state.confirm_batch_order = False\n                st.rerun()\n'
    c = c.replace(old_line2, new_line2)

    with open('app/dashboard.py', 'w', encoding='utf-8') as f:
        f.write(c)

if __name__ == '__main__':
    main()
