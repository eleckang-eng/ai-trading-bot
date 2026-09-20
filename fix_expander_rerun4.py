# coding=utf-8
import re

def main():
    with open('app/dashboard.py', 'r', encoding='utf-8') as f:
        c = f.read()

    # Find where grid_preview is set to True
    pattern = r'(st\.session_state\.show_grid_preview = True\s+st\.session_state\.confirm_batch_order = False\n)'
    
    matches = re.findall(pattern, c)
    print(f"Found {len(matches)} matches")
    
    # We want to replace it with adding st.rerun()
    def replacer(match):
        block = match.group(1)
        # Find the indentation of the last line
        lines = block.split('\n')
        indent = re.match(r'^(\s*)', lines[-2]).group(1)
        return block + indent + "st.rerun()\n"
        
    c = re.sub(pattern, replacer, c)
    
    with open('app/dashboard.py', 'w', encoding='utf-8') as f:
        f.write(c)

if __name__ == '__main__':
    main()

