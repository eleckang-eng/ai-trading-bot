import sys, codecs
sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
with codecs.open(r'd:\aiworkspace\app\dashboard.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()
for i, l in enumerate(lines):
    if 'side_kor =' in l:
        for j in range(i, i+5): print(repr(lines[j]))
        break
for i, l in enumerate(lines):
    if 'st.warning' in l and '거래소에 주문을' in l:
        for j in range(i, i+5): print(repr(lines[j]))
        break

