import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# 백엔드 API URL
API_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="AI 핑퐁 봇", page_icon="📈", layout="wide", initial_sidebar_state="expanded")

# --- 커스텀 CSS ---
st.markdown("""
<style>
    .reportview-container .main .block-container{
        padding-top: 2rem;
    }
    .metric-container {
        background-color: #1e1e1e;
        border-radius: 5px;
        padding: 15px;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.3);
    }
</style>
""", unsafe_allow_html=True)

st.title("AI 통합 핑퐁 봇 대시보드")
st.markdown("실시간 매매 현황 및 알고리즘 상태 모니터링")

# --- 상태 조회 함수 (1회만 호출하여 전역 사용) ---
def fetch_status():
    try:
        response = requests.get(f"{API_URL}/status", timeout=10)
        if response.status_code == 200:
            return response.json()
    except Exception:
        pass
    return None

status_data = fetch_status()

# --- 사이드바 제어 ---
with st.sidebar:
    st.header("⚙️ 시스템 제어")
    
    # 거래소 토글
    exchange_choice = st.radio("거래소 모드", ["빗썸 (가상화폐)", "한국투자증권 (국내주식)"], index=0)
    
    if st.button("🔄 거래소 적용", width="stretch"):
        new_exchange = "bithumb" if "빗썸" in exchange_choice else "kis"
        new_symbol = "ONDO" if new_exchange == "bithumb" else "042660"
        success = False
        try:
            response = requests.post(f"{API_URL}/config", json={"exchange": new_exchange, "symbol": new_symbol}, timeout=5)
            if response.status_code == 200:
                st.success(f"{exchange_choice} 모드로 전환됨.")
                success = True
            else:
                st.error("변경 실패")
        except requests.exceptions.RequestException as e:
            st.error(f"서버 통신 실패: {e}")
        
        if success:
            import time
            time.sleep(0.3)
            st.rerun()

    st.divider()
    
    # 매매 알고리즘 파라미터
    st.subheader("매매 알고리즘 파라미터")
    grid_interval = st.number_input("매수 하락폭 (원)", min_value=1, value=10, step=1)
    take_profit = st.number_input("매도 수익폭 (원)", min_value=1, value=15, step=1)
    order_amount = st.number_input("1회 매수 예산 (원)", min_value=1000, value=50000, step=1000)
    
    if st.button("💾 파라미터 저장", width="stretch"):
        try:
            res = requests.post(f"{API_URL}/config", json={
                "grid_interval": grid_interval,
                "take_profit": take_profit,
                "order_amount": order_amount
            }, timeout=5)
            if res.status_code == 200:
                st.success("알고리즘 파라미터 저장 완료")
            else:
                st.error("파라미터 저장 실패")
        except requests.exceptions.RequestException:
            st.error("서버 통신 실패")

    st.divider()
    
    # 시작/정지 버튼
    is_running = status_data.get("running", False) if status_data else False
    col1, col2 = st.columns(2)

    with col1:
        if is_running:
            st.button("▶️ 가동 중", type="primary", width="stretch", disabled=True)
        else:
            if st.button("▶️ 시작", type="primary", width="stretch"):
                try:
                    requests.post(f"{API_URL}/start", timeout=5)
                    st.rerun()
                except:
                    pass
    with col2:
        if not is_running:
            st.button("🛑 정지됨", width="stretch", disabled=True)
        else:
            if st.button("🛑 정지", width="stretch"):
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
        st.metric(label="활성 거미줄 노드", value=f"{len(status_data.get('positions', []))} 개")
    
    st.divider()
    
    # 2. 탭 콘텐츠
    tab1, tab2, tab3, tab4 = st.tabs(["📈 실시간 차트", "🕸️ 거미줄 현황", "📜 거래 내역", "📡 시스템 로그"])
    
    with tab1:
        cfg = status_data.get('config', {})
        exchange_name = "빗썸" if cfg.get('exchange') == 'bithumb' else "한국투자증권"
        st.subheader(f"[{exchange_name}] 타겟: {cfg.get('symbol', 'N/A')}")
        st.info("시세 데이터 파이프라인(WebSocket) 연동 후 캔들 차트가 활성화됩니다.")
        chart_data = pd.DataFrame({'시간': [datetime.now()], '가격': [0]})
        st.line_chart(chart_data.set_index('시간'))

    with tab2:
        st.subheader("현재 진입 대기 중인 매수/매도 그리드")
        positions = status_data.get('positions', [])
        if positions:
            st.dataframe(pd.DataFrame(positions), width="stretch")
        else:
            st.write("활성화된 거미줄 포지션이 없습니다.")

    with tab3:
        st.subheader("최근 체결 내역")
        st.write("알고리즘 가동 시 실시간으로 기록됩니다.")
        mock_trades = pd.DataFrame(columns=["시간", "종류", "가격(원)", "수량", "상태"])
        st.dataframe(mock_trades, width="stretch")

    with tab4:
        st.subheader("엔진 구동 상태")
        cfg = status_data.get('config', {})
        is_running_main = status_data.get("running", False)
        st.write(f"**코어 루프 상태:** {'🟢 가동 중' if is_running_main else '🔴 정지됨'}")
        st.write(f"**적용된 거래소:** {cfg.get('exchange', 'kis').upper()}")
        st.write(f"**타겟 종목:** {cfg.get('symbol', 'N/A')}")
        
        # 알고리즘 파라미터 표시
        algo_params = {
            "매수 하락폭": f"{cfg.get('grid_interval', '미설정')} 원",
            "매도 수익폭": f"{cfg.get('take_profit', '미설정')} 원",
            "1회 매수 예산": f"{cfg.get('order_amount', '미설정')} 원",
        }
        st.table(pd.DataFrame(algo_params.items(), columns=["파라미터", "값"]))

else:
    st.error("백엔드 서버(FastAPI)와 통신할 수 없습니다. 엔진 가동 상태를 확인하십시오.")
