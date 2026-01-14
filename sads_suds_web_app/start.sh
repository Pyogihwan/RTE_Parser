#!/bin/bash

echo "========================================"
echo "🔧 SADS/SUDS AUTOSAR SWC 분석기"
echo "========================================"
echo

# Python 설치 확인
echo "Python 설치 확인 중..."
if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    echo "❌ Python이 설치되지 않았습니다."
    echo "https://www.python.org/downloads/ 에서 Python 3.8 이상을 설치해주세요."
    exit 1
fi

# Python 명령어 결정
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
else
    PYTHON_CMD="python"
fi

echo "✅ Python 설치 확인 완료: $PYTHON_CMD"
echo

# 필요한 패키지 설치
echo "필요한 패키지 설치 중..."
$PYTHON_CMD -m pip install flask pandas pydantic
if [ $? -ne 0 ]; then
    echo "❌ 패키지 설치 실패"
    exit 1
fi

echo "✅ 패키지 설치 완료"
echo

# 서버 시작
echo "🚀 웹 서버 시작 중..."
echo "서버 주소: http://localhost:5000"
echo "종료하려면 Ctrl+C를 누르세요"
echo

$PYTHON_CMD run.py
