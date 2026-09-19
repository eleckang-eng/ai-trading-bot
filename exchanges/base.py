from abc import ABC, abstractmethod

class BaseExchange(ABC):
    """모든 거래소(증권사/코인) 통신 모듈이 구현해야 할 공통 인터페이스"""
    
    @abstractmethod
    def get_balance(self):
        """계좌 잔고 및 예수금 조회"""
        pass

    @abstractmethod
    def get_current_price(self, symbol: str):
        """특정 종목의 현재가 조회"""
        pass

    @abstractmethod
    def buy_limit(self, symbol: str, price: int, quantity: int):
        """지정가 매수 주문"""
        pass

    @abstractmethod
    def sell_limit(self, symbol: str, price: int, quantity: int):
        """지정가 매도 주문"""
        pass
    
    @abstractmethod
    def cancel_order(self, order_id: str):
        """주문 취소"""
        pass
