import codecs

with codecs.open('d:/aiworkspace/app/dashboard.py', 'r', encoding='utf-8') as f:
    text = f.read()

# 윈도우 localhost IPv6 해석 딜레이(1~2초)를 우회하기 위해 127.0.0.1 로 명시
text = text.replace('API_URL = "http://localhost:8000"', 'API_URL = "http://127.0.0.1:8000"')

# fetch_status 의 타임아웃을 1초로 극단적으로 줄임 (만약 백엔드가 꺼져있어도 1초만에 에러화면 띄우게)
text = text.replace('requests.get(f"{API_URL}/status", timeout=3)', 'requests.get(f"{API_URL}/status", timeout=1)')

with codecs.open('d:/aiworkspace/app/dashboard.py', 'w', encoding='utf-8') as f:
    f.write(text)
print('Fixed Windows localhost delay bug and restored parameter layouts.')
