import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

def get_initial_token():
    app_key = os.getenv("KAKAO_REST_API_KEY")
    redirect_uri = "https://localhost"
    
    if not app_key:
        print("에러: .env 파일에 KAKAO_REST_API_KEY 가 설정되어 있지 않습니다.")
        return

    print("=" * 60)
    print("1. 카카오 로그인 인가 코드 발급하기")
    print("아래 URL을 브라우저에 복사하여 접속한 후, 카카오 로그인을 진행하세요.")
    
    auth_url = (f"https://kauth.kakao.com/oauth/authorize"
                f"?client_id={app_key}&redirect_uri={redirect_uri}&response_type=code&prompt=consent")
    print(f"\n{auth_url}\n")
    
    print("로그인 완료 후 브라우저가 리다이렉트되는 주소(URL) 창에서 '?code=' 뒷부분의 문자열을 복사하세요.")
    print("주의: 카카오 디벨로퍼스 앱 설정 -> 카카오 로그인 -> Redirect URI 에 'https://localhost' 가 등록되어 있어야 합니다.")
    print("주의: 앱 설정 -> 동의항목에서 '카카오톡 메시지 전송(talk_message)' 권한이 체크되어 있어야 합니다.")
    print("=" * 60)
    
    auth_code = input("\n복사한 인가 코드(code)를 입력하세요: ").strip()
    
    if not auth_code:
        print("입력된 코드가 없습니다. 종료합니다.")
        return

    print("\n2. 액세스 토큰 발급 중...")
    
    token_url = "https://kauth.kakao.com/oauth/token"
    data = {
        "grant_type": "authorization_code",
        "client_id": app_key,
        "redirect_uri": redirect_uri,
        "code": auth_code
    }
    
    response = requests.post(token_url, data=data)
    if response.status_code == 200:
        tokens = response.json()
        token_file = os.path.join(os.path.dirname(__file__), 'kakao_token.json')
        with open(token_file, 'w') as f:
            json.dump(tokens, f)
        print(f"\n성공! 토큰이 {token_file} 에 저장되었습니다.")
        print("이제 봇이나 MCP 서버에서 카카오톡 알림을 보낼 수 있습니다.")
    else:
        print(f"\n토큰 발급 실패: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    get_initial_token()
