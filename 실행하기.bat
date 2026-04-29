@echo off
echo ======================================================
echo   쿠팡 카페 자동 포스팅 봇을 실행합니다.
echo ======================================================
echo.
echo 1. 가상환경 확인 및 라이브러리 설치 중...
pip install -r requirements.txt

echo.
echo 2. 서버 실행 중... (창을 닫지 마세요)
echo 주소: http://localhost:8000
echo.
python main.py
pause
