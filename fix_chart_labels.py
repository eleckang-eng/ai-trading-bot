import codecs

with codecs.open('d:/aiworkspace/app/dashboard.py', 'r', encoding='utf-8') as f:
    text = f.read()

# 텍스트 라벨들 원래대로 복구
text = text.replace('view_mode = st.radio("보기 방식", ["📊 호가창 뷰", "📉 차트 뷰", "📝 목록 뷰"], horizontal=True)', 'view_mode = st.radio("보기 방식", ["📊 호가창 뷰 (현재가 중심 정렬)", "📉 시각화 차트 뷰 (분포)", "📝 일반 목록 뷰 (접수순)"], horizontal=True)')
text = text.replace('elif view_mode == "📊 호가창 뷰":', 'elif view_mode == "📊 호가창 뷰 (현재가 중심 정렬)":')
text = text.replace('elif view_mode == "📉 차트 뷰":', 'elif view_mode == "📉 시각화 차트 뷰 (분포)":')

with codecs.open('d:/aiworkspace/app/dashboard.py', 'w', encoding='utf-8') as f:
    f.write(text)
print("Chart labels restored.")
