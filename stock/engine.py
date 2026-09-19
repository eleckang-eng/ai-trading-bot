import streamlit as st

st.set_page_config(page_title="한화오션 그리드 봇", layout="centered")

st.title("한화오션 틱 핑퐁 그리드 대시보드")

# 세션 상태 초기화 (메모리 저장소)
if "running" not in st.session_state:
    st.session_state.running = False
    st.session_state.base_price = 100000
    st.session_state.current_price = 100000
    st.session_state.realized_pnl = 0
    st.session_state.trade_count = 0

# 사이드바: 제어 및 설정 패널
st.sidebar.header("시스템 제어 패널")

if st.sidebar.button("시스템 시작"):
    st.session_state.running = True

if st.sidebar.button("비상 정지 (긴급 중단)"):
    st.session_state.running = False
    st.sidebar.warning("모든 주문이 중지되었습니다.")

new_base_price = st.sidebar.number_input("기준가(시가) 설정", value=st.session_state.base_price, step=1000)
if st.sidebar.button("기준가 변경 적용"):
    st.session_state.base_price = new_base_price
    st.sidebar.success(f"기준가가 {new_base_price:,}원으로 변경되었습니다.")

# 메인 화면: 현황판
col1, col2 = st.columns(2)
with col1:
    st.metric(label="시스템 구동 상태", value="RUNNING" if st.session_state.running else "STOPPED")
    st.metric(label="설정 기준가", value=f"{st.session_state.base_price:,} 원")

with col2:
    st.metric(label="누적 실현 손익", value=f"{st.session_state.realized_pnl:,} 원")
    st.metric(label="핑퐁 체결 횟수", value=f"{st.session_state.trade_count} 회")

st.markdown("---")

# 수동 테스트 입력부
st.subheader("실시간 가격 입력 및 테스트")
input_price = st.number_input("현재가 입력", value=st.session_state.current_price, step=100)
if st.button("가격 업데이트 및 그리드 연동"):
    st.session_state.current_price = input_price
    if st.session_state.running:
        st.session_state.trade_count += 1
        st.session_state.realized_pnl += 1800 # 스프레드 마진 시뮬레이션
        st.success(f"현재가 {input_price:,}원 반영 완료 (핑퐁 매매 실행)")
    else:
        st.warning("시스템이 정지 상태입니다. '시스템 시작'을 먼저 눌러주세요.")

st.text(f"현재 적용된 주가: {st.session_state.current_price:,} 원")