# coding=utf-8

def main():
    with open('app/dashboard.py', 'r', encoding='utf-8') as f:
        c = f.read()

    # Fix view_mode
    c = c.replace('view_mode = st.radio("보기 방식",', 'view_mode = st.radio("보기 방식", label_visibility="collapsed",')
        
    with open('app/dashboard.py', 'w', encoding='utf-8') as f:
        f.write(c)

if __name__ == '__main__':
    main()

