import codecs
import re

file_path = r'd:\aiworkspace\app\dashboard.py'
with codecs.open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Fix batch warning
old_batch_warn = 'st.warning("⚠️ 정말로 이대로 거래소에 주문을 전송하시겠습니까? (실제 자산이 매매됩니다)")'
new_batch_warn = '''st.warning("⚠️ 정말로 이대로 거래소에 주문을 전송하시겠습니까? (실제 자산이 매매됩니다)")
        
        existing_prices = [float(p.get("price", p.get("avg_price", 0))) for p in status_data.get('positions', [])]
        overlap = []
        for row in edited_sell + edited_buy:
            if not row.get("선택", True): continue
            price = row.get("가격")
            if price and float(price) in existing_prices:
                overlap.append(float(price))
                
        if overlap:
            unique_overlap = sorted(list(set(overlap)))
            overlap_str = ", ".join([f"{int(p):,}원" for p in unique_overlap])
            st.error(f"⚠️ 이미 거미줄(미체결)에 다음 가격의 주문이 존재합니다: {overlap_str}\\n중복 주문일 수 있으니 다시 한 번 확인해 주세요!")'''

if old_batch_warn in content and 'unique_overlap =' not in content:
    content = content.replace(old_batch_warn, new_batch_warn)

# Fix manual warning
old_manual_warn = '''        side_kor = "🔴 매수" if order["side"] == "buy" else "🔵 매도"
        st.warning(f"정말로 **{side_kor}** 주문을 전송하시겠습니까? (단가: {order['price']:,} 원, 수량: {order['quantity']} 주)")'''
new_manual_warn = '''        side_kor = "🔴 매수" if order["side"] == "buy" else "🔵 매도"
        st.warning(f"정말로 **{side_kor}** 주문을 전송하시겠습니까? (단가: {order['price']:,} 원, 수량: {order['quantity']} 주)")
        
        existing_prices = [float(p.get("price", p.get("avg_price", 0))) for p in status_data.get('positions', []) if str(p.get("side", "")).lower() == order["side"] or str(p.get("side", "")) == side_kor[-2:]]
        if float(order['price']) in existing_prices:
            st.error(f"⚠️ 이미 거미줄(미체결)에 동일한 가격({order['price']:,}원)의 주문이 존재합니다. 중복 주문일 수 있습니다!")'''

if old_manual_warn in content and 'existing_prices =' not in content:
    content = content.replace(old_manual_warn, new_manual_warn)

with codecs.open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
print('Patched successfully!')

