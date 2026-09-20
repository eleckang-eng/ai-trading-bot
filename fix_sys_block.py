# coding=utf-8

def main():
    with open('app/dashboard.py', 'r', encoding='utf-8') as f:
        c = f.read()

    # The block we need to inject:
    sys_block = """    st.subheader("🤖 시스템 상태")
    st.subheader("엔진 구동 상태")
    col_a, col_b = st.columns(2)
    ex_cfg_disp = cfg.get(curr_ex, {})
    with col_a:
        st.write(f"**상태:** {'🟢 가동 중' if status_data.get('running', False) else '🔴 정지됨'}")
        st.write(f"**거래소:** {curr_ex.upper()}")
        st.write(f"**종목:** {current_sym(current_cfg)}")
        st.write(f"**모드:** {mode_badge}")
    with col_b:
        st.write(f"**기준가:** {ex_cfg_disp.get('base_price', 0):,}")
        st.write(f"**그리드 간격:** {ex_cfg_disp.get('grid_interval', '-')}")
        st.write(f"**익절 간격:** {ex_cfg_disp.get('take_profit', '-')}")
        st.write(f"**1회 주문 수량:** {ex_cfg_disp.get('order_quantity', '-')}")
"""

    # Inject under tab_settings
    inject_point = '    if st.button("🔄 잔고 동기화 (전체 포지션 및 예수금 반영)", use_container_width=True):\n        try: requests.post(f"{API_URL}/refresh_balance", timeout=15); st.rerun()\n        except: st.error("동기화 실패")\n'
    
    if inject_point in c:
        c = c.replace(inject_point, inject_point + '    st.markdown("---")\n' + sys_block)
        
    # Remove '대기 중인 매수/매도 그리드'
    c = c.replace('    st.subheader("🕸️ 대기 중인 매수/매도 그리드")\n', '')
    c = c.replace('st.subheader("🕸️ 대기 중인 매수/매도 그리드")', 'pass')
    
    with open('app/dashboard.py', 'w', encoding='utf-8') as f:
        f.write(c)

if __name__ == '__main__':
    main()

