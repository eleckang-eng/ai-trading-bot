with open('app/dashboard.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('성공\n"', '성공\\n"')
content = content.replace('실패\n"', '실패\\n"')
content = content.replace('v)}\n"', 'v)}\\n"')

with open('app/dashboard.py', 'w', encoding='utf-8') as f:
    f.write(content)
