import codecs

with codecs.open('d:/aiworkspace/app/dashboard.py', 'r', encoding='utf-8') as f:
    text = f.read()

bad_chart = '''            elif view_mode == "📉 차트 뷰":
                chart_data = df_positions[['price', 'quantity', 'side']].copy()
                chart_data['color'] = chart_data['side'].map({'매도': '#4A90E2', '매수': '#E24A4A'})
                st.scatter_chart(data=chart_data, x='price', y='quantity', color='color', use_container_width=True)'''

good_chart = '''            elif view_mode == "📉 차트 뷰":
                chart_data = df_positions[['price', 'quantity', 'side']].copy()
                # color='side'로 지정하면 Streamlit이 매수/매도를 자동 그룹핑하고, size='quantity'로 주문량에 따라 점 크기를 표시합니다.
                st.scatter_chart(data=chart_data, x='price', y='quantity', color='side', size='quantity', use_container_width=True)'''

text = text.replace(bad_chart, good_chart)

with codecs.open('d:/aiworkspace/app/dashboard.py', 'w', encoding='utf-8') as f:
    f.write(text)
print("Chart view fixed.")
