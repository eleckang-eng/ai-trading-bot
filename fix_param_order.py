import codecs
import re

with codecs.open('d:/aiworkspace/app/dashboard.py', 'r', encoding='utf-8') as f:
    text = f.read()

# 기존에 엉망으로 넣은 파라미터 블록 찾기
bad_param_block = '''    st.subheader("🎛️ 매매 알고리즘 파라미터")
    cfg = status_data.get("config", {}) if status_data else {}
    current_exchange = cfg.get("exchange", "bithumb")
    ex_cfg = cfg.get(current_exchange, {})
    is_kis = current_exchange == "kis"

    default_grid = 2000 if is_kis else 10
    default_profit = 2000 if is_kis else 10
    default_qty = 10 if is_kis else 1000
    step_val = 50 if is_kis else 1

    current_market_price = st.session_state.get("manual_price", 0)
    base_price_val = ex_cfg.get("base_price", 0)
    if base_price_val == 0 and current_market_price > 0:
        base_price_val = current_market_price

    base_price = st.number_input("기준가 (0 입력시 자동 계산)", min_value=0.0, value=float(base_price_val), step=float(step_val))
    grid_interval = st.number_input("매수 하락폭 (간격)", min_value=1, value=ex_cfg.get("grid_interval", default_grid), step=step_val)
    take_profit = st.number_input("매도 수익폭 (익절)", min_value=1, value=ex_cfg.get("take_profit", default_profit), step=step_val)
    order_quantity = st.number_input("1회 주문 수량", min_value=1, value=ex_cfg.get("order_quantity", default_qty), step=1)
        
    grid_direction = st.radio("방향", ["매도만", "매수만", "매수/매도 모두"], index=2, horizontal=True)

    c_s, c_b = st.columns(2)
    with c_s: sell_count = st.number_input("매도 개수", min_value=1, max_value=50, value=10, step=1)
    with c_b: buy_count = st.number_input("매수 개수", min_value=1, max_value=50, value=10, step=1)

    if st.button("📝 설정 확인 (그리드 뷰 생성)", width="stretch", type="primary"):
        sell_list = []
        buy_list = []
        bp = base_price if base_price > 0 else (83500 if is_kis else 1000)
        
        if grid_direction in ["매도만", "매수/매도 모두"]:
            for i in range(1, sell_count + 1):
                s_price = bp + (take_profit * i)
                s_price = (s_price // 1000) * 1000 + 900 if is_kis else (s_price // 10) * 10 + 9
                sell_list.append({"선택": True, "가격": int(s_price), "수량": int(order_quantity)})
                
        if grid_direction in ["매수만", "매수/매도 모두"]:
            for i in range(1, buy_count + 1):
                b_price = bp - (grid_interval * i)
                b_price = (b_price // 1000) * 1000 + 100 if is_kis else (b_price // 10) * 10 + 1
                buy_list.append({"선택": True, "가격": int(b_price), "수량": int(order_quantity)})
            
        st.session_state.grid_sell_list = sell_list
        st.session_state.grid_buy_list = buy_list
        st.session_state.show_grid_preview = True

    if st.button("💾 이 파라미터 봇에 저장", width="stretch"):
        try:
            requests.post(f"{API_URL}/config", json={
                current_exchange: {
                    "base_price": base_price, "grid_interval": grid_interval,
                    "take_profit": take_profit, "order_quantity": order_quantity
                }
            }, timeout=5)
            st.success("저장 완료")
        except:
            st.error("저장 실패")'''

# 완벽하게 복구할 원본 형태 (columns 레이아웃 유지)
good_param_block = '''    st.subheader("🎛️ 매매 알고리즘 파라미터 (그리드 설정)")
    cfg = status_data.get("config", {}) if status_data else {}
    current_exchange = cfg.get("exchange", "bithumb")
    ex_cfg = cfg.get(current_exchange, {})
    is_kis = current_exchange == "kis"

    default_grid = 2000 if is_kis else 10
    default_profit = 2000 if is_kis else 10
    default_qty = 10 if is_kis else 1000
    step_val = 50 if is_kis else 1

    current_market_price = st.session_state.get("manual_price", 0)
    base_price_val = ex_cfg.get("base_price", 0)
    if base_price_val == 0 and current_market_price > 0:
        base_price_val = current_market_price

    c_p1, c_p2 = st.columns(2)
    with c_p1:
        base_price = st.number_input("기준가 (0 입력시 현재가 적용)", min_value=0.0, value=float(base_price_val), step=float(step_val))
        grid_interval = st.number_input("매수 하락폭 (그리드 간격)", min_value=1, value=ex_cfg.get("grid_interval", default_grid), step=step_val)
    with c_p2:
        take_profit = st.number_input("매도 수익폭 (익절 간격)", min_value=1, value=ex_cfg.get("take_profit", default_profit), step=step_val)
        order_quantity = st.number_input("1회 매수 수량", min_value=1, value=ex_cfg.get("order_quantity", default_qty), step=1)
        
    grid_direction = st.radio("주문 방향 선택", ["매도만", "매수만", "매수/매도 모두"], index=2, horizontal=True)

    col_sell_cnt, col_buy_cnt = st.columns(2)
    with col_sell_cnt:
        sell_count = st.number_input("매도 주문 개수", min_value=1, max_value=50, value=10, step=1)
    with col_buy_cnt:
        buy_count = st.number_input("매수 주문 개수", min_value=1, max_value=50, value=10, step=1)

    c_btn_gen, c_btn_save = st.columns(2)
    with c_btn_gen:
        if st.button("📝 설정 확인 (그리드 생성)", width="stretch"):
            sell_list = []
            buy_list = []
            bp = base_price if base_price > 0 else (83500 if is_kis else 1000)
            
            if grid_direction in ["매도만", "매수/매도 모두"]:
                for i in range(1, sell_count + 1):
                    s_price = bp + (take_profit * i)
                    s_price = (s_price // 1000) * 1000 + 900 if is_kis else (s_price // 10) * 10 + 9
                    sell_list.append({"선택": True, "가격": int(s_price), "수량": int(order_quantity)})
                    
            if grid_direction in ["매수만", "매수/매도 모두"]:
                for i in range(1, buy_count + 1):
                    b_price = bp - (grid_interval * i)
                    b_price = (b_price // 1000) * 1000 + 100 if is_kis else (b_price // 10) * 10 + 1
                    buy_list.append({"선택": True, "가격": int(b_price), "수량": int(order_quantity)})
                
            st.session_state.grid_sell_list = sell_list
            st.session_state.grid_buy_list = buy_list
            st.session_state.show_grid_preview = True
            
    with c_btn_save:
        if st.button("💾 이 파라미터 봇에 저장", width="stretch"):
            try:
                requests.post(f"{API_URL}/config", json={
                    current_exchange: {
                        "base_price": base_price,
                        "grid_interval": grid_interval,
                        "take_profit": take_profit,
                        "order_quantity": order_quantity
                    }
                }, timeout=5)
                st.success("저장 완료")
            except:
                st.error("저장 실패")'''

text = text.replace(bad_param_block, good_param_block)

with codecs.open('d:/aiworkspace/app/dashboard.py', 'w', encoding='utf-8') as f:
    f.write(text)
print('Parameter UI restored to original column layout.')
