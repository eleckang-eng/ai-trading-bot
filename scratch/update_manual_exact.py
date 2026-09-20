import codecs

file_path = r'd:\aiworkspace\app\dashboard.py'
with codecs.open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

start_idx = -1
for i, l in enumerate(lines):
    if 'c_buy, c_sell = st.columns(2)' in l:
        start_idx = i
        break

if start_idx != -1:
    end_idx = start_idx + 41 # up to st.divider()
    
    new_code = '''        c_buy, c_sell = st.columns(2)
        with c_buy:
            if st.button("🔴 매수", width="stretch"):
                if m_price <= 0:
                    st.error("주문 가격을 1원 이상 입력하십시오.")
                else:
                    st.session_state.confirm_manual_order = {"side": "buy", "quantity": int(m_qty), "price": int(m_price)}
                    st.rerun()
        with c_sell:
            if st.button("🔵 매도", width="stretch"):
                if m_price <= 0:
                    st.error("주문 가격을 1원 이상 입력하십시오.")
                else:
                    st.session_state.confirm_manual_order = {"side": "sell", "quantity": int(m_qty), "price": int(m_price)}
                    st.rerun()
                        
    with m_c4:
        st.write("")
        st.write("")
        if st.button("🗑️ 미체결 일괄 취소", width="stretch", type="primary"):
            st.session_state.confirm_cancel_all = True
            st.rerun()

    if st.session_state.get("confirm_manual_order"):
        order = st.session_state.confirm_manual_order
        side_kor = "🔴 매수" if order["side"] == "buy" else "🔵 매도"
        st.warning(f"정말로 **{side_kor}** 주문을 전송하시겠습니까? (단가: {order['price']:,} 원, 수량: {order['quantity']} 주)")
        cc1, cc2 = st.columns(2)
        with cc1:
            if st.button("✅ 주문 전송", type="primary", use_container_width=True):
                try:
                    import requests
                    res = requests.post(f"{API_URL}/order/manual", json=order, timeout=5)
                    data = res.json()
                    if data.get("status") == "success":
                        st.success(data.get("message", f"{side_kor} 성공"))
                    else:
                        st.error(data.get("message", f"{side_kor} 에러"))
                except Exception as e:
                    st.error(f"요청 실패: {e}")
                st.session_state.confirm_manual_order = None
                import time; time.sleep(1.5); st.rerun()
        with cc2:
            if st.button("❌ 취소", use_container_width=True):
                st.session_state.confirm_manual_order = None
                st.rerun()

    if st.session_state.get("confirm_cancel_all"):
        st.warning("정말로 **모든 미체결 주문을 일괄 취소**하시겠습니까?")
        cc1, cc2 = st.columns(2)
        with cc1:
            if st.button("✅ 전체 취소 실행", type="primary", use_container_width=True):
                try:
                    import requests
                    res = requests.post(f"{API_URL}/order/cancel_all", timeout=5)
                    st.success(res.json().get("message", "모든 주문이 취소되었습니다."))
                except:
                    st.error("취소 요청 실패")
                st.session_state.confirm_cancel_all = False
                import time; time.sleep(1.5); st.rerun()
        with cc2:
            if st.button("❌ 돌아가기", use_container_width=True):
                st.session_state.confirm_cancel_all = False
                st.rerun()
'''
    new_lines = [line + '\n' for line in new_code.split('\n')]
    lines[start_idx:end_idx] = new_lines

    with codecs.open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    print('Replaced exact lines successfully.')
else:
    print('Could not find start idx.')

