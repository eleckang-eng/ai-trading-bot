import codecs

with codecs.open('d:/aiworkspace/app/dashboard.py', 'r', encoding='utf-8') as f:
    text = f.read()

bad_df_code = '''                def highlight_side(row):
                    if row['방향'] == '매도': return ['background-color: rgba(50, 50, 200, 0.2)'] * len(row)
                    elif row['방향'] == '매수': return ['background-color: rgba(200, 50, 50, 0.2)'] * len(row)
                    return [''] * len(row)
                combined_df = pd.concat([sell_orders, buy_orders])
                display_df = combined_df[['side', 'price', 'quantity', 'id']].copy()
                display_df.columns = ['방향', '주문 가격', '수량', 'ID']
                styled_df = display_df.style.apply(highlight_side, axis=1).format({'주문 가격': '{:,.0f}', '수량': '{:,.0f}'})
                st.dataframe(styled_df, use_container_width=True, hide_index=True)'''

good_df_code = '''                combined_df = pd.concat([sell_orders, buy_orders])
                display_df = combined_df[['side', 'price', 'quantity', 'id']].copy()
                display_df.columns = ['방향', '주문 가격', '수량', 'ID']
                
                # pandas Styler 객체의 무거운 렌더링 오버헤드를 피하기 위해 Native dataframe 렌더링 사용
                st.dataframe(
                    display_df, 
                    use_container_width=True, 
                    hide_index=True,
                    column_config={
                        "주문 가격": st.column_config.NumberColumn(format="%d ₩"),
                        "수량": st.column_config.NumberColumn(format="%d 주")
                    }
                )'''

text = text.replace(bad_df_code, good_df_code)

with codecs.open('d:/aiworkspace/app/dashboard.py', 'w', encoding='utf-8') as f:
    f.write(text)
print("Dataframe styler replaced with native fast rendering.")
