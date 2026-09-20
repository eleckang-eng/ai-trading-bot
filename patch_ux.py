# coding=utf-8
import sys

def patch_ux():
    with open("app/dashboard.py", "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Add height=300 to all st.data_editor
    content = content.replace(
        'edited_sell = st.data_editor(s_list, num_rows="dynamic", key="sell_editor", use_container_width=True)',
        'edited_sell = st.data_editor(s_list, num_rows="dynamic", key="sell_editor", use_container_width=True, height=250)'
    )
    content = content.replace(
        'edited_buy  = st.data_editor(b_list, num_rows="dynamic", key="buy_editor",  use_container_width=True)',
        'edited_buy  = st.data_editor(b_list, num_rows="dynamic", key="buy_editor",  use_container_width=True, height=250)'
    )
    content = content.replace(
        'edited_sell = st.data_editor(s_list, num_rows="dynamic", key="sell_editor_only", use_container_width=True)',
        'edited_sell = st.data_editor(s_list, num_rows="dynamic", key="sell_editor_only", use_container_width=True, height=250)'
    )
    content = content.replace(
        'edited_buy  = st.data_editor(b_list, num_rows="dynamic", key="buy_editor_only",  use_container_width=True)',
        'edited_buy  = st.data_editor(b_list, num_rows="dynamic", key="buy_editor_only",  use_container_width=True, height=250)'
    )

    # 2. Add JavaScript to auto-close sidebar when preview is shown
    js_code = """
    # 체크박스 선택된 것만 카운트
"""
    new_js_code = """
    # 모바일 환경에서 그리드가 생성되었을 때 사이드바를 자동으로 닫아주는 JS 트릭
    import streamlit.components.v1 as components
    components.html('''
        <script>
            // 모바일 화면 너비일 때만 작동
            if(window.parent.innerWidth <= 768) {
                const closeBtn = window.parent.document.querySelector('[data-testid="stSidebarCollapseButton"]');
                if(closeBtn) {
                    closeBtn.click();
                }
            }
        </script>
    ''', height=0)

    # 체크박스 선택된 것만 카운트
"""
    content = content.replace("    # 체크박스 선택된 것만 카운트\n", new_js_code)

    with open("app/dashboard.py", "w", encoding="utf-8") as f:
        f.write(content)

if __name__ == "__main__":
    patch_ux()

