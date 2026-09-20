import re

with open('d:/aiworkspace/app/dashboard.py', 'r', encoding='utf-8') as f:
    content = f.read()

sidebar_pattern = re.compile(
    r'exchange_choice = st\.radio.*?if success:.*?st\.rerun\(\)',
    re.DOTALL
)

sidebar_replacement = '''
    # 0: 한투 실전, 1: 빗썸 실전, 2: ---, 3: 한투 모의, 4: 한투 테스트, 5: 빗썸 테스트
    current_cfg = status_data.get("config", {}) if status_data else {}
    curr_ex = current_cfg.get("exchange", "kis")
    curr_mock = current_cfg.get("mock_mode", True)
    curr_paper = current_cfg.get("paper_trading", False)
    
    default_idx = 3 # 한국투자증권 (모의 계좌) 기본
    if curr_ex == "kis":
        if curr_paper: default_idx = 4
        elif curr_mock: default_idx = 3
        else: default_idx = 0
    else:
        if curr_paper: default_idx = 5
        else: default_idx = 1

    exchange_choice = st.radio("거래소 및 투자 모드", [
        "🔴 한국투자증권 (실전)",
        "🔴 빗썸 (실전)",
        "────────────────────",
        "🟢 한국투자증권 (모의 계좌)",
        "🧪 한국투자증권 (테스트 - 미전송)",
        "🧪 빗썸 (테스트 - 미전송)"
    ], index=default_idx)
    
    if st.button("🔄 모드 적용", width="stretch"):
        if "─" in exchange_choice:
            st.warning("구분선은 선택할 수 없습니다. 모드를 선택해주세요.")
        else:
            new_exchange = "bithumb" if "빗썸" in exchange_choice else "kis"
            new_symbol = "ONDO" if new_exchange == "bithumb" else "042660"
            
            is_mock_account = "모의 계좌" in exchange_choice
            is_paper_trading = "테스트" in exchange_choice
            
            # 기본값 프리셋 적용
            new_grid = 2000 if new_exchange == "kis" else 10
            new_profit = 2000 if new_exchange == "kis" else 10
            new_budget = 3000000 if new_exchange == "kis" else 50000
            
            success = False
            try:
                payload = {
                    "exchange": new_exchange, 
                    "symbol": new_symbol,
                    "grid_interval": new_grid,
                    "take_profit": new_profit,
                    "order_amount": new_budget,
                    "mock_mode": is_mock_account,
                    "paper_trading": is_paper_trading
                }
                response = requests.post(f"{API_URL}/config", json=payload, timeout=5)
                if response.status_code == 200:
                    try:
                        requests.post(f"{API_URL}/refresh_balance", timeout=5)
                    except:
                        pass
                    st.success(f"{exchange_choice} 모드로 전환 및 자산 동기화 완료")
                    success = True
                else:
                    st.error("설정 변경 실패")
            except Exception as e:
                st.error(f"서버 통신 실패: {e}")
                
            if success:
                import time
                time.sleep(0.3)
                st.rerun()
'''

content = sidebar_pattern.sub(sidebar_replacement.strip(), content)

# 메인 파라미터 영역의 기존 테스트 모드 관련 로직 일괄 삭제 (정확히 치환)
content = re.sub(r'mock_mode = st\.toggle\(.*?\"🧪 테스트 모드.*?\)', '', content, flags=re.DOTALL)
content = re.sub(r'mock_mode = st\.toggle\(.*?\"🧪 KIS 모의투자.*?\)\n\s*else:\n\s*st\.info.*?\n\s*mock_mode = False', '', content, flags=re.DOTALL)
content = re.sub(r'mock_mode = st\.toggle\(.*?\"🧪 모의투자.*?\)', '', content, flags=re.DOTALL)
content = re.sub(r'if is_kis:\n\s*st\.caption\(.*?연동되어 테스트가 진행됩니다.*?\)', '', content, flags=re.DOTALL)
content = re.sub(r'\"mock_mode\": mock_mode,', '', content, flags=re.DOTALL)


with open('d:/aiworkspace/app/dashboard.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Dashboard UI updated successfully.')
