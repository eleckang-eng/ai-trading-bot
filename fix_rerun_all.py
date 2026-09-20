# coding=utf-8
import re

def main():
    with open('app/dashboard.py', 'r', encoding='utf-8') as f:
        c = f.read()

    # Find where grid_preview is set to True
    pattern = r'(st\.session_state\.show_grid_preview = True\n\s*st\.session_state\.confirm_batch_order = False)\n'
    
    def replacer(match):
        block = match.group(1)
        # Find the indentation of the confirm_batch_order line
        lines = block.split('\n')
        indent = re.match(r'^(\s*)', lines[-1]).group(1)
        return block + '\n' + indent + "st.rerun()\n"
        
    c = re.sub(pattern, replacer, c)
    
    with open('app/dashboard.py', 'w', encoding='utf-8') as f:
        f.write(c)

if __name__ == '__main__':
    main()

