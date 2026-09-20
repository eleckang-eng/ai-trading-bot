# coding=utf-8

def fix_indentation():
    with open("app/dashboard.py", "r", encoding="utf-8") as f:
        content = f.read()

    # Find the problematic block that starts with 4 spaces instead of 8
    bad_code = """
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

    # 체크박스 선택된 것만 카운트"""

    # We need to replace it with 8 spaces
    good_code = """
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

        # 체크박스 선택된 것만 카운트"""

    if bad_code in content:
        content = content.replace(bad_code, good_code)
        with open("app/dashboard.py", "w", encoding="utf-8") as f:
            f.write(content)
        print("Fixed indentation!")
    else:
        print("Bad code not found, manual fix needed.")

if __name__ == "__main__":
    fix_indentation()

