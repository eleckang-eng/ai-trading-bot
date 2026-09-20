# coding=utf-8
import re

def main():
    with open('app/dashboard.py', 'r', encoding='utf-8') as f:
        c = f.read()

    # We need to find the blocks for the two buttons and append st.rerun() if not present.
    # Button 1: 균등 그리드 생성
    btn1_match = re.search(r'(if st\.button\("📊 균등 그리드 생성", use_container_width=True\):.*?st\.session_state\.confirm_batch_order = False\n)', c, re.DOTALL)
    if btn1_match:
        block = btn1_match.group(1)
        if 'st.rerun()' not in block.split('\n')[-2]: # check if already added
            indent = re.match(r'^(\s*)st\.session_state', block.split('\n')[-2]).group(1)
            new_block = block + indent + 'st.rerun()\n'
            c = c.replace(block, new_block)
            print("Fixed button 1")
            
    # Button 2: 계단식 그리드 생성
    btn2_match = re.search(r'(if st\.button\("📈 계단식 그리드 생성", use_container_width=True\):.*?st\.session_state\.confirm_batch_order = False\n)', c, re.DOTALL)
    if btn2_match:
        block = btn2_match.group(1)
        if 'st.rerun()' not in block.split('\n')[-2]:
            indent = re.match(r'^(\s*)st\.session_state', block.split('\n')[-2]).group(1)
            new_block = block + indent + 'st.rerun()\n'
            c = c.replace(block, new_block)
            print("Fixed button 2")

    with open('app/dashboard.py', 'w', encoding='utf-8') as f:
        f.write(c)

if __name__ == '__main__':
    main()
