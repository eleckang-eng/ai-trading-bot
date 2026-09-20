import codecs

with codecs.open('d:/aiworkspace/app/dashboard.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
skip = False
for line in lines:
    if '# 화면 렌더링 후 최초 1회 자산 자동 동기화' in line:
        skip = True
    
    if not skip:
        new_lines.append(line)
        
with codecs.open('d:/aiworkspace/app/dashboard.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
print('Removed auto balance sync logic')
