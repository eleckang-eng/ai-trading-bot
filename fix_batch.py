import re

with open('d:/aiworkspace/app/dashboard.py', 'r', encoding='utf-8') as f:
    text = f.read()

# 'if res.status_code == 200:' 부터 'else:'(서버 오류: HTTP) 전까지 추출하여 교체
pattern = re.compile(r'if res\.status_code == 200:.*?else:\n\s*st\.error\(f"서버 오류: HTTP \{res\.status_code\}"\)', re.DOTALL)

replacement = '''if res.status_code == 200:
                                    data = res.json()
                                    results = data.get("results", [])
                                    
                                    success_count = sum(1 for r in results if isinstance(r, dict) and r.get("status") == "success")
                                    fail_count = len(results) - success_count
                                    
                                    success_msgs = []
                                    fail_msgs = []
                                    
                                    for idx, r in enumerate(results):
                                        side = "매수" if payload_orders[idx]["side"] == "buy" else "매도"
                                        prc = payload_orders[idx]["price"]
                                        if isinstance(r, dict) and r.get("status") == "success":
                                            success_msgs.append(f"✅ {side} {prc}원: 성공")
                                        else:
                                            fail_reason = r.get('message', '알 수 없음') if isinstance(r, dict) else str(r)
                                            fail_msgs.append(f"❌ {side} {prc}원 실패 원인: {fail_reason}")
                                    
                                    if len(success_msgs) > 0:
                                        if len(fail_msgs) == 0:
                                            st.success("모든 일괄 주문이 성공적으로 전송되었습니다!\\n\\n" + "\\n".join(success_msgs))
                                        else:
                                            st.success(f"{len(success_msgs)}건 주문 성공:\\n\\n" + "\\n".join(success_msgs))
                                            
                                    if len(fail_msgs) > 0:
                                        st.error(f"{len(fail_msgs)}건 주문 실패:\\n\\n" + "\\n".join(fail_msgs))
                                    
                                    if fail_count == 0 and success_count > 0:
                                        st.session_state.show_grid_preview = False
                                        st.session_state.confirm_batch_order = False
                                        import time; time.sleep(2); st.rerun()
                                else:
                                    st.error(f"서버 오류: HTTP {res.status_code}")'''

text = pattern.sub(replacement, text)

with open('d:/aiworkspace/app/dashboard.py', 'w', encoding='utf-8') as f:
    f.write(text)
print('Batch order logic replaced.')
