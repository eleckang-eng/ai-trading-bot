# coding=utf-8
import re

def main():
    with open('app/dashboard.py', 'r', encoding='utf-8') as f:
        c = f.read()

    css_inject = """
        /* 모바일에서 컬럼 1줄 풀림 방지 (무조건 50% 폭 유지하여 2열 배치) */
        [data-testid="stHorizontalBlock"] {
            flex-wrap: wrap !important;
        }
        [data-testid="column"] {
            padding: 0 0.2rem !important;
            gap: 0 !important;
            width: calc(50% - 0.4rem) !important;
            flex: 1 1 calc(50% - 0.4rem) !important;
            min-width: calc(50% - 0.4rem) !important;
        }"""
        
    # Replace the existing [data-testid="column"] block inside the @media (max-width: 768px)
    pattern = r'\[data-testid="column"\]\s*\{\s*padding:\s*0\s*!important;\s*gap:\s*0\s*!important;\s*\}'
    
    c = re.sub(pattern, css_inject.strip(), c)
    
    with open('app/dashboard.py', 'w', encoding='utf-8') as f:
        f.write(c)

if __name__ == '__main__':
    main()

