# coding=utf-8
import sys

def main():
    with open('app/dashboard.py', 'r', encoding='utf-8') as f:
        c = f.read()

    css_inject = """
        /* 컬럼 간격 최소화 및 모바일 2열(50%) 강제 (한 줄 풀림 방지) */
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
        
    old_css = """
        /* 컬럼 간격 최소화 */
        [data-testid="column"] {
            padding: 0 !important;
            gap: 0 !important;
        }"""
        
    if old_css in c:
        c = c.replace(old_css, css_inject)
    else:
        # Just in case the exact old_css is not found, find `@media (max-width: 768px) {`
        # and insert the new css rules right after it.
        pass

    # Actually let's just do a direct string replace if possible.
    
    with open('app/dashboard.py', 'w', encoding='utf-8') as f:
        f.write(c)

if __name__ == '__main__':
    main()

