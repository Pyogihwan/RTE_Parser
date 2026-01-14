# SADS/SUDS AUTOSAR SWC 분석기

AUTOSAR Classic C 소스 코드를 분석하여 SWC(Software Component) 단위로 구조화된 SADS/SUDS CSV 파일을 생성하는 웹 애플리케이션입니다.

## 🚀 다른 PC에서 실행하는 방법

### 방법 1: 간단 실행 (권장)

#### Windows:
```bash
# 1. 이 폴더를 다른 PC로 복사
# 2. start.bat 파일 더블클릭
start.bat
```

#### Linux/Mac:
```bash
# 1. 이 폴더를 다른 PC로 복사
# 2. 터미널에서 실행
chmod +x start.sh
./start.sh
```

### 방법 2: Python 직접 실행
```bash
# 1. Python 3.8+ 설치 확인
python --version

# 2. 자동 실행 스크립트 실행
python run.py
```

### 방법 3: 수동 설치
```bash
# 1. 필요한 패키지 설치
pip install flask pandas pydantic

# 2. 애플리케이션 실행
python app.py
```

## 📋 시스템 요구사항

- **Python 3.8 이상**
- **인터넷 연결** (패키지 다운로드용)
- **2GB 이상의 RAM**
- **100MB 이상의 디스크 공간**

## 🎯 실행 후 사용법

1. **웹 브라우저 자동 열림**: http://localhost:5000
2. **C 소스 코드 디렉토리 경로 입력**:
   - Windows: `C:\project\source\`
   - Linux/Mac: `/home/user/project/`
3. **"분석 시작" 버튼 클릭**
4. **결과 확인 및 CSV 파일 다운로드**

## 📁 포터블 버전 만들기

다른 PC에서 인터넷 없이 실행하려면:

1. **오프라인 패키지 다운로드**:
```bash
pip download flask pandas pydantic -d packages/
```

2. **오프라인 설치 스크립트**:
```bash
pip install --no-index --find-links packages/ flask pandas pydantic
```

## 🔧 기능

- **C 코드 분석**: 지정된 디렉토리의 모든 .c 파일을 재귀적으로 분석
- **함수 추출**: 정적/전역 함수 및 시그니처 정보 추출
- **변수 추출**: 전역/정적 변수 및 타입 정보 추출  
- **RTE 인터페이스 추출**: Rte_Read, Rte_Write, Rte_Call 등 AUTOSAR RTE API 호출 분석
- **SWC 매핑**: 파일 경로 기반 Software Component 자동 추정
- **신뢰도 평가**: 추출 결과의 confidence 레벨(high/medium/low) 제공
- **CSV 내보내기**: SADS/SUDS 형식으로 구조화된 데이터 다운로드

## 설치

1. Python 3.8+ 설치 확인
2. 의존성 패키지 설치:
```bash
pip install -r requirements.txt
```

## 실행

```bash
python app.py
```

애플리케이션이 `http://localhost:5000`에서 시작됩니다.

## 사용법

1. 웹 브라우저에서 `http://localhost:5000` 접속
2. C 소스 코드가 있는 디렉토리 경로 입력
   - Windows: `C:\project\source\`
   - Linux/Mac: `/home/user/project/`
3. "분석 시작" 버튼 클릭
4. 분석 결과 확인 및 CSV 파일 다운로드

## API 엔드포인트

### POST /api/process

프로그래매틱 액세스를 위한 JSON API

**요청:**
```json
{
    "directory_path": "/path/to/c/source"
}
```

**응답:**
```json
{
    "success": true,
    "csv_filename": "sads_suds_extract_20240114_123456.csv",
    "download_url": "/download/sads_suds_extract_20240114_123456.csv",
    "total_files": 15,
    "total_functions": 45,
    "total_variables": 23,
    "total_rte_interfaces": 67,
    "swc_candidates": ["DemoSwc", "HWIOP", "IVC_P"],
    "issues": []
}
```

## 분석 규칙

### SWC 추정
- `Rte_<SwcName>.h` 또는 `Rte_<SwcName>.c` 파일명에서 SWC 이름 추출
- 상위 폴더명을 SWC 후보로 사용

### RTE API 패턴
- `Rte_Read_<Port>_<DataElement>`
- `Rte_Write_<Port>_<DataElement>`
- `Rte_Call_<Port>_<Operation>`
- `Rte_IRead_`, `Rte_IWrite_`, `Rte_IStatus_` 등

### 신뢰도 레벨
- **High**: libclang AST 기반 추출 또는 caller function 확인된 RTE 호출
- **Medium**: SWC 매핑은 확실하지만 심볼 추출이 regex fallback인 경우
- **Low**: regex fallback 모드로 추출되거나 SWC 매핑이 불확실한 경우

## 정확도 향상 팁

1. **libclang 사용**: clang python binding 설치 시 더 정확한 AST 분석 가능
2. **빌드 설정**: include path, defines, compiler flags 제공 시 정확도 향상
3. **파일 구조**: SWC별로 폴더 구조화 시 자동 매핑 정확도 향상

## 출력 CSV 컬럼

| 컬럼 | 설명 |
|------|------|
| swc | Software Component 이름 |
| kind | 종류 (function/variable/rte_interface) |
| name | 심볼 이름 |
| signature | 함수 시그니처 또는 변수 타입 |
| scope | 범위 (static/global/unknown) |
| file | 소스 파일 경로 |
| line | 라인 번호 |
| direction | RTE 방향 (read/write/call 등) |
| port | RTE 포트 이름 |
| data_element | 데이터 요소 이름 |
| callee | 호출된 함수 (Rte_Call의 경우) |
| caller_function | 호출자 함수 |
| confidence | 신뢰도 (high/medium/low) |
| evidence | 추출 근거 |

## 주의사항

- 정규식 fallback 모드에서는 매크로, 헤더, 조건부 컴파일 영향으로 정확도가 보장되지 않음
- 복잡한 프로젝트에서는 libclang 사용 권장
- 결과 검증 시 low/medium confidence 항목 중점 확인 필요

## 라이선스

이 프로젝트는 AUTOSAR SWC 분석을 위한 도구로 제공됩니다.
