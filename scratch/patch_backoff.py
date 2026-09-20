import codecs
import re

file_path = r'd:\aiworkspace\exchanges\kis_api.py'
with codecs.open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

old_block = '''        max_retries = 5
        for attempt in range(max_retries):
            res = requests.post(url, headers=headers, data=json.dumps(body))
            data = res.json()
            
            rt_cd = str(data.get("rt_cd", "0"))
            msg1 = data.get("msg1", "")
            msg_cd = data.get("msg_cd", "")
            
            # KIS Rate Limit 에러 방어적 프로그래밍 (초당 거래건수 초과 등)
            if rt_cd != "0" and ("초과" in msg1 or "건수" in msg1 or "EGW00" in msg_cd):
                print(f"[Rate Limit] KIS API 제한 도달 ({msg1}). 1초 대기 후 재시도... ({attempt+1}/{max_retries})")
                time.sleep(1.2)
                continue
                
            return data'''

new_block = '''        max_retries = 5
        base_wait = 1.0
        for attempt in range(max_retries):
            res = requests.post(url, headers=headers, data=json.dumps(body))
            data = res.json()
            
            rt_cd = str(data.get("rt_cd", "0"))
            msg1 = data.get("msg1", "")
            msg_cd = data.get("msg_cd", "")
            
            # KIS Rate Limit 점진적 대기(Exponential/Incremental Backoff)
            if rt_cd != "0" and ("초과" in msg1 or "건수" in msg1 or "EGW00" in msg_cd):
                wait_time = base_wait + (attempt * 0.8) # 1.0, 1.8, 2.6, 3.4, 4.2초...
                print(f"[Rate Limit] KIS API 제한 도달 ({msg1}). {wait_time:.1f}초 대기 후 재시도... ({attempt+1}/{max_retries})")
                time.sleep(wait_time)
                continue
                
            return data'''

if old_block in content:
    content = content.replace(old_block, new_block)
else:
    print('Could not find old_block')

with codecs.open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
print('Incremental backoff patch applied.')

