import codecs

file_path = r'd:\aiworkspace\app\dashboard.py'
with codecs.open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update order_book display
old_order_book_display = '''        def highlight_rows(row):
            if row["side"] == "🎯 현재가":
                return ['background-color: #ffd700; color: black; font-weight: bold'] * len(row)
            elif row.get("side", "").lower() == "sell" or row.get("side", "") == "매도":
                return ['background-color: rgba(54, 162, 235, 0.2)'] * len(row)
            elif row.get("side", "").lower() == "buy" or row.get("side", "") == "매수":
                return ['background-color: rgba(255, 99, 132, 0.2)'] * len(row)
            return [''] * len(row)

        st.dataframe(order_book.style.apply(highlight_rows, axis=1), width="stretch", height=500)'''

new_order_book_display = '''        def highlight_rows(row):
            side = row.get("방향", row.get("side", ""))
            if side == "🎯 현재가":
                return ['background-color: #ffd700; color: black; font-weight: bold'] * len(row)
            elif str(side).lower() == "sell" or side == "매도":
                return ['background-color: rgba(54, 162, 235, 0.2)'] * len(row)
            elif str(side).lower() == "buy" or side == "매수":
                return ['background-color: rgba(255, 99, 132, 0.2)'] * len(row)
            return [''] * len(row)

        display_order_book = order_book.rename(columns={"id": "주문번호", "side": "방향", "price": "가격(원)", "quantity": "수량", "symbol": "종목"})
        st.dataframe(display_order_book.style.apply(highlight_rows, axis=1), width="stretch", height=500)'''

if old_order_book_display in content:
    content = content.replace(old_order_book_display, new_order_book_display)
else:
    print('Could not find old_order_book_display')

# 2. Update list view display
old_list_view = 'st.dataframe(df_positions, width="stretch")'
new_list_view = 'st.dataframe(df_positions.rename(columns={"id": "주문번호", "side": "방향", "price": "가격(원)", "quantity": "수량", "symbol": "종목"}), width="stretch")'

if old_list_view in content:
    content = content.replace(old_list_view, new_list_view)
else:
    print('Could not find old_list_view')

with codecs.open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
print('Grid display update script finished.')

