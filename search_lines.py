# coding=utf-8
with open('app/dashboard.py', 'r', encoding='utf-8') as f:
    with open('output.txt', 'w', encoding='utf-8') as out:
        for i, line in enumerate(f):
            if '공통' in line or 'st.divider()' in line or 'st.markdown("---")' in line or '알고리즘 파라미터' in line:
                out.write(f'{i}: {line.strip()}\n')

