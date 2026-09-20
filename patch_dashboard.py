# coding=utf-8
import sys

def patch_dashboard():
    with open("app/dashboard.py", "r", encoding="utf-8") as f:
        lines = f.readlines()
        
    # 1. Add toggle
    toggle_code = """
    st.divider()

    # 중복 주문 제거 토글창 추가
    remove_dup = st.toggle("중복주문제거", value=True, help="켜져 있을 때는 중복 주문 자동 제거해서 주문해줌. 꺼져 있을 때는 기존과 동일함")
    st.session_state.remove_dup = remove_dup
"""
    
    # insert before "12. 파라미터 저장"
    for i, line in enumerate(lines):
        if "12. " in line and "파라미터 저장" in line:
            lines.insert(i-1, toggle_code)
            break
            
    # 2. Add duplicate removal logic
    # Find "overlap = sorted({"
    for i, line in enumerate(lines):
        if "overlap = sorted({" in line:
            filter_code = """                if st.session_state.get("remove_dup", True):
                    checked_sell = [r for r in checked_sell if float(r.get("가격", 0)) not in existing_prices]
                    checked_buy = [r for r in checked_buy if float(r.get("가격", 0)) not in existing_prices]
"""
            lines.insert(i, filter_code)
            break
            
    with open("app/dashboard.py", "w", encoding="utf-8") as f:
        f.writelines(lines)

if __name__ == "__main__":
    patch_dashboard()

