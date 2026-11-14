@echo off
cd /d "D:\Python全栈AI答题小程序\backend"
.venv\Scripts\uvicorn.exe app.main:app --host 127.0.0.1 --port 8000 --reload
