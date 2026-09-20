import sys
import codecs

file_path = r'd:\aiworkspace\app\dashboard.py'
with codecs.open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('sell_list.append({"가격": int(s_price), "수량": int(order_quantity)})', 'sell_list.append({"선택": True, "가격": int(s_price), "수량": int(order_quantity)})')
content = content.replace('buy_list.append({"가격": int(b_price), "수량": int(order_quantity)})', 'buy_list.append({"선택": True, "가격": int(b_price), "수량": int(order_quantity)})')

old_sell_loop = '''                        for row in edited_sell:
                            qty = row.get("수량")
                            price = row.get("가격")'''
new_sell_loop = '''                        for row in edited_sell:
                            if not row.get("선택", True): continue
                            qty = row.get("수량")
                            price = row.get("가격")'''
content = content.replace(old_sell_loop, new_sell_loop)

old_buy_loop = '''                        for row in edited_buy:
                            qty = row.get("수량")
                            price = row.get("가격")'''
new_buy_loop = '''                        for row in edited_buy:
                            if not row.get("선택", True): continue
                            qty = row.get("수량")
                            price = row.get("가격")'''
content = content.replace(old_buy_loop, new_buy_loop)

old_total_orders = '        total_orders = len(edited_sell) + len(edited_buy)'
new_total_orders = '        total_orders = sum(1 for r in edited_sell if r.get("선택", True)) + sum(1 for r in edited_buy if r.get("선택", True))'
content = content.replace(old_total_orders, new_total_orders)

with codecs.open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
print('Dashboard updated successfully!')

