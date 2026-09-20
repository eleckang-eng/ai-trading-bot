# coding=utf-8
import re

def main():
    with open('app/dashboard.py', 'r', encoding='utf-8') as f:
        c = f.read()

    # The broken part looks like this:
    broken = """            with hd_col2:
                if st.button("✖ 닫기", use_container_width=True):
                    st.session_state.show_grid_preview   = False
                    st.session_state.confirm_batch_order = False
                st.rerun()
            st.rerun()
                    st.rerun()"""
    
    fixed = """            with hd_col2:
                if st.button("✖ 닫기", use_container_width=True):
                    st.session_state.show_grid_preview   = False
                    st.session_state.confirm_batch_order = False
                    st.rerun()"""
    
    c = c.replace(broken, fixed)
    
    with open('app/dashboard.py', 'w', encoding='utf-8') as f:
        f.write(c)

if __name__ == '__main__':
    main()
