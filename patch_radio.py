# coding=utf-8
import sys

def patch_radio():
    with open("app/dashboard.py", "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Update index logic
    old_idx = """if curr_ex == "kis":
        if curr_paper:  default_idx = 4
        elif curr_mock: default_idx = 3
        else:           default_idx = 0
    else:
        default_idx = 5 if curr_paper else 1"""
    
    new_idx = """if curr_ex == "kis":
        if curr_paper:  default_idx = 3
        elif curr_mock: default_idx = 2
        else:           default_idx = 0
    else:
        default_idx = 4 if curr_paper else 1"""
    
    content = content.replace(old_idx, new_idx)

    # 2. Update radio list
    old_radio = """exchange_choice = st.radio("거래소 및 투자 모드", [
        "🔴 한국투자증권 (실전)",
        "🔴 빗썸 (실전)",
        "────────────────────────────────────────",
        "🟢 한국투자증권 (모의 계좌)",
        "🧪 한국투자증권 (테스트)",
        "🧪 빗썸 (테스트)"
    ], index=default_idx)"""
    
    new_radio = """exchange_choice = st.selectbox("거래소 및 투자 모드", [
        "🔴 한국투자증권 (실전)",
        "🔴 빗썸 (실전)",
        "🟢 한국투자증권 (모의 계좌)",
        "🧪 한국투자증권 (테스트)",
        "🧪 빗썸 (테스트)"
    ], index=default_idx)"""
    
    content = content.replace(old_radio, new_radio)

    # 3. Update the warning logic that checked for the divider
    old_warn = """    if "─" in exchange_choice:
        st.warning("옵션을 제대로 선택하세요.")
    else:"""
    
    new_warn = """    if False:
        pass
    else:"""
    
    content = content.replace(old_warn, new_warn)

    with open("app/dashboard.py", "w", encoding="utf-8") as f:
        f.write(content)

if __name__ == "__main__":
    patch_radio()

