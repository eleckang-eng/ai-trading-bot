import codecs

with codecs.open('d:/aiworkspace/app/dashboard.py', 'r', encoding='utf-8') as f:
    text = f.read()

# if 조건문 문자열 완벽히 일치시키기
bad_if_1 = 'if view_mode == "📊 호가창 뷰":'
good_if_1 = 'if view_mode == "📊 호가창 뷰 (현재가 중심 정렬)":'
text = text.replace(bad_if_1, good_if_1)

bad_if_2 = 'elif view_mode == "📉 차트 뷰":'
good_if_2 = 'elif view_mode == "📉 시각화 차트 뷰 (분포)":'
text = text.replace(bad_if_2, good_if_2)

with codecs.open('d:/aiworkspace/app/dashboard.py', 'w', encoding='utf-8') as f:
    f.write(text)
print("View mode condition strings fixed.")
