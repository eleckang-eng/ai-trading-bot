import codecs
import re

with codecs.open('d:/aiworkspace/app/dashboard.py', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. 수동 주문 확인창 복원
old_manual = '''        with c_buy:
            if st.button("🔴 매수", width="stretch"):
                if m_price <= 0:
                    st.error("주문 가격을 1원 이상 입력하십시오.")
                else:
                    try:
                        payload = {"side": "buy", "quantity": int(m_qty), "price": int(m_price)}
                        res = requests.post(f"{API_URL}/order/manual", json=payload, timeout=5)
                        data = res.json()
                        if data.get("status") == "success":
                            st.success(data.get("message", "매수 성공"))
                        else:
                            st.error(data.get("message", "매수 에러"))
                    except Exception as e:
                        st.error(f"매수 요청 실패: {e}")
        with c_sell:
            if st.button("🔵 매도", width="stretch"):
                if m_price <= 0:
                    st.error("주문 가격을 1원 이상 입력하십시오.")
                else:
                    try:
                        payload = {"side": "sell", "quantity": int(m_qty), "price": int(m_price)}
                        res = requests.post(f"{API_URL}/order/manual", json=payload, timeout=5)
                        data = res.json()
                        if data.get("status") == "success":
                            st.success(data.get("message", "매도 성공"))
                        else:
                            st.error(data.get("message", "매도 에러"))
                    except Exception as e:
                        st.error(f"매도 요청 실패: {e}")
                        
    with m_c4:
        st.write("")
        st.write("")
        if st.button("🗑️ 미체결 일괄 취소", width="stretch", type="primary"):
            try:
                res = requests.post(f"{API_URL}/order/cancel_all", timeout=5)
                st.warning(res.json().get("message", "모든 주문이 취소되었습니다."))
            except:
                st.error("취소 요청 실패")'''

new_manual = '''        with c_buy:
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
        st.warning(f"정말로 **{side_kor}** 주문을 전송하시겠습니까? (단가: {order['price']:,} 원  수량: {order['quantity']} 주)")
        
        # 중복 검사
        existing_prices = [float(p.get("price", p.get("avg_price", 0))) for p in status_data.get('positions', []) if str(p.get("side", "")).lower() == order["side"] or str(p.get("side", "")) == side_kor[-2:]]
        if float(order['price']) in existing_prices:
            st.error(f"⚠️ 이미 거래망에 동일한 가격({order['price']:,}원)의 주문이 존재합니다. 중복 주문일 수 있습니다!")
            
        cc1, cc2 = st.columns(2)
        with cc1:
            if st.button("✅ 네, 전송합니다", type="primary", use_container_width=True):
                try:
                    res = requests.post(f"{API_URL}/order/manual", json=order, timeout=5)
                    data = res.json()
                    if data.get("status") == "success":
                        st.success(data.get("message", f"{side_kor} 성공"))
                    else:
                        st.error(data.get("message", f"{side_kor} 에러"))
                except Exception as e:
                    st.error(f"요청 실패: {e}")
                st.session_state.confirm_manual_order = None
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
                    res = requests.post(f"{API_URL}/order/cancel_all", timeout=5)
                    st.success(res.json().get("message", "모든 주문이 취소되었습니다."))
                except:
                    st.error("취소 요청 실패")
                st.session_state.confirm_cancel_all = False
        with cc2:
            if st.button("❌ 돌아가기", use_container_width=True):
                st.session_state.confirm_cancel_all = False
                st.rerun()'''

text = text.replace(old_manual, new_manual)


# 2. 일괄 주문 겹침 검사 복원
old_batch_warn = '''                st.warning("⚠️ 정말로 이대로 거래소에 주문을 전송하시겠습니까? (실제 자산이 매매됩니다.)")
                c1_batch, c2_batch = st.columns(2)'''

new_batch_warn = '''                st.warning("⚠️ 정말로 이대로 거래소에 주문을 전송하시겠습니까? (실제 자산이 매매됩니다.)")
                
                existing_prices = [float(p.get("price", p.get("avg_price", 0))) for p in status_data.get('positions', [])]
                overlap = []
                for row in edited_sell + edited_buy:
                    price = row.get("가격")
                    if price and float(price) in existing_prices:
                        overlap.append(float(price))
                        
                if overlap:
                    unique_overlap = sorted(list(set(overlap)))
                    overlap_str = ", ".join([f"{int(p):,}원" for p in unique_overlap])
                    st.error(f"⚠️ 이미 거래중인 미체결 건과 다음 가격의 주문이 겹칩니다: {overlap_str}\\n중복 주문일 수 있으니 다시 한 번 확인해 주세요!")
                
                c1_batch, c2_batch = st.columns(2)'''

text = text.replace(old_batch_warn, new_batch_warn)

with codecs.open('d:/aiworkspace/app/dashboard.py', 'w', encoding='utf-8') as f:
    f.write(text)
print('Confirmation windows restored.')
