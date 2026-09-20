import codecs

dashboard_code = '''import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# 페이지 설정
st.set_page_config(page_title="AI 핑퐁 봇", page_icon="📈", layout="wide",
                   initial_sidebar_state="expanded")

API_URL = "http://localhost:8000"

# --- 커스텀 CSS ---
st.markdown("""
<style>
    /* 사이드바 폭 확장 */
    [data-testid="stSidebar"] {
        min-width: 450px !important;
        max-width: 500px !important;
    }
    .reportview-container .main .block-container{
        padding-top: 2rem;
    }
</style>
""", unsafe_allow_html=True)

st.title("📈 핑퐁 봇 대시보드")

# 상태 조회를 캐싱하지 않고 매번 새로고침 하도록 구현
def fetch_status():
    try:
        response = requests.get(f"{API_URL}/status", timeout=10)
        if response.status_code == 200:
            return response.json()
    except Exception:
        pass
    return None

status_data = fetch_status()

# 최초 1회 자산 동기화
if status_data and "initial_balance_refreshed" not in st.session_state:
    try:
        requests.post(f"{API_URL}/refresh_balance", timeout=5)
    except:
        pass
    st.session_state.initial_balance_refreshed = True
    st.rerun()

# --- 사이드바 제어 ---
with st.sidebar:
    st.header("⚙️ 시스템 제어")
    
    # 거래소 및 투자 모드 선택
    current_cfg = status_data.get("config", {}) if status_data else {}
    curr_ex = current_cfg.get("exchange", "kis")
    curr_mock = current_cfg.get("mock_mode", True)
    curr_paper = current_cfg.get("paper_trading", False)
    
    # 0: 한투 실전, 1: 빗썸 실전, 2: ---, 3: 한투 모의, 4: 한투 테스트, 5: 빗썸 테스트
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

    st.divider()
    
    # 봇 자동 매매 제어
    st.subheader("봇 자동 매매 제어")
    is_running = status_data.get("running", False) if status_data else False
    if is_running:
        st.success("🟢 봇 코어 루프가 실행 중입니다.")
    else:
        st.error("🔴 봇 코어 루프가 정지되어 있습니다.")
        
    c_btn1, c_btn2 = st.columns(2)
    with c_btn1:
        if is_running:
            st.button("▶️ 시작", width="stretch", disabled=True)
        else:
            if st.button("▶️ 시작", width="stretch"):
                try:
                    requests.post(f"{API_URL}/start", timeout=5)
                    st.rerun()
                except:
                    pass
    with c_btn2:
        if st.button("🔄 봇 서버 재시작", width="stretch"):
            try:
                res = requests.post(f"{API_URL}/system/restart", timeout=3)
                st.warning("서버 재시작 명령을 전송했습니다. 3~5초 뒤에 동작을 확인하세요.")
            except:
                st.warning("서버 재시작 중...")
        if not is_running:
            st.button("⏹️ 정지", width="stretch", disabled=True)
        else:
            if st.button("⏹️ 정지", width="stretch"):
                try:
                    requests.post(f"{API_URL}/stop", timeout=5)
                    st.rerun()
                except:
                    pass

# --- 메인 대시보드 ---
if status_data:
    # 1. 상단 메트릭 카드
    c1, c2, c3, c4 = st.columns(4)
    
    is_connected = status_data.get('exchange_connected', False)
    conn_str = "연동 완료" if is_connected else "연동 실패/대기"
    conn_color = "normal" if is_connected else "off"
    
    with c1:
        st.metric(label="총 자산 (예수금)", value=f"{status_data.get('balance', 0):,} 원", delta=conn_str, delta_color=conn_color)
        if st.button("🔄 잔고 동기화", width="stretch"):
            try:
                res = requests.post(f"{API_URL}/refresh_balance", timeout=15)
                if res.status_code == 200:
                    st.rerun()
                else:
                    st.error("잔고 동기화 실패")
            except requests.exceptions.RequestException:
                st.error("잔고 동기화 실패")
    with c2:
        st.metric(label="누적 실현 수익", value=f"{status_data.get('total_profit', 0):,} 원", delta="0.00%", delta_color="normal")
    with c3:
        st.metric(label="금일 체결 횟수", value=f"{status_data.get('trade_count', 0)} 회")
    with c4:
        st.metric(label="활성 거래중 노드", value=f"{len(status_data.get('positions', []))} 개")
    
    st.divider()
    
    # 🕹️ 수동 주문 제어 (Manual Control) 영역
    st.subheader("🕹️ 수동 주문 제어 (지정가 전용)")
    
    if "manual_price" not in st.session_state:
        st.session_state.manual_price = 0
        
    current_exchange = status_data.get('config', {}).get("exchange", "kis")
    sym = current_cfg.get("symbol", "ONDO" if current_exchange == "bithumb" else "042660")
    
    m_c0, m_c1, m_c2, m_c3, m_c4 = st.columns([1.2, 1.6, 1.2, 1.5, 1.3])
    
    with m_c0:
        st.write("")
        st.write("")
        if st.button("🔎 현재가 조회", width="stretch", help="현재 시장가를 조회하여 주문 단가에 자동 입력합니다."):
            try:
                p_res = requests.get(f"{API_URL}/price?exchange={current_exchange}&symbol={sym}", timeout=3)
                if p_res.status_code == 200:
                    fetched_p = p_res.json().get("price", 0)
                    if fetched_p > 0:
                        st.session_state.manual_price = int(fetched_p)
                        st.rerun()
                    else:
                        st.error("현재가 0 수신")
                else:
                    st.error("조회 실패")
            except:
                st.error("서버 통신 실패")
        if st.session_state.manual_price > 0:
            st.caption(f"현재가: **{st.session_state.manual_price:,}** 원")
            
    with m_c1:
        is_kis = current_exchange == "kis"
        step_val = 50 if is_kis else 1
        default_p = st.session_state.manual_price if st.session_state.manual_price > 0 else (83500 if is_kis else 1000)
        m_price = st.number_input("주문 단가 (원)", min_value=1, value=default_p, step=step_val)
        
    with m_c2:
        default_manual_qty = 10 if is_kis else 1000
        m_qty = st.number_input("주문 수량 (정수)", min_value=1, value=default_manual_qty, step=1)
        
    with m_c3:
        st.write("")
        st.write("")
        c_buy, c_sell = st.columns(2)
        with c_buy:
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
                st.error("취소 요청 실패")

    st.divider()
    
    if st.session_state.get("show_grid_preview", False):
        st.subheader("📋 그리드 주문 리스트 확인 및 편집")
        st.info("아래 표의 데이터를 클릭하여 가격과 수량을 직접 수정할 수 있습니다.")
        
        has_sell = len(st.session_state.grid_sell_list) > 0
        has_buy = len(st.session_state.grid_buy_list) > 0
        
        if has_sell and has_buy:
            g_c1, g_c2 = st.columns(2)
            with g_c1:
                st.markdown(f"#### 🔵 매도 리스트 (위로 {len(st.session_state.grid_sell_list)}개)")
                edited_sell = st.data_editor(st.session_state.grid_sell_list, num_rows="dynamic", key="sell_editor", use_container_width=True)
            with g_c2:
                st.markdown(f"#### 🔴 매수 리스트 (아래로 {len(st.session_state.grid_buy_list)}개)")
                edited_buy = st.data_editor(st.session_state.grid_buy_list, num_rows="dynamic", key="buy_editor", use_container_width=True)
        elif has_sell:
            st.markdown(f"#### 🔵 매도 리스트 (위로 {len(st.session_state.grid_sell_list)}개)")
            edited_sell = st.data_editor(st.session_state.grid_sell_list, num_rows="dynamic", key="sell_editor_only", use_container_width=True)
            edited_buy = []
        elif has_buy:
            st.markdown(f"#### 🔴 매수 리스트 (아래로 {len(st.session_state.grid_buy_list)}개)")
            edited_buy = st.data_editor(st.session_state.grid_buy_list, num_rows="dynamic", key="buy_editor_only", use_container_width=True)
            edited_sell = []
            
        total_orders = len(edited_sell) + len(edited_buy)
        if total_orders > 0:
            if not st.session_state.get("confirm_batch_order", False):
                if st.button(f"🚀 일괄 주문 실행 (총 {total_orders}건)", type="primary", use_container_width=True):
                    st.session_state.confirm_batch_order = True
                    st.rerun()
                    
            if st.session_state.get("confirm_batch_order", False):
                st.warning("⚠️ 정말로 이대로 거래소에 주문을 전송하시겠습니까? (실제 자산이 매매됩니다.)")
                c1, c2 = st.columns(2)
                
                with c1:
                    if st.button("✅ 네, 주문 전송합니다.", type="primary", use_container_width=True):
                        payload_orders = []
                        for row in edited_sell:
                            qty = row.get("수량")
                            price = row.get("가격")
                            if pd.notna(qty) and pd.notna(price) and float(qty) > 0 and float(price) > 0:
                                payload_orders.append({"side": "sell", "quantity": float(qty), "price": float(price)})
                        for row in edited_buy:
                            qty = row.get("수량")
                            price = row.get("가격")
                            if pd.notna(qty) and pd.notna(price) and float(qty) > 0 and float(price) > 0:
                                payload_orders.append({"side": "buy", "quantity": float(qty), "price": float(price)})
                            
                        if len(payload_orders) == 0:
                            st.error("전송할 유효한 주문이 없습니다. (수량이나 가격이 비어있거나 0 이하입니다.)")
                        else:
                            try:
                                res = requests.post(f"{API_URL}/order/batch", json={"orders": payload_orders}, timeout=15)
                                if res.status_code == 200:
                                    data = res.json()
                                    results = data.get("results", [])
                                    
                                    success_count = sum(1 for r in results if isinstance(r, dict) and r.get("status") == "success")
                                    fail_count = len(results) - success_count
                                    
                                    success_msgs = []
                                    fail_msgs = []
                                    
                                    for idx, r in enumerate(results):
                                        side = "매수" if payload_orders[idx]["side"] == "buy" else "매도"
                                        prc = payload_orders[idx]["price"]
                                        if isinstance(r, dict) and r.get("status") == "success":
                                            success_msgs.append(f"✅ {side} {prc}원: 성공")
                                        else:
                                            fail_reason = r.get('message', '알 수 없음') if isinstance(r, dict) else str(r)
                                            fail_msgs.append(f"❌ {side} {prc}원 실패 원인: {fail_reason}")
                                    
                                    if len(success_msgs) > 0:
                                        if len(fail_msgs) == 0:
                                            st.success("모든 일괄 주문이 성공적으로 전송되었습니다!\n\n" + "\n".join(success_msgs))
                                        else:
                                            st.success(f"{len(success_msgs)}건 주문 성공:\n\n" + "\n".join(success_msgs))
                                            
                                    if len(fail_msgs) > 0:
                                        st.error(f"{len(fail_msgs)}건 주문 실패:\n\n" + "\n".join(fail_msgs))
                                    
                                    if fail_count == 0 and success_count > 0:
                                        st.session_state.show_grid_preview = False
                                        st.session_state.confirm_batch_order = False
                                        import time; time.sleep(2); st.rerun()
                                else:
                                    st.error(f"서버 오류: HTTP {res.status_code}")
                            except Exception as e:
                                st.error(f"서버 통신 실패: {e}")
                                
                with c2:
                    if st.button("❌ 취소", use_container_width=True):
                        st.session_state.confirm_batch_order = False
                        st.rerun()
                
        st.divider()
    
    # 2. 탭 콘텐츠
    tab1, tab2, tab3 = st.tabs(["📊 진입 거래망 현황", "📜 거래 내역", "⚙️ 시스템 로그"])
    
    with tab1:
        st.subheader("🕸️ 진입 대기 중인 매수/매도 그리드")
        all_positions = status_data.get('positions', [])
        
        sym = current_cfg.get("symbol", "ONDO" if current_exchange == "bithumb" else "042660")
        positions = [p for p in all_positions if p.get("symbol") == sym]
        
        if positions:
            view_mode = st.radio("보기 방식", ["📊 호가창 뷰 (현재가 중심 정렬)", "📉 시각화 차트 뷰 (분포)", "📝 일반 목록 뷰 (접수순)"], horizontal=True)
            df_positions = pd.DataFrame(positions)
            
            if 'price' not in df_positions.columns and 'avg_price' in df_positions.columns:
                df_positions['price'] = df_positions['avg_price']
            if 'side' not in df_positions.columns and 'price' in df_positions.columns:
                df_positions['side'] = df_positions['price'].apply(lambda x: "매도" if x > 50000 else "매수")
            
            if view_mode == "📊 호가창 뷰 (현재가 중심 정렬)":
                sell_orders = df_positions[df_positions['side'] == '매도'].sort_values('price', ascending=False)
                buy_orders = df_positions[df_positions['side'] == '매수'].sort_values('price', ascending=False)
                def highlight_side(row):
                    if row['side'] == '매도': return ['background-color: rgba(50, 50, 200, 0.2)'] * len(row)
                    elif row['side'] == '매수': return ['background-color: rgba(200, 50, 50, 0.2)'] * len(row)
                    return [''] * len(row)
                combined_df = pd.concat([sell_orders, buy_orders])
                display_df = combined_df[['side', 'price', 'quantity', 'id']].copy()
                display_df.columns = ['방향', '주문 가격', '수량', 'ID']
                styled_df = display_df.style.apply(highlight_side, axis=1).format({'주문 가격': '{:,.0f}', '수량': '{:,.0f}'})
                st.dataframe(styled_df, use_container_width=True, hide_index=True)
            elif view_mode == "📉 시각화 차트 뷰 (분포)":
                chart_data = df_positions[['price', 'quantity', 'side']].copy()
                chart_data['color'] = chart_data['side'].map({'매도': '#4A90E2', '매수': '#E24A4A'})
                st.scatter_chart(data=chart_data, x='price', y='quantity', color='color', use_container_width=True)
            else:
                st.dataframe(df_positions, width="stretch")
        else:
            st.write("활성화된 거래중 포지션이 없습니다.")

    with tab2:
        st.subheader("최근 체결 내역")
        st.write("알고리즘 가동 시 실시간으로 기록됩니다.")
        mock_trades = pd.DataFrame(columns=["시간", "종류", "가격(원)", "수량", "상태"])
        st.dataframe(mock_trades, width="stretch")

    with tab3:
        st.subheader("엔진 구동 상태")
        is_running_main = status_data.get("running", False)
        st.write(f"**코어 루프 상태:** {'🟢 가동 중' if is_running_main else '🔴 정지됨'}")
        st.write(f"**적용된 거래소:** {curr_ex.upper()}")
        st.write(f"**타겟 종목:** {curr_cfg.get('symbol', 'N/A')}")
        
        mode_str = ""
        if curr_paper: mode_str = "🧪 테스트 모드 (미전송)"
        elif curr_mock: mode_str = "🟢 KIS 모의투자"
        else: mode_str = "🔴 실전 투자"
        st.write(f"**투자 모드:** {mode_str}")

else:
    st.error("백엔드 서버(FastAPI)와 통신할 수 없습니다. 엔진 가동 상태를 확인하십시오.")

st.divider()

# 🎛️ 매매 알고리즘 파라미터 제어
st.subheader("🎛️ 매매 알고리즘 파라미터 (그리드 설정)")

cfg = status_data.get("config", {}) if status_data else {}
current_exchange = cfg.get("exchange", "bithumb")
ex_cfg = cfg.get(current_exchange, {})

is_kis = current_exchange == "kis"

default_grid = 2000 if is_kis else 10
default_profit = 2000 if is_kis else 10
default_qty = 10 if is_kis else 1000
step_val = 50 if is_kis else 1

current_market_price = 0
try:
    sym = cfg.get("symbol", "ONDO" if current_exchange == "bithumb" else "042660")
    p_res = requests.get(f"{API_URL}/price?exchange={current_exchange}&symbol={sym}", timeout=2)
    if p_res.status_code == 200:
        current_market_price = p_res.json().get("price", 0)
except:
    pass
    
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

if st.button("📝 설정 확인 (그리드 생성)", width="stretch"):
    sell_list = []
    buy_list = []
    bp = base_price if base_price > 0 else current_market_price
    
    if grid_direction in ["매도만", "매수/매도 모두"]:
        for i in range(1, sell_count + 1):
            if is_kis:
                s_price = bp + (take_profit * i)
                s_price = (s_price // 1000) * 1000 + 900
            else:
                s_price = bp + (take_profit * i)
                s_price = (s_price // 10) * 10 + 9
            sell_list.append({"선택": True, "가격": int(s_price), "수량": int(order_quantity)})
            
    if grid_direction in ["매수만", "매수/매도 모두"]:
        for i in range(1, buy_count + 1):
            if is_kis:
                b_price = bp - (grid_interval * i)
                b_price = (b_price // 1000) * 1000 + 100
            else:
                b_price = bp - (grid_interval * i)
                b_price = (b_price // 10) * 10 + 1
            buy_list.append({"선택": True, "가격": int(b_price), "수량": int(order_quantity)})
        
    st.session_state.grid_sell_list = sell_list
    st.session_state.grid_buy_list = buy_list
    st.session_state.show_grid_preview = True

st.markdown("---")
if st.button("💾 파라미터 저장", width="stretch"):
    try:
        res = requests.post(f"{API_URL}/config", json={
            current_exchange: {
                "base_price": base_price,
                "grid_interval": grid_interval,
                "take_profit": take_profit,
                "order_quantity": order_quantity
            }
        }, timeout=5)
        if res.status_code == 200:
            st.success(f"[{current_exchange.upper()}] 파라미터 저장 완료")
            import time; time.sleep(0.3); st.rerun()
        else:
            st.error("저장 실패")
    except Exception as e:
        st.error(f"서버 통신 실패: {e}")
'''

with codecs.open('d:/aiworkspace/app/dashboard.py', 'w', encoding='utf-8') as f:
    f.write(dashboard_code)
print('Full recovery successful!')
