# coding=utf-8
import sys

def patch_mobile_fonts():
    with open("app/dashboard.py", "r", encoding="utf-8") as f:
        content = f.read()

    old_css = """    /* 모바일에서 Metric(수치) 폰트 크기 살짝 줄이기 */
    [data-testid="stMetricValue"] {
        font-size: 1.5rem !important;
    }"""
    
    new_css = """    /* 모바일에서 제목과 Metric(수치) 폰트 크기 대폭 줄이기 (줄바꿈 방지) */
    @media (max-width: 768px) {
        h1 { font-size: 1.5rem !important; }
        h2 { font-size: 1.25rem !important; }
        h3 { font-size: 1.1rem !important; }
        
        [data-testid="stMetricLabel"] p {
            font-size: 0.9rem !important;
            white-space: nowrap !important;
            overflow: hidden !important;
            text-overflow: ellipsis !important;
        }
        [data-testid="stMetricValue"] { font-size: 1.2rem !important; }
        
        /* 컬럼 간격 최소화 */
        [data-testid="column"] {
            padding: 0 !important;
            gap: 0 !important;
        }
        
        /* 탭 라벨 폰트 크기 조정 */
        button[data-baseweb="tab"] p {
            font-size: 0.9rem !important;
        }
    }"""

    content = content.replace(old_css, new_css)
    
    with open("app/dashboard.py", "w", encoding="utf-8") as f:
        f.write(content)

if __name__ == "__main__":
    patch_mobile_fonts()

