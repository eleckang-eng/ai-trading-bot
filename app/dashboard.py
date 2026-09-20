import streamlit as st
import requests
import pandas as pd
import time

# =============================================================================
# [대규모 UX/UI 개선 히스토리 및 참고사항 - 2026-09-20]
# 1. 모바일 레이아웃 강어:
#    - Streamlit 기본 속성으로 인해 창 폭이 줄어들면 st.columns()가 1열(세로)로 풀리는 현상 발생.
#    - 이를 원천 방어하기 위해 <style> 내부에 flex-direction: row !important; 와 
#      flex-wrap: nowrap !important; CSS를 추가. 어떠한 경우에도 50% 너비 2열로 고정됨.
# 2. 그리드 설정창 자동 접힘 (Expander):
#    - 주문 생성 탭(tab_order)의 파라미터 입력부 전체를 st.expander()로 감쌈.
#    - '균등/계단식 그리드 생성' 버튼 클릭 시 st.session_state.show_grid_preview가 True로 변경되며,
#      expanded=not show_grid_preview 속성에 의해 설정창이 즉시 접히고(팝업아웃 효과) 표가 화면을 채움.
# =============================================================================

# 페이지 설정
st.set_page_config(page_title="AI 핑퐁 봇", page_icon="📈", layout="wide", initial_sidebar_state="auto")

# 모바일 환경에서 화면 핀치 줌(확대/축소)을 허용하는 JS 주입
import streamlit.components.v1 as components
components.html('''
<script>
    const meta = window.parent.document.querySelector('meta[name="viewport"]');
    if (meta) {
        meta.setAttribute("content", "width=device-width, initial-scale=1.0, maximum-scale=5.0, user-scalable=yes");
    }
</script>
''', height=0)

API_URL = "http://127.0.0.1:8000"

st.markdown("""

<style>

        /* 
         * [CRITICAL] 모바일 반응형 레이아웃 잘림 방지 (2열 강제 유지)
         * 
         * 1. flex-wrap: nowrap 
         *    - 모바일에서 좁은 폭으로 인해 2열이 1열로 강제 줄바꿈(Stack)되는 것을 막고, 항상 2열(또는 4열)을 유지합니다.
         * 2. justify-content: center 제거 (중요)
         *    - 과거에는 center 정렬이 있었으나, 내부 내용물이 화면 폭보다 클 경우 
         *      가운데 정렬로 인해 뷰포트 왼쪽(음수 좌표)으로 밀려나버려 스크롤조차 불가능하게 좌측 화면이 잘리는 치명적 버그가 있었습니다.
         * 3. flex: 1 1 auto 및 min-width: 0 (가장 중요)
         *    - 기존에는 0%를 써서 무조건 1:1:1 로 나누었더니 상단 제목(모드)처럼 긴 글씨가 들어가는 곳이 너무 좁아져 두 줄로 꺾이는 문제가 생겼습니다.
         *    - 이를 auto로 변경하면 내용물 길이에 비례해서 공간을 영리하게 나누어 가지되, min-width: 0 덕분에 화면 밖으로 절대 튀어나가지는 않습니다.
         */
        div[data-testid="stHorizontalBlock"] {
            flex-direction: row !important;
            flex-wrap: nowrap !important;
            gap: 0.5rem !important;
        }
        div[data-testid="stHorizontalBlock"] > div {
            flex: 1 1 auto !important; 
            min-width: 0 !important; 
            padding: 0 0.2rem !important;
            display: block !important;
        }
    /* 윈도우/모바일 공통: 상단 여백 확보(제목 가림 방지) 및 좌우 여백 축소 */
    .block-container {
        padding-top: 5rem !important; /* 가림 현상 완벽 방지를 위해 여백을 5rem으로 대폭 늘림 */
        padding-bottom: 1rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
        max-width: 1400px !important;
    }
    
    /* 각 요소들 간의 상하 간격 줄이기 */
    div[data-testid="stVerticalBlock"] > div {
        margin-bottom: -0.5rem !important;
    }
    
    /* 탭 메뉴 상하 간격 축소 */
    button[data-baseweb="tab"] {
        padding-top: 0.2rem !important;
        padding-bottom: 0.2rem !important;
        font-size: 1.1rem !important;
    }
    
    /* 숫자/메트릭 폰트 및 여백 축소 */
    div[data-testid="metric-container"] {
        padding-top: 0 !important;
        padding-bottom: 0 !important;
    }
    
    /* 데이터프레임 높이 튜닝 */
    div[data-testid="stDataFrame"] {
        margin-top: -0.5rem !important;
    }

    /* 데스크톱에서만 사이드바 넓게 유지 */
    @media (min-width: 768px) {
        [data-testid="stSidebar"] { min-width: 440px !important; max-width: 480px !important; }
    }
    /* 모바일 웹뷰(앱) 최적화: 불필요한 Streamlit 기본 헤더/푸터 및 여백 제거 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 1.5rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }
    /* 모바일에서 제목과 Metric(수치) 폰트 크기 대폭 줄이기 (줄바꿈 방지) */
    @media (max-width: 768px) {
        h1 { font-size: 1.5rem !important; }
        h2 { font-size: 1.25rem !important; }
        h3 { font-size: 1.1rem !important; }
        
        [data-testid="stMetricLabel"] p {
            font-size: 0.9rem !important;
            white-space: nowrap !important;
            overflow: hidden !important;
            text-overflow: ellipsis !important;
        }
        [data-testid="stMetricValue"] { font-size: 1.2rem !important; }
        
        /* 폰에서 100% 팽창 억제 및 강제 반반 분배 */
        [data-testid="column"] {
            min-width: 0 !important;
            flex: 1 1 0% !important;
            padding: 0 !important;
            gap: 0 !important;
        }
        
        /* 탭 라벨 폰트 크기 조정 */
        button[data-baseweb="tab"] p {
            font-size: 0.9rem !important;
        }
    }
</style>
""", unsafe_allow_html=True)

def fetch_status():
    try:
        r = requests.get(f"{API_URL}/status", timeout=1)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return None

def current_sym(cfg):
    ex = cfg.get("exchange", "kis")
    return cfg.get("symbol", "ONDO" if ex == "bithumb" else "042660")

status_data = fetch_status()

if not status_data:
    st.error("백엔드 서버(FastAPI)에 연결할 수 없습니다.")
    st.info("터미널에서 `python main.py` 를 실행하여 서버를 시작해 주세요.")
    st.stop()

current_cfg = status_data.get("config", {})
curr_ex     = current_cfg.get("exchange", "kis")
curr_mock   = current_cfg.get("mock_mode", True)
curr_paper  = current_cfg.get("paper_trading", False)
# [UI 테스트용] 한국투자(모의) 모드일 때 포지션이 비어있으면 강제로 더미 데이터를 주입합니다.
if curr_ex == "kis" and curr_mock and not curr_paper:
    if not status_data.get("positions"):
        dummy_pos = []
        bp = 83500
        # 매도 20건 (현재가 위)
        for i in range(1, 21):
            if (100+i) not in st.session_state.get("dummy_cancelled_ids", []):
                dummy_pos.append({"id": 100+i, "side": "sell", "avg_price": bp + (i * 2000), "quantity": 10 + (i*2), "symbol": "042660"})
        # 매수 20건 (현재가 아래)
        for i in range(1, 21):
            if (200+i) not in st.session_state.get("dummy_cancelled_ids", []):
                dummy_pos.append({"id": 200+i, "side": "buy", "avg_price": bp - (i * 2000), "quantity": 10 + (i*2), "symbol": "042660"})
        status_data["positions"] = dummy_pos

ex_name = "한국투자" if curr_ex == "kis" else "빗썸"
if curr_paper:
    mode_name = "테스트"
    mode_badge = "🧪 테스트 (미전송)"
elif curr_mock:
    mode_name = "모의 계좌"
    mode_badge = "🟢 모의 투자"
else:
    mode_name = "실전"
    mode_badge = "🔴 실전 투자"

# ── 백엔드 긴급 경보(알림) 표시 ────────────────────────
alert_msg = status_data.get("state", {}).get("critical_alert")
if alert_msg:
    st.error(f"🚨 **[시스템 긴급 경보]** {alert_msg}")
    st.write("")

title_str = f"📈 {ex_name} ({mode_name})"

# 상단 헤더 메뉴바(Deploy 등)에 제목이 가려지는 것을 방지하기 위해 강제로 빈 줄 1칸 확보
st.markdown("<br>", unsafe_allow_html=True) 

c_title, c_sync = st.columns([7, 3])
with c_title:
    st.markdown(f"### {title_str}")
with c_sync:
    if st.button("🔄 잔고갱신", use_container_width=True):
        try:
            r = requests.post(f"{API_URL}/refresh_balance", timeout=15)
            if r.status_code == 200 and r.json().get("status") == "success":
                st.session_state.sync_msg = "✅ 잔고 동기화가 성공적으로 완료되었습니다."
            else:
                st.session_state.sync_msg = "❌ 잔고 갱신 실패 (거래소 API 에러 등)"
        except:
            st.session_state.sync_msg = "❌ 백엔드 통신 실패"
        st.rerun()

if st.session_state.get("sync_msg"):
    msg = st.session_state.sync_msg
    color = "#155724" if "✅" in msg else "#721c24"
    bg = "#d4edda" if "✅" in msg else "#f8d7da"
    border = "#c3e6cb" if "✅" in msg else "#f5c6cb"
    
    st.markdown(f"""
    <div class="fade-out-msg" style="padding:1rem; margin-bottom:1rem; border-radius:0.5rem; color:{color}; background-color:{bg}; border: 1px solid {border}; font-weight:bold;">
        {msg}
    </div>
    <style>
    .fade-out-msg {{
        animation: fadeOutMsg 5s forwards;
    }}
    @keyframes fadeOutMsg {{
        0% {{ opacity: 1; max-height: 100px; padding: 1rem; margin-bottom: 1rem; border-width: 1px; }}
        80% {{ opacity: 1; max-height: 100px; padding: 1rem; margin-bottom: 1rem; border-width: 1px; }}
        100% {{ opacity: 0; max-height: 0px; padding: 0px; margin-bottom: 0px; border-width: 0px; overflow: hidden; }}
    }}
    </style>
    """, unsafe_allow_html=True)
    st.session_state.sync_msg = None

# ══════════════════════════════════════════════════════
# 사이드바
# ══════════════════════════════════════════════════════
tab_dash, tab_order, tab_history, tab_settings = st.tabs(["📊 현황", "🛒 주문 생성", "💸 거래 내역", "⚙️ 설정"])

with tab_settings:
    st.header("⚙️ 시스템 제어")

    # ── 거래소 / 모드 선택 ───────────────────────────
    default_idx = 3
    if curr_ex == "kis":
        if curr_paper:  default_idx = 3
        elif curr_mock: default_idx = 2
        else:           default_idx = 0
    else:
        default_idx = 4 if curr_paper else 1

    exchange_choice = st.selectbox("거래소 및 투자 모드", [
        "🔴 한국투자증권 (실전)",
        "🔴 빗썸 (실전)",
        "🟢 한국투자증권 (모의 계좌)",
        "🧪 한국투자증권 (테스트)",
        "🧪 빗썸 (테스트)"
    ], index=default_idx)

    if st.button("🔄 모드 적용", use_container_width=True):
        if False:
            st.warning("구분선은 선택할 수 없습니다.")
        else:
            new_exchange     = "bithumb" if "빗썸" in exchange_choice else "kis"
            new_symbol       = "ONDO"    if new_exchange == "bithumb"  else "042660"
            is_mock_account  = "모의 계좌" in exchange_choice
            is_paper_trading = "테스트"    in exchange_choice

            # 모드가 변경되었는지 감지
            new_mode_str = f"{new_exchange}_{is_mock_account}_{is_paper_trading}"
            if st.session_state.get("prev_mode_str") != new_mode_str:
                st.session_state.prev_mode_str = new_mode_str
                # 모드 변경 시 서버에 모드 적용 후 1회 즉시 동기화 요청
                try:
                    # 1. 현재가 조회 (서버 시작시/모드 변경시 기준가 초기화 용도)
                    p_res = requests.get(f"{API_URL}/price?exchange={new_exchange}&symbol={new_symbol}", timeout=5)
                    fetched_p = 0
                    if p_res.status_code == 200 and p_res.json().get("price", 0) > 0:
                        fetched_p = int(p_res.json().get("price"))
                        st.session_state.manual_price = fetched_p
                    
                    config_payload = {
                        "exchange":      new_exchange,
                        "symbol":        new_symbol,
                        "mock_mode":     is_mock_account,
                        "paper_trading": is_paper_trading,
                    }
                    if fetched_p > 0:
                        # 기존 파라미터를 유지하되 기준가만 덮어씌우려면 서버 측 로직이 dict merge를 하므로 이렇게 넘깁니다
                        config_payload[new_exchange] = {"base_price": fetched_p}

                    requests.post(f"{API_URL}/config", json=config_payload, timeout=5)
                    requests.post(f"{API_URL}/refresh_balance", timeout=10)
                    requests.post(f"{API_URL}/order/sync", timeout=10)
                except Exception as e:
                    pass
                st.session_state.mode_changed_msg = f"✅ {exchange_choice} 모드로 변경되었습니다."
                st.rerun()

            try:
                requests.post(f"{API_URL}/config", json={
                    "exchange":      new_exchange,
                    "symbol":        new_symbol,
                    "mock_mode":     is_mock_account,
                    "paper_trading": is_paper_trading,
                }, timeout=5)
                st.session_state.mode_changed_msg = f"✅ 이미 {exchange_choice} 모드입니다. 설정을 갱신했습니다."
                st.rerun()
            except Exception as e:
                st.error(f"서버 통신 실패: {e}")

    # 모드 변경 완료 메시지 (다음 클릭 시 자동 사라짐)
    if st.session_state.get("mode_changed_msg"):
        st.success(st.session_state.mode_changed_msg)
        st.session_state.mode_changed_msg = None

    pass

    pass

    # 시스템 공통 설정과 합치기 위해 삭제됨
    # ── 매매 알고리즘 파라미터 ──────────────────────
with tab_order:
    with st.expander("⚙️ 그리드 파라미터 설정 (터치하여 열기/닫기)", expanded=not st.session_state.get("show_grid_preview", False)):
        st.subheader("🎛️ 매매 알고리즘 파라미터 (그리드 설정)")
        cfg              = status_data.get("config", {}) if status_data else {}
        current_exchange = cfg.get("exchange", "bithumb")
        ex_cfg           = cfg.get(current_exchange, {})
        is_kis           = (current_exchange == "kis")
        default_grid     = 2000 if is_kis else 10
        default_profit   = 2000 if is_kis else 10
        default_qty      = 10   if is_kis else 1000
        step_val         = 50   if is_kis else 1

        # 1. 서버조회 (버튼 1개)
        if st.button("🔄 서버조회 (현재가 & 주문 동기화)", use_container_width=True, help="거래소 미체결 내역과 현재가를 최신으로 동기화합니다."):
            try:
                # 현재가 조회
                sym   = current_sym(cfg)
                p_res = requests.get(f"{API_URL}/price?exchange={current_exchange}&symbol={sym}", timeout=5)
                if p_res.status_code == 200:
                    p = p_res.json().get("price", 0)
                    if p > 0:
                        st.session_state.manual_price = int(p)
            
                # 미체결 주문 동기화
                s_res = requests.post(f"{API_URL}/order/sync", timeout=10)
                if s_res.status_code == 200:
                    st.success(s_res.json().get("message", "동기화 완료"))
                st.rerun()
            except Exception as e:
                st.error(f"서버조회 실패: {e}")

        if True: # 내부 중복 expander 제거됨
            key_suffix = f"_{current_exchange}_{cfg.get('mock_mode', True)}"

            # 2. 매도 간격 / 매도주문 수량 (입력창 가로 2개)
            col_sell_1, col_sell_2 = st.columns(2)
            with col_sell_1:
                take_profit = st.number_input("매도 간격 (수익폭)", min_value=1, value=int(ex_cfg.get("take_profit", default_profit)), step=step_val, key=f"tp{key_suffix}")
            with col_sell_2:
                sell_count  = st.number_input("매도주문 개수", min_value=1, max_value=50, value=10, step=1, key=f"sc{key_suffix}")

            # 3. 기준가 / 1회 매수 수량 (입력창 가로 2개)
            cached_price = st.session_state.get("manual_price", 0)
            base_price_val = float(ex_cfg.get("base_price", 0) or cached_price)
        
            col_base_1, col_base_2 = st.columns(2)
            with col_base_1:
                base_price = st.number_input("기준가", min_value=0.0, value=base_price_val, step=float(step_val), help="0 입력 시 현재가로 자동 적용", key=f"bp{key_suffix}")
            with col_base_2:
                order_quantity = st.number_input("1회 매수 수량", min_value=1, value=int(ex_cfg.get("order_quantity", default_qty)), step=1, key=f"oq{key_suffix}")

            # 4. 매수 간격 / 매수주문 수량 (입력창 가로 2개)
            col_buy_1, col_buy_2 = st.columns(2)
            with col_buy_1:
                grid_interval = st.number_input("매수 간격 (하락폭)", min_value=1, value=int(ex_cfg.get("grid_interval", default_grid)), step=step_val, key=f"gi{key_suffix}")
            with col_buy_2:
                buy_count     = st.number_input("매수주문 개수", min_value=1, max_value=50, value=10, step=1, key=f"bc{key_suffix}")

            # 5. 주문 방향 (라디오 버튼 3개)
            grid_direction = st.radio("주문 방향", ["매수/매도 모두", "매수만", "매도만"], index=0, horizontal=True, key=f"gd{key_suffix}")

            # ── 그리드 생성 헬퍼 ──
            def _calc_base_price():
                if base_price > 0: return base_price
                if cached_price > 0: return cached_price
                return 80000 if is_kis else 1000

            def _generate_grid(bp, qty):
                sell_list, buy_list = [], []
                if grid_direction in ["매도만", "매수/매도 모두"]:
                    for i in range(1, int(sell_count) + 1):
                        s_price = bp + (take_profit * i)
                        s_price = (s_price // 1000) * 1000 + 900 if is_kis else (s_price // 10) * 10 + 9
                        sell_list.append({"선택": True, "가격": int(s_price), "수량": int(qty)})
                if grid_direction in ["매수만", "매수/매도 모두"]:
                    for i in range(1, int(buy_count) + 1):
                        b_price = bp - (grid_interval * i)
                        if b_price <= 0: break
                        b_price = (b_price // 1000) * 1000 + 100 if is_kis else (b_price // 10) * 10 + 1
                        buy_list.append({"선택": True, "가격": int(b_price), "수량": int(qty)})
                return sell_list, buy_list

            # 6. 균등그리드생성 (버튼 1개)
            if st.button("📝 균등 그리드 생성", use_container_width=True):
                bp = _calc_base_price()
                sell_list, buy_list = _generate_grid(bp, order_quantity)
                st.session_state.grid_sell_list = sell_list
                st.session_state.grid_buy_list = buy_list
                st.session_state.show_grid_preview = True
                st.session_state.confirm_batch_order = False
                st.rerun()

            # ── 계단형 그리드 생성 ─────────────────────────
            st.caption("계단형: 지정한 방향에만 수량을 증액하는 그리드")
            stair_c1, stair_c2 = st.columns(2)
            with stair_c1:
                stair_steps = st.number_input("증액 계단 수량", min_value=1, max_value=10, value=3, step=1, help="몇 단계마다 수량이 증액되는지", key=f"ss{key_suffix}")
            with stair_c2:
                stair_add_qty = st.number_input("증액 수량", min_value=1, value=5 if is_kis else 500, step=1, help="계단 한 단계당 추가되는 수량", key=f"saq{key_suffix}")

            stair_direction = st.radio("계단 적용 방향", ["매수매도계단", "매수계단", "매도계단"], index=0, horizontal=True, key=f"sd{key_suffix}")

            # 8. 계단형그리드생성 (버튼 1개)
            if st.button("📈 계단형 그리드 생성", use_container_width=True):
                bp = _calc_base_price()
                sell_list, buy_list = [], []
                if grid_direction in ["매도만", "매수/매도 모두"]:
                    for i in range(1, int(sell_count) + 1):
                        s_price = bp + (take_profit * i)
                        s_price = (s_price // 1000) * 1000 + 900 if is_kis else (s_price // 10) * 10 + 9
                    
                        if stair_direction in ["매수매도계단", "매도계단"]:
                            stair_level = (i - 1) // int(stair_steps)
                            qty = int(order_quantity) + (stair_level * int(stair_add_qty))
                        else:
                            qty = int(order_quantity)
                        
                        sell_list.append({"선택": True, "가격": int(s_price), "수량": qty})
                    
                if grid_direction in ["매수만", "매수/매도 모두"]:
                    for i in range(1, int(buy_count) + 1):
                        b_price = bp - (grid_interval * i)
                        if b_price <= 0: break
                        b_price = (b_price // 1000) * 1000 + 100 if is_kis else (b_price // 10) * 10 + 1
                    
                        if stair_direction in ["매수매도계단", "매수계단"]:
                            stair_level = (i - 1) // int(stair_steps)
                            qty = int(order_quantity) + (stair_level * int(stair_add_qty))
                        else:
                            qty = int(order_quantity)
                        
                        buy_list.append({"선택": True, "가격": int(b_price), "수량": qty})

                st.session_state.grid_sell_list = sell_list
                st.session_state.grid_buy_list = buy_list
                st.session_state.show_grid_preview = True
                st.session_state.confirm_batch_order = False
                st.rerun()

            st.write("")
            st.write("")
            
            # 12. 파라미터 저장 / 초기화 (버튼 2개)
            btn_p1, btn_p2 = st.columns(2)
            with btn_p1:
                if st.button("💾 파라미터 저장", use_container_width=True):
                    st.session_state.confirm_param_save = True
                    st.session_state.confirm_param_reset = False
                    st.rerun()
            with btn_p2:
                if st.button("🔄 파라미터 초기화", use_container_width=True):
                    st.session_state.confirm_param_reset = True
                    st.session_state.confirm_param_save = False
                    st.rerun()
                
            if st.session_state.get("confirm_param_save"):
                st.warning("현재 입력된 파라미터(기준가, 간격, 수량)를 다음 번에도 유지되도록 저장하시겠습니까?")
                conf_p1, conf_p2 = st.columns(2)
                with conf_p1:
                    if st.button("네, 실행합니다", key="yes_param_save", use_container_width=True):
                        try:
                            requests.post(f"{API_URL}/config", json={
                                current_exchange: {
                                    "grid_interval": grid_interval,
                                    "take_profit": take_profit, 
                                    "order_quantity": order_quantity,
                                    "sell_count": sell_count,
                                    "buy_count": buy_count,
                                    "grid_direction": grid_direction,
                                    "stair_steps": stair_steps,
                                    "stair_add_qty": stair_add_qty,
                                    "stair_direction": stair_direction
                                }
                            }, timeout=5)
                            st.session_state.param_result_msg = "그리드 파라미터 기본값으로 저장 완료"
                        except Exception as e:
                            st.session_state.param_result_msg = f"저장 실패: {e}"
                        st.session_state.confirm_param_save = None
                        st.rerun()
                with conf_p2:
                    if st.button("취소", key="no_param_save", use_container_width=True):
                        st.session_state.confirm_param_save = None
                        st.rerun()

            if st.session_state.get("confirm_param_reset"):
                st.warning("그리드 파라미터를 권장 기본값으로 완전 초기화하시겠습니까?")
                conf_r1, conf_r2 = st.columns(2)
                with conf_r1:
                    if st.button("네, 초기화합니다", key="yes_param_reset", use_container_width=True):
                        try:
                            def_grid = 2000 if is_kis else 10
                            def_prof = 2000 if is_kis else 10
                            def_qty  = 10   if is_kis else 1000
                            requests.post(f"{API_URL}/config", json={
                                current_exchange: {
                                    "base_price": 0, 
                                    "grid_interval": def_grid,
                                    "take_profit": def_prof, 
                                    "order_quantity": def_qty,
                                    "sell_count": 10,
                                    "buy_count": 10,
                                    "grid_direction": "매수/매도 모두",
                                    "stair_steps": 3,
                                    "stair_add_qty": 5 if is_kis else 500,
                                    "stair_direction": "매수매도계단"
                                }
                            }, timeout=5)
                            st.session_state.param_result_msg = "그리드 파라미터 완전 초기화 완료"
                        except Exception as e:
                            st.session_state.param_result_msg = f"초기화 실패: {e}"
                        st.session_state.confirm_param_reset = None
                        st.rerun()
                with conf_r2:
                    if st.button("취소", key="no_param_reset", use_container_width=True):
                        st.session_state.confirm_param_reset = None
                        st.rerun()
                        
            if st.session_state.get("param_result_msg"):
                st.success(st.session_state.param_result_msg)
                if st.button("확인", key="ok_param"):
                    st.session_state.param_result_msg = None
                    st.rerun()

with tab_settings:
    # ── 시스템 공통 설정 ──
    st.subheader("⚙️ 시스템 공통 설정")
    
    # 10. 자동동기화 간격
    sync_c1, sync_c2 = st.columns([3, 1], vertical_alignment="bottom")
    with sync_c1:
        auto_sync_interval = st.number_input("자동동기화 간격 (분)", min_value=1, value=int(cfg.get("auto_sync_interval", 1)), step=1)
    with sync_c2:
        if st.button("입력", key="btn_sync", use_container_width=True):
            st.session_state.confirm_sync_change = auto_sync_interval
            st.rerun()
            
    if st.session_state.get("confirm_sync_change"):
        val = st.session_state.confirm_sync_change
        st.warning(f"자동동기화 간격을 **{val}분**으로 변경하시겠습니까?")
        conf_c1, conf_c2 = st.columns(2)
        with conf_c1:
            if st.button("네, 실행합니다", key="yes_sync", use_container_width=True):
                try:
                    requests.post(f"{API_URL}/config", json={"auto_sync_interval": val}, timeout=5)
                    st.session_state.sync_result_msg = f"자동동기화 간격이 {val}분으로 변경되었습니다."
                except Exception as e:
                    st.session_state.sync_result_msg = f"변경 실패: {e}"
                st.session_state.confirm_sync_change = None
                st.rerun()
        with conf_c2:
            if st.button("취소", key="no_sync", use_container_width=True):
                st.session_state.confirm_sync_change = None
                st.rerun()
                
    if st.session_state.get("sync_result_msg"):
        st.success(st.session_state.sync_result_msg)
        if st.button("확인", key="ok_sync"):
            st.session_state.sync_result_msg = None
            st.rerun()

    # 11. 종목 변경
    sym_c1, sym_c2 = st.columns([3, 1], vertical_alignment="bottom")
    with sym_c1:
        symbol_input = st.text_input("종목 변경 (코드/심볼)", value=cfg.get("symbol", "042660" if is_kis else "ONDO"))
    with sym_c2:
        if st.button("입력", key="btn_sym", use_container_width=True):
            st.session_state.confirm_sym_change = symbol_input
            st.rerun()
            
    if st.session_state.get("confirm_sym_change"):
        val = st.session_state.confirm_sym_change
        st.warning(f"적용 종목을 **{val}**(으)로 변경하시겠습니까? (기준가와 그리드를 다시 확인하세요)")
        conf_s1, conf_s2 = st.columns(2)
        with conf_s1:
            if st.button("네, 실행합니다", key="yes_sym", use_container_width=True):
                try:
                    resolved_val = val
                    
                    # 1. 한국투자증권 (국내주식) 한글 이름 변환 로직
                    if current_exchange == "kis" and not val.isdigit():
                        try:
                            import FinanceDataReader as fdr
                            df = fdr.StockListing('KRX')
                            matched = df[df['Name'] == val]
                            if not matched.empty:
                                resolved_val = matched.iloc[0]['Code']
                            else:
                                st.session_state.sym_result_msg = f"❌ 종목 변경 실패: '{val}'(을)를 찾을 수 없습니다."
                                st.session_state.confirm_sym_change = None
                                st.rerun()
                        except Exception as e:
                            st.session_state.sym_result_msg = f"❌ 주식 종목명 검색 실패: {e}"
                            st.session_state.confirm_sym_change = None
                            st.rerun()
                            
                    # 2. 빗썸 (코인) 한글 이름 변환 로직
                    if current_exchange == "bithumb" and any(ord(c) >= 0xAC00 and ord(c) <= 0xD7A3 for c in val):
                        try:
                            # 업비트 API를 활용해 한글 코인명 -> 영문 심볼 매핑 (빗썸에 없는 코인일 수 있으나 뒤에서 가격 검증하므로 안전)
                            upbit_res = requests.get('https://api.upbit.com/v1/market/all')
                            if upbit_res.status_code == 200:
                                name_map = {x['korean_name']: x['market'].split('-')[1] for x in upbit_res.json() if x['market'].startswith('KRW')}
                                # 예외 하드코딩 추가
                                name_map["온도"] = "ONDO"
                                name_map["온도코인"] = "ONDO"
                                if val in name_map:
                                    resolved_val = name_map[val]
                        except:
                            pass
                            
                    # 3. 변경된 resolved_val(코드/심볼)로 가격 조회하여 유효성 최종 검증
                    p_res = requests.get(f"{API_URL}/price?exchange={current_exchange}&symbol={resolved_val}", timeout=5)
                    fetched_p = 0
                    if p_res.status_code == 200:
                        fetched_p = p_res.json().get("price", 0)
                        
                    if fetched_p > 0:
                        config_payload = {
                            "symbol": resolved_val,
                            current_exchange: {"base_price": int(fetched_p)}
                        }
                        requests.post(f"{API_URL}/config", json=config_payload, timeout=5)
                        st.session_state.manual_price = int(fetched_p)
                        st.session_state.sym_result_msg = f"✅ 종목이 {resolved_val}(으)로 변경되었습니다. (현재가 {int(fetched_p)}원으로 자동 반영)"
                    else:
                        st.session_state.sym_result_msg = f"❌ 잘못된 종목이거나 조회할 수 없습니다. (입력:{val} / 해석:{resolved_val})"
                        
                except Exception as e:
                    st.session_state.sym_result_msg = f"❌ 변경 중 서버 오류 발생: {e}"
                st.session_state.confirm_sym_change = None
                st.rerun()
        with conf_s2:
            if st.button("취소", key="no_sym", use_container_width=True):
                st.session_state.confirm_sym_change = None
                st.rerun()
                
    if st.session_state.get("sym_result_msg"):
        st.success(st.session_state.sym_result_msg)
        if st.button("확인", key="ok_sym"):
            st.session_state.sym_result_msg = None
            st.rerun()

    pass

    pass

    # 중복 주문 제거 토글창 추가
    remove_dup = st.toggle("중복주문제거", value=True, help="켜져 있을 때는 중복 주문 자동 제거해서 주문해줌. 꺼져 있을 때는 기존과 동일함")
    st.session_state.remove_dup = remove_dup

    # 파라미터 저장/초기화 블록 삭제됨

    st.write("")
    st.write("")
    
    st.subheader("🤖 시스템 상태")
    col_a, col_b = st.columns(2)
    ex_cfg_disp = status_data.get("config", {}).get(status_data.get("config", {}).get("exchange", "bithumb"), {}) if status_data else {}
    curr_ex_disp = status_data.get("config", {}).get("exchange", "bithumb") if status_data else "bithumb"
    with col_a:
        st.write(f"**상태:** {'🟢 가동 중' if status_data.get('running', False) else '🔴 정지됨'}")
        st.write(f"**거래소:** {curr_ex_disp.upper()}")
        st.write(f"**모드:** {mode_badge}")
    with col_b:
        st.write(f"**기준가:** {ex_cfg_disp.get('base_price', 0):,}")
        st.write(f"**그리드 간격:** {ex_cfg_disp.get('grid_interval', '-')}")
        st.write(f"**익절 간격:** {ex_cfg_disp.get('take_profit', '-')}")
        st.write(f"**1회 주문 수량:** {ex_cfg_disp.get('order_quantity', '-')}")

    st.write("")
    st.write("")

    # ── 봇 제어 ─────────────────────────────────────
    st.subheader("🤖 봇 자동 매매 제어")
    is_running = status_data.get("running", False) if status_data else False
    if is_running:
        st.success("🟢 봇 코어 루프가 실행 중입니다.")
    else:
        st.warning("🔴 봇 코어 루프가 정지되어 있습니다.")

    c_b1, c_b2 = st.columns(2)
    with c_b1:
        if st.button("▶️ 시작", use_container_width=True, disabled=is_running):
            try: requests.post(f"{API_URL}/start", timeout=5); st.rerun()
            except: pass
    with c_b2:
        if st.button("⏹️ 정지", use_container_width=True, disabled=not is_running):
            try: requests.post(f"{API_URL}/stop", timeout=5); st.rerun()
            except: pass

    if st.button("🔄 봇 서버 재시작", use_container_width=True):
        msg_placeholder = st.empty()
        try:
            requests.post(f"{API_URL}/system/restart", timeout=3)
            msg_placeholder.info("재시작 명령 전송. 서버 응답을 대기 중입니다... (최대 10초)")
            
            success = False
            for _ in range(10):
                time.sleep(1.0)
                try:
                    res = requests.get(f"{API_URL}/status", timeout=1)
                    if res.status_code == 200:
                        success = True
                        break
                except:
                    pass
            
            if success:
                msg_placeholder.success("✅ 서버 재시작 완료!")
                time.sleep(1)
                st.rerun()
            else:
                msg_placeholder.error("❌ 서버 재시작 실패 또는 응답 시간 초과")
        except Exception as e:
            msg_placeholder.error("❌ 명령 전송 실패")
# ══════════════════════════════════════════════════════
# 메인 대시보드
# ══════════════════════════════════════════════════════

# ── 메트릭 카드 ──────────────────────────────────────
with tab_dash:
    pass


    # ── 그리드 주문 프리뷰 ────────────────────────────────
with tab_order:
    if st.session_state.get("show_grid_preview", False):
        s_list = st.session_state.get("grid_sell_list", [])
        b_list = st.session_state.get("grid_buy_list",  [])

        with st.container(border=True):
            hd_col1, hd_col2 = st.columns([4, 1])
            with hd_col1:
                st.markdown("#### 📋 그리드 주문 확인 및 편집")
            with hd_col2:
                if st.button("✖ 닫기", use_container_width=True):
                    st.session_state.show_grid_preview   = False
                    st.session_state.confirm_batch_order = False
                    st.rerun()

            # 요약 정보 (선택된 주문 건수는 삭제 요청으로 제거됨)

            has_sell = len(s_list) > 0
            has_buy  = len(b_list) > 0

            from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode, JsCode
            import pandas as pd

            def render_aggrid(list_data, key_suffix, color):
                if not list_data:
                    return []
                df = pd.DataFrame(list_data)
                if "가격" not in df.columns or "수량" not in df.columns:
                    return []
                    
                gb = GridOptionsBuilder.from_dataframe(df[["가격", "수량"]])
                
                # pre-select based on existing "선택" key
                selected_idx = [i for i, r in enumerate(list_data) if r.get("선택", True)]
                
                gb.configure_selection(
                    selection_mode="multiple", 
                    use_checkbox=True, 
                    header_checkbox=True
                )
                
                gb.configure_column("가격", editable=True, cellStyle={'textAlign': 'center'}, width=120, type=["numericColumn"])
                gb.configure_column("수량", editable=True, cellStyle={'textAlign': 'center'}, width=120, type=["numericColumn"])
                
                # 초기에 아무것도 선택되어 있지 않으면(첫 로드 시) 전체 선택 수행
                js_init = """
                function(params) {
                    var selectedCount = params.api.getSelectedNodes().length;
                    if (selectedCount === 0) {
                        params.api.selectAll();
                    }
                }
                """
                
                gb.configure_grid_options(
                    onFirstDataRendered=JsCode(js_init),
                    rowHeight=35, 
                    singleClickEdit=True
                )
                
                # [UI 커스텀] Streamlit 테마의 기본 선택 색상(파란색)을 강제로 덮어씌우기 위한 CSS
                # .ag-theme-streamlit과 ::before 가상 클래스를 명시하여 CSS 우선순위를 높여 강제 적용(!important)합니다.
                custom_css = {
                    ".ag-row-selected": {
                        "background-color": f"{color} !important",
                        "color": "black !important"
                    },
                    ".ag-row-selected::before": {
                        "background-color": f"{color} !important"
                    },
                    ".ag-theme-streamlit .ag-row-selected": {
                        "background-color": f"{color} !important"
                    },
                    ".ag-theme-streamlit .ag-row-selected::before": {
                        "background-color": f"{color} !important"
                    }
                }
                
                resp = AgGrid(
                    df[["가격", "수량"]],
                    gridOptions=gb.build(),
                    update_mode=GridUpdateMode.SELECTION_CHANGED | GridUpdateMode.VALUE_CHANGED,
                    data_return_mode=DataReturnMode.AS_INPUT,
                    fit_columns_on_grid_load=True,
                    allow_unsafe_jscode=True,
                    theme="streamlit",
                    custom_css=custom_css,
                    key=f"grid_{key_suffix}",
                    height=420
                )
                
                # selected_rows가 DataFrame 객체로 반환될 경우를 대비해 항상 dict 리스트로 변환
                sel = resp.get("selected_rows", [])
                if isinstance(sel, pd.DataFrame):
                    return sel.to_dict("records")
                return sel if sel else []

            edited_sell = []
            edited_buy = []

            # [캐싱 방지] Streamlit이 AgGrid 컴포넌트를 캐싱하여 색상 변경이 무시되는 것을 막기 위해
            # key 값에 버전을 명시하여 강제로 새로 그리게 만듭니다. (예: "sell_v3")
            if has_sell and has_buy:
                g_c1, g_c2 = st.columns(2)
                with g_c1:
                    st.markdown("**🔵 매도 리스트**")
                    edited_sell = render_aggrid(s_list, "sell_v3", "#E0F2FE")
                    sell_qty = sum(int(r.get("수량", 0)) for r in edited_sell)
                    st.markdown(f"<p style='font-size: 20px; margin-top: 5px;'><b>총 매도 수량:</b> {sell_qty:,} 주</p>", unsafe_allow_html=True)
                with g_c2:
                    st.markdown("**🔴 매수 리스트**")
                    edited_buy = render_aggrid(b_list, "buy_v3", "#FCE4EC")
                    buy_amt = sum(int(r.get("가격", 0)) * int(r.get("수량", 0)) for r in edited_buy)
                    st.markdown(f"<p style='font-size: 20px; margin-top: 5px;'><b>총 매수 예상금액:</b> {buy_amt:,} 원</p>", unsafe_allow_html=True)
            elif has_sell:
                edited_sell = render_aggrid(s_list, "sell_only_v3", "#E0F2FE")
                sell_qty = sum(int(r.get("수량", 0)) for r in edited_sell)
                st.markdown(f"<p style='font-size: 20px; margin-top: 5px;'><b>총 매도 수량:</b> {sell_qty:,} 주</p>", unsafe_allow_html=True)
            elif has_buy:
                edited_buy = render_aggrid(b_list, "buy_only_v3", "#FCE4EC")
                buy_amt = sum(int(r.get("가격", 0)) * int(r.get("수량", 0)) for r in edited_buy)
                st.markdown(f"<p style='font-size: 20px; margin-top: 5px;'><b>총 매수 예상금액:</b> {buy_amt:,} 원</p>", unsafe_allow_html=True)

    
            # 모바일 환경에서 그리드가 생성되었을 때 사이드바를 자동으로 닫아주는 JS 트릭
            import streamlit.components.v1 as components
            components.html('''
                <script>
                    // 모바일 화면 너비일 때만 작동
                    if(window.parent.innerWidth <= 768) {
                        const closeBtn = window.parent.document.querySelector('[data-testid="stSidebarCollapseButton"]');
                        if(closeBtn) {
                            closeBtn.click();
                        }
                    }
                </script>
            ''', height=0)

            # 체크박스 선택된 것만 카운트
            def _to_list(ed):
                if isinstance(ed, pd.DataFrame):
                    return ed.to_dict("records")
                return ed if ed else []
                
            e_sell_list = _to_list(edited_sell)
            e_buy_list  = _to_list(edited_buy)

            checked_sell = [r for r in e_sell_list if r.get("선택", True) and r.get("가격") and r.get("수량")]
            checked_buy  = [r for r in e_buy_list  if r.get("선택", True) and r.get("가격") and r.get("수량")]
            total_checked = len(checked_sell) + len(checked_buy)

            if total_checked > 0:
                if not st.session_state.get("confirm_batch_order", False):
                    if st.button(f"🚀 일괄 주문 전송 (선택 {total_checked}건)", type="primary", use_container_width=True):
                        st.session_state.confirm_batch_order = True
                        st.rerun()

                if st.session_state.get("confirm_batch_order", False):
                    st.warning("⚠️ 정말로 이대로 거래소에 주문을 전송하시겠습니까? (실제 자산이 매매됩니다.)")

                    # 중복 가격 검사
                    existing_prices = {float(p.get("avg_price", p.get("price", 0))) for p in status_data.get("positions", [])}
                    if st.session_state.get("remove_dup", True):
                        checked_sell = [r for r in checked_sell if float(r.get("가격", 0)) not in existing_prices]
                        checked_buy = [r for r in checked_buy if float(r.get("가격", 0)) not in existing_prices]
                    overlap = sorted({float(r["가격"]) for r in checked_sell + checked_buy if float(r.get("가격", 0)) in existing_prices})
                    if overlap:
                        st.error(f"⚠️ 이미 거래중인 포지션과 가격이 겹칩니다: {', '.join(f'{int(p):,}원' for p in overlap)}")
                        st.warning("중복 주문이 발생할 수 있습니다. 다시 확인해 주세요!")

                    # 현재가 대비 불리한 가격(즉시 체결 위험) 경고
                    curr_price = st.session_state.get("manual_price", 0)
                    if curr_price <= 0 and status_data:
                        curr_price = float(status_data.get("current_price", 0))
                
                    if curr_price > 0:
                        bad_buys = [r for r in checked_buy if float(r["가격"]) > curr_price]
                        bad_sells = [r for r in checked_sell if float(r["가격"]) < curr_price]
                        if bad_buys or bad_sells:
                            st.error("🚨 [주의] 현재가 대비 즉시 체결 위험이 있는 주문이 포함되어 있습니다!")
                            if bad_buys:
                                bad_b_str = ", ".join([f"{int(r['가격']):,}원" for r in bad_buys])
                                st.warning(f"🔴 현재가({int(curr_price):,})보다 비싸게 매수: {bad_b_str}")
                            if bad_sells:
                                bad_s_str = ", ".join([f"{int(r['가격']):,}원" for r in bad_sells])
                                st.warning(f"🔵 현재가({int(curr_price):,})보다 싸게 매도: {bad_s_str}")

                    c1_b, c2_b = st.columns(2)
                    with c1_b:
                        if st.button("✅ 네, 주문 전송합니다.", type="primary", use_container_width=True):
                            payload_orders = [
                                {"side": "sell", "quantity": float(r["수량"]), "price": float(r["가격"])} for r in checked_sell
                            ] + [
                                {"side": "buy",  "quantity": float(r["수량"]), "price": float(r["가격"])} for r in checked_buy
                            ]
                            try:
                                res  = requests.post(f"{API_URL}/order/batch", json={"orders": payload_orders}, timeout=5)
                                data = res.json()
                                if data.get("status") == "accepted":
                                    st.session_state.batch_task_id      = data.get("task_id")
                                    st.session_state.confirm_batch_order = False
                                    st.rerun()
                                else:
                                    st.error(f"주문 접수 실패: {data.get('message', '알 수 없음')}")
                            except Exception as e:
                                st.error(f"서버 통신 실패: {e}")
                    with c2_b:
                        if st.button("❌ 취소", use_container_width=True):
                            st.session_state.confirm_batch_order = False
                            st.rerun()

            # ── 배치 주문 진행 상황 (자동 폴링) ──────────────────
            if st.session_state.get("batch_task_id"):
                task_id = st.session_state.batch_task_id
                try:
                    tr          = requests.get(f"{API_URL}/order/batch/status/{task_id}", timeout=3)
                    task_data   = tr.json()
                    task_status = task_data.get("status", "unknown")
                    progress    = task_data.get("progress", 0)
                    total       = task_data.get("total", 0)
                    success_cnt = task_data.get("success_count", 0)
                    fail_cnt    = task_data.get("fail_count", 0)

                    with st.container(border=True):
                        if task_status in ("queued", "processing"):
                            pct = progress / total if total > 0 else 0
                            st.info(f"⏳ 일괄 주문 처리 중... **{progress}/{total}건** 완료")
                            st.progress(pct, text=f"({progress}/{total}) {int(pct*100)}%")
                            # 자동 폴링: 2초 후 새로고침
                            time.sleep(2)
                            st.rerun()
                        elif task_status == "done":
                            if fail_cnt == 0:
                                st.success(f"✅ 일괄 주문 완료! 총 {total}건 전부 성공했습니다.")
                            else:
                                st.warning(f"⚠️ 일괄 주문 완료: {success_cnt}건 성공 / {fail_cnt}건 실패")
                                error_groups = {}
                                for i, r in enumerate(task_data.get("results", [])):
                                    if isinstance(r, dict) and r.get("status") != "success":
                                        msg = r.get("message", "알 수 없음")
                                        if msg not in error_groups:
                                            error_groups[msg] = []
                                        error_groups[msg].append(i + 1)
                                    
                                for msg, indices in error_groups.items():
                                    idx_str = ", ".join(map(str, indices))
                                    st.error(f"❌ 동일 오류 {len(indices)}건 (주문번호 {idx_str}) ➔ {msg}")
                            if st.button("✔️ 프리뷰 닫기", key="close_batch_status"):
                                st.session_state.batch_task_id = None
                                st.session_state.show_grid_preview = False
                                st.rerun()
                except Exception:
                    pass

        pass

    # ── 수동 주문 결과 메시지 ─────────────────────────────
    if st.session_state.get("manual_order_result"):
        res_info = st.session_state.manual_order_result
        if res_info["ok"]:
            st.success(res_info["msg"])
        else:
            st.error(res_info["msg"])
        if st.button("✔️ 닫기", key="close_manual_result"):
            st.session_state.manual_order_result = None
            st.rerun()

    # ── 수동 주문 제어 ────────────────────────────────────
    col_t1, col_t2 = st.columns([3, 1])
    with col_t1:
        st.subheader("🕹️ 수동 주문 (지정가)")
    with col_t2:
        if st.button("🔎 현재가 조회", use_container_width=True):
            try:
                sym   = current_sym(current_cfg)
                p_res = requests.get(f"{API_URL}/price?exchange={curr_ex}&symbol={sym}", timeout=3)
                if p_res.status_code == 200:
                    p = p_res.json().get("price", 0)
                    if p > 0:
                        st.session_state.manual_price = int(p)
                        st.rerun()
            except: pass
            
        # 1순위: 수동조회 현재가 / 2순위: 서버 실시간 현재가 / 3순위: 설정된 기준가
        display_price = st.session_state.get("manual_price", 0)
        if display_price <= 0 and status_data:
            display_price = float(status_data.get("current_price", 0))
        if display_price <= 0:
            display_price = float(current_cfg.get(curr_ex, {}).get("base_price", 0))
            
        if display_price > 0:
            st.caption(f"현재(기준)가: **{int(display_price):,}** 원")

    # 입력창 2열 (주문 단가, 주문 수량 나란히 배치)
    default_p = int(display_price) if display_price > 0 else (83500 if curr_ex == "kis" else 1000)
    m_step    = 50 if curr_ex == "kis" else 1
    
    c_in1, c_in2 = st.columns(2)
    with c_in1:
        m_price = st.number_input("주문 단가 (원)", min_value=1, value=default_p, step=m_step)
    with c_in2:
        m_qty   = st.number_input("주문 수량", min_value=1, value=10 if curr_ex == "kis" else 1000, step=1)

    st.write("") # 세로 여백 추가
    st.write("") # 세로 여백 추가

    # 매수 매도 (버튼 가운데 정렬을 위해 양옆 여백 컬럼 추가)
    c_space1, c_buy, c_sell, c_space2 = st.columns([1, 2, 2, 1])
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

    st.write("") # 세로 여백 추가
    st.write("") # 세로 여백 추가

    # 수동 주문 확인창
    if st.session_state.get("confirm_manual_order"):
        order    = st.session_state.confirm_manual_order
        side_kor = "🔴 매수" if order["side"] == "buy" else "🔵 매도"
        st.warning(f"정말로 **{side_kor}** 주문을 전송하시겠습니까?  "
                   f"(단가: **{order['price']:,}원** / 수량: **{order['quantity']}주**)")

        existing = {float(p.get("avg_price", 0)) for p in status_data.get("positions", [])
                    if p.get("side", "buy") == order["side"]}
        if float(order["price"]) in existing:
            st.error(f"⚠️ 이미 같은 방향으로 {order['price']:,}원 포지션이 존재합니다!")

        cc1, cc2 = st.columns(2)
        with cc1:
            if st.button("✅ 네, 전송합니다", type="primary", use_container_width=True):
                try:
                    res  = requests.post(f"{API_URL}/order/manual", json=order, timeout=5)
                    data = res.json()
                    ok   = data.get("status") == "success"
                    msg  = data.get("message", "성공" if ok else "오류")
                    st.session_state.manual_order_result = {"ok": ok, "msg": f"{side_kor} — {msg}"}
                except Exception as e:
                    st.session_state.manual_order_result = {"ok": False, "msg": f"요청 실패: {e}"}
                st.session_state.confirm_manual_order = None
                st.rerun()
        with cc2:
            if st.button("❌ 취소", use_container_width=True):
                st.session_state.confirm_manual_order = None
                st.rerun()
                
        st.write("") # 수동 주문 확인창과 아래 버튼 사이의 여백
        st.write("")
    # 미체결 전체 취소 (버튼 1개)
    if st.button("🗑️ 미체결 전체 취소", use_container_width=True, type="primary"):
        st.session_state.confirm_cancel_all  = True
        st.session_state.manual_order_result = None
        st.rerun()

    # 미체결 전체 취소 확인창
    if st.session_state.get("confirm_cancel_all"):
        st.warning("정말로 **모든 미체결 주문을 일괄 취소**하시겠습니까?  \n(DB 포지션 기록도 모두 초기화됩니다.)")
        cc1, cc2 = st.columns(2)
        with cc1:
            if st.button("✅ 전체 취소 실행", type="primary", use_container_width=True):
                try:
                    res = requests.post(f"{API_URL}/order/cancel_all", timeout=5)
                    st.session_state.manual_order_result = {"ok": True, "msg": res.json().get("message", "취소 완료")}
                except Exception as e:
                    st.session_state.manual_order_result = {"ok": False, "msg": f"취소 실패: {e}"}
                st.session_state.confirm_cancel_all = False
                st.rerun()
        with cc2:
            if st.button("❌ 돌아가기", use_container_width=True):
                st.session_state.confirm_cancel_all = False
                st.rerun()

    pass

    # ── 탭 콘텐츠 ─────────────────────────────────────────
with tab_dash:

    pass
    st.subheader("📊 주문 현황")
    positions = status_data.get("positions", [])

    if positions:
        df = pd.DataFrame(positions)
        if "price" not in df.columns and "avg_price" in df.columns:
            df["price"] = df["avg_price"]
        if "side" not in df.columns:
            df["side"] = "buy"
        df["side_kor"] = df["side"].map({"buy": "🔴 매수", "sell": "🔵 매도"}).fillna("🔴 매수")
        df["avg_price"] = pd.to_numeric(df["avg_price"], errors="coerce")
        df["quantity"]  = pd.to_numeric(df["quantity"],  errors="coerce")

        sell_df = df[df["side"] == "sell"].sort_values("avg_price", ascending=False).reset_index(drop=True)
        buy_df  = df[df["side"] == "buy" ].sort_values("avg_price", ascending=False).reset_index(drop=True)
        sell_cnt = len(sell_df)
        buy_cnt  = len(buy_df)

        st.caption(f"🔵 매도 {sell_cnt}건  |  🔴 매수 {buy_cnt}건  |  합계 {sell_cnt + buy_cnt}건")

        view_mode = st.radio("보기 방식",
                             ["📉 차트 뷰", "📊 호가창 정렬", "📝 주문순 정렬"],
                             horizontal=True,
                             label_visibility="collapsed")

        from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
        
        def _render_dash_grid(df_disp, key_suffix, color="#E0F2FE"):
            gb = GridOptionsBuilder.from_dataframe(df_disp)
            gb.configure_selection("multiple", use_checkbox=True)
            gb.configure_column("id", hide=True)
            gb.configure_column("진입 가격", type=["numericColumn", "numberColumnFilter"], valueFormatter="x.toLocaleString() + ' ₩'")
            gb.configure_column("수량", type=["numericColumn", "numberColumnFilter"], valueFormatter="x.toLocaleString() + ' 주'")
            
            custom_css = {
                ".ag-row-selected": { "background-color": f"{color} !important", "color": "black !important" },
                ".ag-row-selected::before": { "background-color": f"{color} !important" },
                ".ag-theme-streamlit .ag-row-selected": { "background-color": f"{color} !important" },
                ".ag-theme-streamlit .ag-row-selected::before": { "background-color": f"{color} !important" }
            }
            
            resp = AgGrid(
                df_disp,
                gridOptions=gb.build(),
                update_mode=GridUpdateMode.SELECTION_CHANGED,
                fit_columns_on_grid_load=True,
                allow_unsafe_jscode=True,
                theme="streamlit",
                custom_css=custom_css,
                key=f"dash_grid_{key_suffix}",
                height=350
            )
            sel = resp.get("selected_rows", [])
            if sel is None:
                return []
            return sel.to_dict("records") if isinstance(sel, pd.DataFrame) else sel

        if view_mode == "📉 차트 뷰":
            selected_pos = []
            import plotly.graph_objects as go

            # 차트뷰에서는 같은 가격대의 수량을 합산하여 깔끔하게 표시
            chart_sell_df = sell_df.groupby("avg_price", as_index=False)["quantity"].sum() if not sell_df.empty else sell_df
            chart_buy_df  = buy_df.groupby("avg_price", as_index=False)["quantity"].sum() if not buy_df.empty else buy_df

            fig = go.Figure()
            # 실시간 서버 현재가를 우선 사용하고, 없으면 수동 설정 가격 사용
            chart_current_price = 0
            if status_data:
                chart_current_price = float(status_data.get("current_price", 0))
            if chart_current_price <= 0:
                chart_current_price = st.session_state.get("manual_price", 0)
            
            # 위에서 못 가져왔다면 API 찔러서 강제로라도 실시간 현재가를 가져오기
            if chart_current_price <= 0:
                try:
                    sym = current_sym(current_cfg)
                    p_res = requests.get(f"{API_URL}/price?exchange={curr_ex}&symbol={sym}", timeout=1)
                    if p_res.status_code == 200:
                        chart_current_price = float(p_res.json().get("price", 0))
                except:
                    pass
                    
            # 3순위: 그래도 0원이면 설정된 기준가(base_price)를 현재가로 표시
            if chart_current_price <= 0:
                chart_current_price = float(current_cfg.get(curr_ex, {}).get("base_price", 0))

            # 매도 그리드 수평선 (파란색, 얇은 점선)
            for _, row in chart_sell_df.iterrows():
                p = int(row["avg_price"])
                q = int(row["quantity"])
                fig.add_shape(type="line", x0=0, x1=1, xref="paper",
                              y0=p, y1=p, line=dict(color="#4a90e2", width=1, dash="dot"))
                fig.add_annotation(x=1.02, xref="paper", y=p, text=f"매도 {p:,} / {q}주",
                                   showarrow=False, font=dict(color="#4a90e2", size=11), xanchor="left")

            # 매수 그리드 수평선 (빨간색, 얇은 점선)
            for _, row in chart_buy_df.iterrows():
                p = int(row["avg_price"])
                q = int(row["quantity"])
                fig.add_shape(type="line", x0=0, x1=1, xref="paper",
                              y0=p, y1=p, line=dict(color="#e05050", width=1, dash="dot"))
                fig.add_annotation(x=1.02, xref="paper", y=p, text=f"매수 {p:,} / {q}주",
                                   showarrow=False, font=dict(color="#e05050", size=11), xanchor="left")

            # 현재가 굵은 수평선 (주황색, 파스텔 배경에 어울리게 변경)
            if chart_current_price > 0:
                fig.add_shape(type="line", x0=0, x1=1, xref="paper",
                              y0=chart_current_price, y1=chart_current_price,
                              line=dict(color="#FF9800", width=3))
                fig.add_annotation(x=0.5, xref="paper", y=chart_current_price,
                                   text=f"━━ 현재가 {int(chart_current_price):,} ━━",
                                   showarrow=False, font=dict(color="#FFFFFF", size=14, family="monospace"),
                                   bgcolor="rgba(255,152,0,0.85)")

            # Y축 범위 설정
            all_prices = list(sell_df["avg_price"]) + list(buy_df["avg_price"])
            if chart_current_price > 0:
                all_prices.append(chart_current_price)
            if all_prices:
                y_min = min(all_prices)
                y_max = max(all_prices)
                margin = (y_max - y_min) * 0.08 if y_max > y_min else 1000
                fig.update_yaxes(range=[y_min - margin, y_max + margin])

            fig.update_layout(
                height=550,
                xaxis=dict(visible=False),
                plot_bgcolor="#F4F6F9",  # 부드러운 파스텔톤 (연한 블루그레이)
                paper_bgcolor="#F4F6F9", # 부드러운 파스텔톤
                font_color="#333333",    # 배경이 밝아졌으므로 폰트는 어둡게
                margin=dict(l=10, r=120, t=10, b=10),  # 여백 최소화 (우측은 글씨를 위해 약간 확보)
            )
            fig.update_yaxes(tickformat=",", gridcolor="rgba(0,0,0,0.05)")
            st.plotly_chart(fig, use_container_width=True)

        elif view_mode in ["📊 호가창 정렬", "📝 주문순 정렬"]:
            st.write("")
            if view_mode == "📝 주문순 정렬":
                s_df = sell_df.sort_values("id") if "id" in sell_df.columns else sell_df
                b_df = buy_df.sort_values("id") if "id" in buy_df.columns else buy_df
            else:
                s_df = sell_df
                b_df = buy_df
                
            col_s, col_b = st.columns(2)
            sel_s = []
            sel_b = []
            
            # 취소 시 표를 완전히 새로 그리기 위한 강제 리프레시 카운터
            grid_refresh_cnt = st.session_state.get("grid_refresh_cnt", 0)
            
            with col_s:
                st.markdown(f"**🔵 매도 포지션 ({len(s_df)}건)**")
                if not s_df.empty:
                    s_disp = s_df[["id", "avg_price", "quantity"]].copy()
                    s_disp.columns = ["id", "진입 가격", "수량"]
                    s_disp.insert(0, "순번", range(1, len(s_disp) + 1))
                    sel_s = _render_dash_grid(s_disp, f"dash_sell_{view_mode}_{grid_refresh_cnt}", "#E0F2FE")
                else:
                    st.info("매도 포지션 없음")
                    
            with col_b:
                st.markdown(f"**🔴 매수 포지션 ({len(b_df)}건)**")
                if not b_df.empty:
                    b_disp = b_df[["id", "avg_price", "quantity"]].copy()
                    b_disp.columns = ["id", "진입 가격", "수량"]
                    b_disp.insert(0, "순번", range(1, len(b_disp) + 1))
                    sel_b = _render_dash_grid(b_disp, f"dash_buy_{view_mode}_{grid_refresh_cnt}", "#FCE4EC")
                else:
                    st.info("매수 포지션 없음")
                    
            selected_pos = (sel_s or []) + (sel_b or [])
            
        # 선택된 항목이 있을 때만 취소 버튼 표시
        # ── 3) 취소 버튼 및 API 호출 로직 ────────────────────────
        # 선택된 항목이 있을 때만 취소 버튼 표시
        if selected_pos:
            st.write("")
            # 버튼 클릭 시 폼 제출처럼 화면이 리로드(rerun)되므로, 상태(session_state)에 메시지를 저장해야 합니다.
            if st.button(f"🗑️ 선택한 {len(selected_pos)}건 주문 취소", use_container_width=True, type="primary"):
                ids_to_cancel = [int(p["id"]) for p in selected_pos if "id" in p]
                try:
                    # 백엔드 서버로 실제 증권사 취소 명령 전송 (5초 타임아웃으로 블로킹 방지)
                    res = requests.post(f"{API_URL}/order/cancel_list", json={"ids": ids_to_cancel}, timeout=5)
                    
                    if res.status_code == 200:
                        res_data = res.json()
                        if res_data.get("status") == "success":
                            st.session_state.dash_cancel_msg = f"✅ {res_data.get('message', '취소 성공')}"
                        else:
                            st.session_state.dash_cancel_msg = f"❌ {res_data.get('message', '취소 실패')}"
                        
                        # [UI 더미 테스트 전용] 백엔드 DB가 비어있어서 계속 똑같은 더미 데이터가 주입되는 현상을 막기 위해
                        # 방금 취소한 가짜 ID들을 기억해두고 렌더링 시 제외시킵니다.
                        if "dummy_cancelled_ids" not in st.session_state:
                            st.session_state.dummy_cancelled_ids = []
                        st.session_state.dummy_cancelled_ids.extend(ids_to_cancel)
                        
                        # 체크박스 선택 잔상 초기화 (위젯 키 변경으로 완전 새 위젯으로 인식시킴)
                        st.session_state.grid_refresh_cnt = st.session_state.get("grid_refresh_cnt", 0) + 1

                        st.rerun()
                    else:
                        st.error(f"❌ {len(ids_to_cancel)}건 주문 취소 처리 실패 (사유: HTTP {res.status_code} - {res.text})")
                except Exception as e:
                    # 증권사 API 오류가 아닌 백엔드 서버 자체가 죽었거나 인터넷이 끊긴 경우
                    st.error(f"❌ {len(ids_to_cancel)}건 주문 취소 처리 실패 (사유: 서버 응답 없음 또는 네트워크 에러 - {e})")
                    
        if st.session_state.get("dash_cancel_msg"):
            if st.session_state.dash_cancel_msg.startswith("❌"):
                st.error(st.session_state.dash_cancel_msg)
            else:
                st.success(st.session_state.dash_cancel_msg)
            if st.button("확인", key="ok_dash_cancel"):
                st.session_state.dash_cancel_msg = None
                st.rerun()
    else:
        st.info("활성화된 포지션이 없습니다.")



    st.write("") # 차트와 간격 띄우기
    
    st.subheader("💰 내 자산 및 수익 현황")
    c1, c2 = st.columns(2)
    is_connected = status_data.get("exchange_connected", False)

    with c1:
        st.metric("총 자산 (예수금)", f"{status_data.get('balance', 0):,} 원",
                  delta="연동 완료" if is_connected else "연동 실패/대기",
                  delta_color="normal" if is_connected else "off")
        st.metric("금일 체결 횟수", f"{status_data.get('trade_count', 0)} 회")
    with c2:
        st.metric("누적 실현 수익", f"{status_data.get('total_profit', 0):,} 원", delta="0.00%")
        st.metric("활성 거래중 노드", f"{len(status_data.get('positions', []))} 개")

# ── 신규 거래 내역 탭 ────────────────────────────────
with tab_history:
    hc1, hc2 = st.columns([0.6, 0.4])
    with hc1:
        st.subheader("💸 실시간 거래 내역")
    with hc2:
        with st.expander("🗑️ 내역 초기화"):
            st.warning("내역 전체 삭제")
            if st.button("영구 삭제", use_container_width=True):
                try:
                    c_res = requests.post(f"{API_URL}/history/clear", timeout=5)
                    if c_res.status_code == 200:
                        st.session_state.history_msg = "✅ 거래 내역이 성공적으로 초기화되었습니다."
                    else:
                        st.session_state.history_msg = f"❌ 초기화 실패: {c_res.text}"
                except Exception as e:
                    st.session_state.history_msg = f"❌ 통신 에러: {e}"
                st.rerun()

    if st.session_state.get("history_msg"):
        if st.session_state.history_msg.startswith("✅"):
            st.success(st.session_state.history_msg)
        else:
            st.error(st.session_state.history_msg)
        if st.button("알림 닫기", key="close_hist_msg"):
            st.session_state.history_msg = None
            st.rerun()
    
    try:
        hist_res = requests.get(f"{API_URL}/history?limit=100", timeout=5)
        if hist_res.status_code == 200:
            history_data = hist_res.json()
            if history_data:
                formatted_history = []
                for h in history_data:
                    side_str = "🔴 매수" if h['side'] == 'buy' else "🔵 매도"
                    status_str = "✅ 체결" if h['status'] == 'filled' else "❌ 취소"
                    formatted_history.append({
                        "시간": h['filled_at'],
                        "종류": side_str,
                        "가격(원)": f"{float(h['price']):,g}",
                        "수량": f"{float(h['quantity']):,g}",
                        "상태": status_str
                    })
                st.dataframe(pd.DataFrame(formatted_history), use_container_width=True, hide_index=True)
            else:
                st.info("아직 기록된 체결 또는 취소 내역이 없습니다.")
        else:
            st.error("거래 내역을 불러오지 못했습니다.")
    except Exception as e:
        st.error(f"백엔드 서버 통신 오류: {e}")

