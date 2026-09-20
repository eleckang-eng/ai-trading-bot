import re

with open('app/dashboard.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 정규식을 이용해 엉켜버린 if st.button('✅ 네, 주문 전송합니다' 블록 전체를 추출하여 교체
pattern = r'(if st\.button\("✅ 네, 주문 전송합니다".*?)(?=\s*with c2:\s*if st\.button\("❌ 취소")'

new_block = '''if st.button("✅ 네, 주문 전송합니다", type="primary", use_container_width=True):
                        payload_orders = []
                        for row in edited_sell:
                            if not row.get("선택", True): continue
                            qty = row.get("수량")
                            price = row.get("가격")
                            if pd.notna(qty) and pd.notna(price) and float(qty) > 0 and float(price) > 0:
                                payload_orders.append({"side": "sell", "quantity": float(qty), "price": float(price)})
                        for row in edited_buy:
                            if not row.get("선택", True): continue
                            qty = row.get("수량")
                            price = row.get("가격")
                            if pd.notna(qty) and pd.notna(price) and float(qty) > 0 and float(price) > 0:
                                payload_orders.append({"side": "buy", "quantity": float(qty), "price": float(price)})
                            
                        if len(payload_orders) == 0:
                            st.error("전송할 유효한 주문이 없습니다. (수량이나 가격이 비어있거나 0 이하입니다)")
                        else:
                            status_text = st.empty()
                            progress_bar = st.progress(0)
                            
                            results = []
                            total_cnt = len(payload_orders)
                            
                            import time
                            for i, order_data in enumerate(payload_orders):
                                current_step = i + 1
                                status_text.info(f"🚀 거래소로 주문을 순차 전송 중입니다... ({current_step}/{total_cnt})")
                                progress_bar.progress(current_step / total_cnt)
                                
                                try:
                                    res = requests.post(f"{API_URL}/order/manual", json=order_data, timeout=5)
                                    if res.status_code == 200:
                                        results.append(res.json())
                                    else:
                                        results.append({"status": "error", "message": f"HTTP {res.status_code}"})
                                except Exception as e:
                                    results.append({"status": "error", "message": str(e)})
                                    
                                time.sleep(0.25)
                                
                            status_text.empty()
                            progress_bar.empty()
                            
                            success_groups = {}
                            fail_groups = {}
                            
                            for idx, r in enumerate(results):
                                side = "매수" if payload_orders[idx]["side"] == "buy" else "매도"
                                prc_str = f"{payload_orders[idx]['price']:,.0f}원"
                                
                                if isinstance(r, dict) and r.get("status") == "success":
                                    key = f"✅ {side} 주문 접수 성공"
                                    if key not in success_groups: success_groups[key] = []
                                    success_groups[key].append(prc_str)
                                else:
                                    fail_reason = r.get('message', '알 수 없음') if isinstance(r, dict) else str(r)
                                    if "msg1" in fail_reason:
                                        import ast
                                        try:
                                            dict_str = fail_reason.split("주문 실패: ")[-1]
                                            err_dict = ast.literal_eval(dict_str)
                                            reason_str = err_dict.get("msg1", fail_reason)
                                        except:
                                            reason_str = fail_reason
                                    else:
                                        reason_str = fail_reason
                                        
                                    key = f"❌ {reason_str}"
                                    if key not in fail_groups: fail_groups[key] = []
                                    fail_groups[key].append(f"[{side}] {prc_str}")
                                    
                            success_count = sum(len(v) for v in success_groups.values())
                            fail_count = sum(len(v) for v in fail_groups.values())
                            
                            if success_count > 0:
                                msg = f"#### 🎉 총 {success_count}건 성공\\n"
                                for k, v in success_groups.items():
                                    msg += f"- **{k}** ({len(v)}건) ➔ {', '.join(v)}\\n"
                                st.success(msg)
                                
                            if fail_count > 0:
                                msg = f"#### 🚨 총 {fail_count}건 실패\\n"
                                for k, v in fail_groups.items():
                                    msg += f"- **{k}** ({len(v)}건) ➔ {', '.join(v)}\\n"
                                st.error(msg)
                                
                            if fail_count == 0 and success_count > 0:
                                st.session_state.show_grid_preview = False
                                st.session_state.confirm_batch_order = False
                                import time; time.sleep(2); st.rerun()
                                
                '''

new_content = re.sub(pattern, new_block, content, flags=re.DOTALL)

with open('app/dashboard.py', 'w', encoding='utf-8') as f:
    f.write(new_content)
    
print("Fixed successfully!")
