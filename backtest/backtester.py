import pandas as pd
import os
import io
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.detach(), encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.detach(), encoding='utf-8')

# 모듈 경로 추가
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from strategies.hanwha_grid import HanwhaGridStrategy

def run_backtest():
    csv_path = os.path.join(os.path.dirname(__file__), '042660_minute_data_full.csv')
    print(f"[{csv_path}] 분봉 데이터를 불러오는 중...")
    
    if not os.path.exists(csv_path):
        print("CSV 파일이 존재하지 않습니다. 먼저 fetch_kis_minutes.py를 실행하세요.")
        return
        
    df = pd.read_csv(csv_path)
    strategy = HanwhaGridStrategy()

    print("틱 단위(분봉 내 고가/저가) 백테스팅 시뮬레이션 시작...")
    for index, row in df.iterrows():
        low = int(row['Low'])
        high = int(row['High'])

        # 저가부터 고가까지 100원 단위로 시뮬레이션 (단순 틱 제너레이션)
        for price in range(low, high + 1, 100):
            strategy.generate_signals(price)
            
    # 최종 결과 출력
    final_price = int(df.iloc[-1]['Close'])
    status = strategy.get_status(final_price)
    
    print("=" * 40)
    print("백테스팅 결과")
    print("=" * 40)
    print(f"총 투입 자금: {status['total_injected']:,} 원")
    print(f"잔고(현금): {status['cash']:,.0f} 원")
    print(f"주식 평가금: {status['stock_value']:,.0f} 원")
    print(f"총 평가금: {status['total_value']:,.0f} 원")
    print(f"총 수익률: {status['return_rate']:.2f}%")
    print(f"현재 보유 포지션 수: {status['holding_count']}개")
    print("=" * 40)

if __name__ == "__main__":
    run_backtest()
