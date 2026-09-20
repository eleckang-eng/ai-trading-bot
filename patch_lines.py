# coding=utf-8
import sys

def patch_lines():
    with open("app/dashboard.py", "r", encoding="utf-8") as f:
        lines = f.readlines()
        
    # Replace lines 99 to 106 (index 99 to 106)
    new_radio = """    exchange_choice = st.selectbox("거래소 및 투자 모드", [
        "🔴 한국투자증권 (실전)",
        "🔴 빗썸 (실전)",
        "🟢 한국투자증권 (모의 계좌)",
        "🧪 한국투자증권 (테스트)",
        "🧪 빗썸 (테스트)"
    ], index=default_idx)
"""
    # Delete the old lines 99 to 106 and insert the new one
    del lines[99:107]
    lines.insert(99, new_radio)
    
    # We also need to fix the warning logic which is now around line 102
    # Find `if "─" in exchange_choice:`
    warn_idx = -1
    for i, line in enumerate(lines):
        if 'in exchange_choice:' in line and ('─' in line or '구분선' in line or '선' in line):
            warn_idx = i
            break
            
    if warn_idx != -1:
        # replace `if "─" in exchange_choice:` with `if False:`
        # and delete the warning body, or just replace the condition
        lines[warn_idx] = '        if False:\n'

    with open("app/dashboard.py", "w", encoding="utf-8") as f:
        f.writelines(lines)

if __name__ == "__main__":
    patch_lines()

