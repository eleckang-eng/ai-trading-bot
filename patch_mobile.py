# coding=utf-8
import sys

def patch_mobile():
    with open("app/dashboard.py", "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Change initial_sidebar_state
    content = content.replace(
        'initial_sidebar_state="expanded"',
        'initial_sidebar_state="auto"'
    )

    # 2. Fix CSS
    old_css = """<style>
    [data-testid="stSidebar"] { min-width: 440px !important; max-width: 480px !important; }
</style>"""
    
    new_css = """<style>
    /* 데스크톱에서만 사이드바 넓게 유지 */
    @media (min-width: 768px) {
        [data-testid="stSidebar"] { min-width: 440px !important; max-width: 480px !important; }
    }
    /* 모바일 웹뷰(앱) 최적화: 불필요한 Streamlit 기본 헤더/푸터 및 여백 제거 */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 1.5rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }
    /* 모바일에서 Metric(수치) 폰트 크기 살짝 줄이기 */
    [data-testid="stMetricValue"] {
        font-size: 1.5rem !important;
    }
</style>"""

    content = content.replace(old_css, new_css)
    
    with open("app/dashboard.py", "w", encoding="utf-8") as f:
        f.write(content)

if __name__ == "__main__":
    patch_mobile()

