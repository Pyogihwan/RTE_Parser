@echo off
chcp 65001 >nul
title SADS/SUDS AUTOSAR SWC 분석기

echo ========================================
echo 🔧 SADS/SUDS AUTOSAR SWC 분석기
echo ========================================
echo.

echo Python 설치 확인 중...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python이 설치되지 않았습니다.
    echo https://www.python.org/downloads/ 에서 Python 3.8 이상을 설치해주세요.
    pause
    exit /b 1
)

echo ✅ Python 설치 확인 완료
echo.

echo 필요한 패키지 설치 중...
python -m pip install flask pandas pydantic
if errorlevel 1 (
    echo ❌ 패키지 설치 실패
    pause
    exit /b 1
)

echo ✅ 패키지 설치 완료
echo.

echo 🚀 웹 서버 시작 중...
echo 서버 주소: http://localhost:5000
echo 종료하려면 Ctrl+C를 누르세요
echo.

python run.py

pause
