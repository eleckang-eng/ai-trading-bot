import sys
import os

# core 모듈을 임포트하기 위해 상위 경로 추가
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.kakao_api import KakaoMessenger

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    print("mcp 패키지가 설치되어 있지 않습니다. 'pip install mcp'를 실행해주세요.")
    sys.exit(1)

# MCP 서버 인스턴스 생성
mcp = FastMCP("kakao-messenger")
messenger = KakaoMessenger()

@mcp.tool()
def send_kakao_message(message: str) -> str:
    """
    지정된 메시지를 카카오톡 '나에게 보내기'로 전송합니다.
    트레이딩 봇의 상태, 수익률, 체결 알림 등을 보낼 때 사용합니다.
    """
    success = messenger.send_message(message)
    if success:
        return "카카오톡 메시지 전송 성공"
    else:
        return "카카오톡 메시지 전송 실패. 로그를 확인하세요."

if __name__ == "__main__":
    # MCP 서버 실행 (stdio 표준 입출력 통신 방식)
    mcp.run()

