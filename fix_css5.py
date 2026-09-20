# coding=utf-8
import re

def main():
    with open('app/dashboard.py', 'r', encoding='utf-8') as f:
        c = f.read()

    css_old = """
        /* 모바일에서 컬럼 1줄 풀림 강제 방지 (가로 배치 고정 및 50% 폭 유지) */
        [data-testid="stHorizontalBlock"] {
            flex-direction: row !important;
            flex-wrap: wrap !important;
        }
        [data-testid="column"], [data-testid="stColumn"] {
            padding: 0 0.2rem !important;
            gap: 0 !important;
            width: calc(50% - 0.4rem) !important;
            flex: 1 1 calc(50% - 0.4rem) !important;
            min-width: calc(50% - 0.4rem) !important;
        }"""
        
    css_new = """
        /* 모바일에서 컬럼 1줄 풀림 절대 강제 방지 */
        div[data-testid="stHorizontalBlock"] {
            flex-direction: row !important;
            flex-wrap: wrap !important;
            align-items: flex-start !important;
        }
        div[data-testid="stHorizontalBlock"] > div[data-testid="column"],
        div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"] {
            padding: 0 0.2rem !important;
            gap: 0 !important;
            width: calc(50% - 0.4rem) !important;
            flex: 1 1 calc(50% - 0.4rem) !important;
            min-width: calc(50% - 0.4rem) !important;
            max-width: calc(50% - 0.4rem) !important;
            display: block !important;
        }"""
        
    c = c.replace(css_old.strip(), css_new.strip())
    
    with open('app/dashboard.py', 'w', encoding='utf-8') as f:
        f.write(c)

if __name__ == '__main__':
    main()

