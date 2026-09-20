# coding=utf-8
import sys

def patch_css():
    with open('app/dashboard.py', 'r', encoding='utf-8') as f:
        content = f.read()
        
    compact_css = """
<style>
    /* 윈도우/모바일 공통: 극단적인 여백(Padding/Margin) 축소 */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 1rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
        max-width: 1400px !important;
    }
    
    /* 각 요소들 간의 상하 간격 줄이기 */
    div[data-testid="stVerticalBlock"] > div {
        margin-bottom: -0.5rem !important;
    }
    
    /* 탭 메뉴 상하 간격 축소 */
    button[data-baseweb="tab"] {
        padding-top: 0.2rem !important;
        padding-bottom: 0.2rem !important;
        font-size: 1.1rem !important;
    }
    
    /* 숫자/메트릭 폰트 및 여백 축소 */
    div[data-testid="metric-container"] {
        padding-top: 0 !important;
        padding-bottom: 0 !important;
    }
    
    /* 데이터프레임 높이 튜닝 */
    div[data-testid="stDataFrame"] {
        margin-top: -0.5rem !important;
    }
"""
    # Replace the existing <style> tag with our new comprehensive CSS
    if '<style>' in content:
        content = content.replace('<style>', compact_css)
        with open('app/dashboard.py', 'w', encoding='utf-8') as f:
            f.write(content)
        print("CSS patched!")

if __name__ == '__main__':
    patch_css()

