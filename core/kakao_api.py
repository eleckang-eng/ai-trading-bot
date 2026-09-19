import os
import json
import logging
import requests
from dotenv import load_dotenv

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 환경변수 로드
load_dotenv()

TOKEN_FILE = os.path.join(os.path.dirname(__file__), 'kakao_token.json')

class KakaoMessenger:
    def __init__(self):
        self.app_key = os.getenv("KAKAO_REST_API_KEY")
        self.tokens = self._load_tokens()

    def _load_tokens(self):
        if not os.path.exists(TOKEN_FILE):
            logger.warning("카카오 토큰 파일이 없습니다. 최초 인증을 진행해주세요.")
            return {}
        try:
            with open(TOKEN_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"토큰 파일을 읽는 중 오류 발생: {e}")
            return {}

    def _save_tokens(self, tokens):
        try:
            with open(TOKEN_FILE, 'w') as f:
                json.dump(tokens, f)
            self.tokens = tokens
        except Exception as e:
            logger.error(f"토큰 저장 중 오류 발생: {e}")

    def refresh_token(self):
        if not self.tokens.get("refresh_token"):
            logger.error("리프레시 토큰이 없어 토큰을 갱신할 수 없습니다.")
            return False

        url = "https://kauth.kakao.com/oauth/token"
        data = {
            "grant_type": "refresh_token",
            "client_id": self.app_key,
            "refresh_token": self.tokens["refresh_token"]
        }
        
        try:
            response = requests.post(url, data=data)
            response.raise_for_status()
            new_tokens = response.json()
            
            # 리프레시 토큰이 응답에 없다면 기존 것 유지
            if "refresh_token" not in new_tokens:
                new_tokens["refresh_token"] = self.tokens["refresh_token"]
                
            self._save_tokens(new_tokens)
            logger.info("카카오 액세스 토큰 갱신 완료")
            return True
        except Exception as e:
            logger.error(f"토큰 갱신 실패: {e}")
            return False

    def send_message(self, text: str):
        if not self.tokens.get("access_token"):
            logger.error("액세스 토큰이 없습니다. 전송 불가.")
            return False

        url = "https://kapi.kakao.com/v2/api/talk/memo/default/send"
        headers = {
            "Authorization": f"Bearer {self.tokens['access_token']}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        template = {
            "object_type": "text",
            "text": text,
            "link": {
                "web_url": "https://developers.kakao.com",
                "mobile_web_url": "https://developers.kakao.com"
            },
            "button_title": "확인"
        }
        
        data = {
            "template_object": json.dumps(template)
        }
        
        try:
            response = requests.post(url, headers=headers, data=data)
            
            # 401 에러(토큰 만료) 시 갱신 후 재시도
            if response.status_code == 401:
                logger.info("토큰이 만료되어 갱신을 시도합니다.")
                if self.refresh_token():
                    headers["Authorization"] = f"Bearer {self.tokens['access_token']}"
                    response = requests.post(url, headers=headers, data=data)
            
            response.raise_for_status()
            logger.info("카카오톡 메시지 발송 성공")
            return True
        except Exception as e:
            logger.error(f"메시지 전송 중 오류 발생: {e}")
            return False

