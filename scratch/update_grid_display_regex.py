import codecs, re

file_path = r'd:\aiworkspace\app\dashboard.py'
with codecs.open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

pattern = re.compile(r'(def highlight_rows\(row\):.*?st\.dataframe\(order_book\.style\.apply\(highlight_rows, axis=1\), width="stretch", height=500\))', re.DOTALL)

def replacer(match):
    old_block = match.group(1)
    new_block = old_block.replace('row["side"] == "🎯 현재가"', 'row.get("방향", row.get("side", "")) == "🎯 현재가"')
    new_block = new_block.replace('row.get("side", "")', 'row.get("방향", row.get("side", ""))')
    new_block = new_block.replace('st.dataframe(order_book.style', 'display_order_book = order_book.rename(columns={"id": "주문번호", "side": "방향", "price": "가격(원)", "quantity": "수량", "symbol": "종목"})\n                    st.dataframe(display_order_book.style')
    return new_block

new_content = pattern.sub(replacer, content)

with codecs.open(file_path, 'w', encoding='utf-8') as f:
    f.write(new_content)
print('Regex update script finished.')

