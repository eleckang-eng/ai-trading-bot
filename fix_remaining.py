# coding=utf-8
import re

def main():
    with open('app/dashboard.py', 'r', encoding='utf-8') as f:
        c = f.read()

    # 1. 그리드 주문 확인창 엑셀
    c = c.replace('height=250)', 'height=400, hide_index=True)')

    # 2, 3, 4. 수동 주문 제어 리팩토링
    m_start_str = '    st.subheader("🕹️ 수동 주문 제어 (지정가 전용)")\n'
    m_end_str = '        st.session_state.confirm_cancel_all  = True\n        st.session_state.manual_order_result = None\n        st.rerun()\n'
    m_start_idx = c.find(m_start_str)
    m_end_idx = c.find(m_end_str)
    
    if m_start_idx != -1 and m_end_idx != -1:
        m_end_idx += len(m_end_str)
        old_m_block = c[m_start_idx:m_end_idx]
        new_m_block = """    m_title_col, m_btn_col = st.columns([4, 1])
    with m_title_col:
        st.subheader("🕹️ 수동 주문 제어 (지정가 전용)")
        if st.session_state.get("manual_price", 0) > 0:
            st.caption(f"현재가: **{st.session_state.manual_price:,}** 원")
    with m_btn_col:
        if st.button("🔄 현재가 가져오기", use_container_width=True):
            try:
                sym   = current_sym(current_cfg)
                p_res = requests.get(f"{API_URL}/price?exchange={curr_ex}&symbol={sym}", timeout=3)
                if p_res.status_code == 200:
                    p = p_res.json().get("price", 0)
                    if p > 0:
                        st.session_state.manual_price = int(p)
                        st.rerun()
            except: pass

    m_c1, m_c2, m_c3 = st.columns([2, 2, 3])
    with m_c1:
        default_p = st.session_state.get("manual_price", 0) or (83500 if curr_ex == "kis" else 1000)
        m_price   = st.number_input("주문 단가 (원)", min_value=1, value=default_p, step=None)

    with m_c2:
        m_qty = st.number_input("주문 수량", min_value=1, value=10 if curr_ex == "kis" else 1000, step=1)

    with m_c3:
        st.write("")
        st.write("")
        c_buy, c_sell = st.columns(2)
        with c_buy:
            if st.button("🔴 매수", use_container_width=True):
                if m_price > 0:
                    st.session_state.confirm_manual_order  = {"side": "buy",  "quantity": int(m_qty), "price": int(m_price)}
                    st.session_state.manual_order_result   = None
                    st.rerun()
        with c_sell:
            if st.button("🔵 매도", use_container_width=True):
                if m_price > 0:
                    st.session_state.confirm_manual_order  = {"side": "sell", "quantity": int(m_qty), "price": int(m_price)}
                    st.session_state.manual_order_result   = None
                    st.rerun()
                    
    if st.button("🗑️ 미체결 전체 취소", use_container_width=True, type="primary"):
        st.session_state.confirm_cancel_all  = True
        st.session_state.manual_order_result = None
        st.rerun()\n"""
        c = c.replace(old_m_block, new_m_block)

    # 5. 잔고동기화버튼 이동 (대시보드 -> 시스템설정)
    sync_target = '        if st.button("🔄 잔고 동기화", use_container_width=True):\n            try: requests.post(f"{API_URL}/refresh_balance", timeout=15); st.rerun()\n            except: st.error("동기화 실패")\n'
    if sync_target in c:
        c = c.replace(sync_target, "")
        header_target = 'st.header("🤖 시스템 제어")\n'
        if header_target in c:
            new_btn = header_target + '    if st.button("🔄 잔고 동기화 (전체 포지션 및 예수금 반영)", use_container_width=True):\n        try: requests.post(f"{API_URL}/refresh_balance", timeout=15); st.rerun()\n        except: st.error("동기화 실패")\n'
            c = c.replace(header_target, new_btn)

    # 6. 진입 거래망 현황 -> 주문 현황
    c = c.replace('st.subheader("📊 진입 거래망 현황")', 'st.subheader("📊 주문 현황")')

    # 7. 대기 중인 매수/매도 그리드 문구 삭제
    c = c.replace('st.subheader("⏳ 대기 중인 매수/매도 그리드")', 'pass')

    # 8. 보기방식 문구 삭제
    view_target = 'view_mode = st.radio("보기 방식",\n        ["📈 차트 뷰", "📊 호가창 정렬", "📋 주문순 정렬"],\n        horizontal=True)'
    if view_target in c:
        c = c.replace(view_target, 'view_mode = st.radio("보기 방식", ["📈 차트 뷰", "📊 호가창 정렬", "📋 주문순 정렬"], label_visibility="collapsed", horizontal=True)')

    # 9. 시스템 상태는 시스템설정으로 이동
    start_str = '    st.subheader("🤖 시스템 상태")\n'
    end_str = 'st.write(f"**1회 주문 수량:** {ex_cfg_disp.get(\'order_quantity\', \'-\')}")\n'
    start_idx = c.find(start_str)
    end_idx = c.find(end_str)
    
    if start_idx != -1 and end_idx != -1:
        end_idx += len(end_str)
        sys_block = c[start_idx:end_idx]
        c = c.replace(sys_block, "")
        
        inject_target = 'except: st.error("동기화 실패")\n'
        c = c.replace(inject_target, inject_target + '    st.markdown("---")\n' + sys_block)

    with open('app/dashboard.py', 'w', encoding='utf-8') as f:
        f.write(c)

if __name__ == '__main__':
    main()

