import codecs

file_path = r'd:\aiworkspace\app\dashboard.py'
with codecs.open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

old_list_view = 'st.dataframe(df_positions, width="stretch")'
new_list_view = 'st.dataframe(df_positions.rename(columns={"id": "주문번호", "side": "방향", "price": "가격(원)", "quantity": "수량", "symbol": "종목"}), width="stretch")'

if old_list_view in content:
    content = content.replace(old_list_view, new_list_view)
else:
    print('Could not find old_list_view')

with codecs.open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
print('List view update finished.')

