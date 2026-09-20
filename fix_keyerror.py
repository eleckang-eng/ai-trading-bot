with open('d:/aiworkspace/app/dashboard.py', 'r', encoding='utf-8') as f:
    text = f.read()

old_highlight = '''                def highlight_side(row):
                    if row['side'] == '매도': return ['background-color: rgba(50, 50, 200, 0.2)'] * len(row)
                    elif row['side'] == '매수': return ['background-color: rgba(200, 50, 50, 0.2)'] * len(row)
                    return [''] * len(row)'''

new_highlight = '''                def highlight_side(row):
                    if row['방향'] == '매도': return ['background-color: rgba(50, 50, 200, 0.2)'] * len(row)
                    elif row['방향'] == '매수': return ['background-color: rgba(200, 50, 50, 0.2)'] * len(row)
                    return [''] * len(row)'''

text = text.replace(old_highlight, new_highlight)

with open('d:/aiworkspace/app/dashboard.py', 'w', encoding='utf-8') as f:
    f.write(text)
print('KeyError side fixed.')
