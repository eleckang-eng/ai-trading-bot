# coding=utf-8

def main():
    with open('app/dashboard.py', 'r', encoding='utf-8') as f:
        c = f.read()

    bad_str = 'st.session_state.confirm_batch_order = Fa\n    pass'
    good_str = 'st.session_state.confirm_batch_order = False\n                st.rerun()'
    c = c.replace(bad_str, good_str)
    
    with open('app/dashboard.py', 'w', encoding='utf-8') as f:
        f.write(c)

if __name__ == '__main__':
    main()

