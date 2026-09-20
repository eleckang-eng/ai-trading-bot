' Windows 백그라운드 무인 실행 스크립트
' 창(콘솔) 없이 백그라운드에서 완전히 독립적으로 자동매매 엔진(main.py)을 구동합니다.
Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "D:\aiworkspace"
WshShell.Run "python main.py", 0, False
Set WshShell = Nothing

