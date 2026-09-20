with open('d:/aiworkspace/app/dashboard.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    if 'st.success("모든 일괄 주문이' in line:
        new_lines.append('                                            st.success("모든 일괄 주문이 성공적으로 전송되었습니다!\\n\\n" + "\\n".join(success_msgs))\n')
    elif 'st.success(f"{len(success_msgs)}건 주문 성공' in line:
        new_lines.append('                                            st.success(f"{len(success_msgs)}건 주문 성공:\\n\\n" + "\\n".join(success_msgs))\n')
    elif 'st.error(f"{len(fail_msgs)}건 주문 실패' in line:
        new_lines.append('                                        st.error(f"{len(fail_msgs)}건 주문 실패:\\n\\n" + "\\n".join(fail_msgs))\n')
    # 이전 Powershell 버그로 들어간 줄바꿈된 이상한 문자열을 무시
    elif line.strip().startswith('+ "\\n".join(success_msgs))') or line.strip().startswith('+ "\\n".join(fail_msgs))'):
        continue
    else:
        new_lines.append(line)

with open('d:/aiworkspace/app/dashboard.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
print('Fixed syntax errors 2')
