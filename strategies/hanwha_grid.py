class HanwhaGridStrategy:
    def __init__(self):
        self.initial_capital = 10000000  # 시작 자금 1000만원
        self.cash = self.initial_capital
        self.total_injected = self.initial_capital
        self.positions = []  # 매수 건별 기록 [{'buy_price': int, 'qty': int}]
        self.last_buy_price = None
        self.max_price = 0

    def generate_signals(self, current_price):
        """현재가에 따른 매수/매도 시그널 생성 및 체결 처리"""
        self.max_price = max(self.max_price, current_price)
        
        # 가격대별 설정 (10만원 기준)
        if current_price >= 100000:
            step = 2000
            margin = 2800
            # 매수 끝자리 100, 매도 끝자리 900
        else:
            step = 1000
            margin = 1800
            # 매수 끝자리 100, 매도 끝자리 900

        # 1. 매도 로직 확인
        sold_positions = []
        for pos in self.positions:
            sell_target = pos['buy_price'] + margin
            if current_price >= sell_target:
                # 매도 체결
                self.cash += current_price * pos['qty']
                sold_positions.append(pos)
        
        # 체결된 포지션 제거
        for pos in sold_positions:
            self.positions.remove(pos)

        # 2. 매수 로직 확인
        # 현재가가 매수 타점(끝자리 100)인지 확인 (예: 90100, 91100, 100100)
        if current_price % 1000 == 100:
            # 직전 매수가 대비 step만큼 하락했거나, 첫 매수인 경우
            if self.last_buy_price is None or current_price <= self.last_buy_price - step:
                buy_qty = 10  # 기본 매수 수량 (임의 설정, 필요시 수정 가능)
                required_cash = current_price * buy_qty

                # 자금 부족 시 증액 로직
                if self.cash < required_cash:
                    # 하단 밀릴 때마다 300만원 증액
                    injection = 3000000
                    # 10만원 이상 하락 시 추가 100만원 증액 (최고가 대비 10만원 하락 의미로 해석)
                    if self.max_price - current_price >= 100000:
                        injection += 1000000
                    
                    self.cash += injection
                    self.total_injected += injection
                    # print(f"자금 증액: {injection}원 (총 증액: {self.total_injected}원)")

                # 매수 체결
                self.cash -= required_cash
                self.positions.append({'buy_price': current_price, 'qty': buy_qty})
                self.last_buy_price = current_price

    def get_status(self, current_price):
        """현재 계좌 상태 반환"""
        stock_value = sum(pos['qty'] * current_price for pos in self.positions)
        total_value = self.cash + stock_value
        return_rate = ((total_value / self.total_injected) - 1) * 100
        return {
            'total_injected': self.total_injected,
            'cash': self.cash,
            'stock_value': stock_value,
            'total_value': total_value,
            'return_rate': return_rate,
            'holding_count': len(self.positions)
        }
