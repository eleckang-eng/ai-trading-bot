# coding=utf-8

def fix_ux():
    with open('app/dashboard.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()

    new_lines = []
    
    # We will track indices precisely based on our findings
    # params_start = 247
    # sys_start = 383
    # param_save_end = 548 (just before metrics)
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Goal 1: Remove dividers
        if 'st.divider()' in line or 'st.markdown("---")' in line:
            new_lines.append(line.replace('st.divider()', 'pass').replace('st.markdown("---")', 'pass'))
            i += 1
            continue

        # Goal 3: Put grid params inside an expander
        # Grid params start at 247: "# 매매 알고리즘 파라미터"
        # Line 248 is `with tab_order:`
        if i == 248:
            new_lines.append(line)
            # Insert the expander!
            new_lines.append('    with st.expander("⚙️ 그리드 파라미터 설정 (터치하여 열기/닫기)", expanded=not st.session_state.get("show_grid_preview", False)):\n')
            i += 1
            continue
            
        if 249 <= i <= 382:
            # Indent by 4 spaces (to be inside the expander, which is inside tab_order)
            # Wait, previously it was inside tab_order (so it had 0 spaces because tab_order was at 0 spaces? NO! `with tab_order:` was unindented, but its contents were also UNINDENTED! Let's check!)
            # Wait! In `dashboard.py`, `with tab_order:` is at 0 spaces, but ARE ITS CONTENTS INDENTED?
            # Let's check how the script generated them.
            pass # We will do indentation later in this loop block

        # Goal 2: Move system common settings to tab_settings
        if i == 383:
            new_lines.append('with tab_settings:\n')
            # Fall through to process line 383 itself

        # Handle indentation properly
        # Wait, let's check current indentation of line 249.
        # It's at 0 spaces! Because my previous script did not indent lines 212-548! (Because it assumed they were already indented by 4 spaces in the sidebar!)
        # Wait, if they were already indented by 4 spaces in `dashboard_backup.py`, then in `dashboard.py`, they HAVE 4 spaces!
        # Let's check `dashboard.py` line 249 indentation.
        # Ah, in `dashboard_backup.py`, they were in `with st.sidebar:` which is unindented, but the contents were indented by 4 spaces.
        # So in `dashboard.py`, line 249 has 4 spaces!
        
        # If line 249 has 4 spaces, and `with tab_order:` has 0 spaces, then line 249 IS properly indented under `tab_order`!
        # Now, if we insert `    with st.expander...:` (4 spaces), its contents need 8 spaces!
        # So for lines 249 to 382, we just add 4 spaces!
        
        if 249 <= i <= 382:
            if line.strip() != '':
                new_lines.append('    ' + line)
            else:
                new_lines.append(line)
            i += 1
            continue
            
        # For lines 383 to 548, we added `with tab_settings:\n` (0 spaces).
        # These lines ALREADY have 4 spaces, so they naturally fall under `with tab_settings:` perfectly!
        # No indentation change needed for them!
        
        new_lines.append(line)
        i += 1

    with open('app/dashboard.py', 'w', encoding='utf-8') as f:
        f.writelines(new_lines)

if __name__ == '__main__':
    fix_ux()

