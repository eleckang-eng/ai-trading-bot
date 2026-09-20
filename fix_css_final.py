# coding=utf-8
import re

def main():
    with open('app/dashboard.py', 'r', encoding='utf-8') as f:
        c = f.read()

    css_new = """
        /* 모바일 컬럼 무적 방어: 절대 두 줄로 안 풀림 */
        div[data-testid="stHorizontalBlock"] {
            flex-direction: row !important;
            flex-wrap: nowrap !important; /* 아래로 넘어가지 않음 */
        }
        div[data-testid="stHorizontalBlock"] > div {
            width: 50% !important;
            min-width: 50% !important;
            max-width: 50% !important;
            flex: 1 1 50% !important;
            padding: 0 0.2rem !important;
            display: block !important;
        }"""
        
    if "data-testid=\"stHorizontalBlock\"" not in c:
        c = c.replace('<style>', '<style>' + css_new)
        with open('app/dashboard.py', 'w', encoding='utf-8') as f:
            f.write(c)
        print("Injected CSS")
    else:
        print("Already exists")

if __name__ == '__main__':
    main()

