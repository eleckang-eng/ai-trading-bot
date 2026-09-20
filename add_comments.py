# coding=utf-8

def main():
    with open('app/dashboard.py', 'r', encoding='utf-8') as f:
        c = f.read()

    # Add a documentation comment block to the top of dashboard.py
    doc_comment = '''"""
=============================================================================
[대규모 UX/UI 개선 히스토리 및 참고사항 - 2026-09-20]
1. 모바일 레이아웃 강어:
   - Streamlit 기본 속성으로 인해 창 폭이 줄어들면 st.columns()가 1열(세로)로 풀리는 현상 발생.
   - 이를 원천 방어하기 위해 <style> 내부에 flex-direction: row !important; 와 
     flex-wrap: nowrap !important; CSS를 추가. 어떠한 경우에도 50% 너비 2열로 고정됨.
2. 그리드 설정창 자동 접힘 (Expander):
   - 주문 생성 탭(tab_order)의 파라미터 입력부 전체를 st.expander()로 감쌈.
   - '균등/계단식 그리드 생성' 버튼 클릭 시 st.session_state.show_grid_preview가 True로 변경되며,
     expanded=not show_grid_preview 속성에 의해 설정창이 즉시 접히고(팝업아웃 효과) 표가 화면을 채움.
=============================================================================
"""
'''
    if 'UX/UI 개선 히스토리' not in c:
        # insert after the imports
        import_end = c.find('import time\n') + len('import time\n')
        c = c[:import_end] + '\n' + doc_comment + c[import_end:]

    with open('app/dashboard.py', 'w', encoding='utf-8') as f:
        f.write(c)

if __name__ == '__main__':
    main()

