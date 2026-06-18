# WeSeed AI Agent 개발 가이드

이 가이드는 WeSeed AI Agent 개발 환경 설정 및 구현 방법을 단계별로 설명합니다.

## 시작하기 전에 준비할 것들

1. **Python 설치하기**

   - [Python 공식 웹사이트](https://www.python.org/downloads/)에서 Python 3.12 이상 버전을 다운로드
   - 설치 시 "Add Python to PATH" 옵션을 반드시 체크해주세요!
   - 설치 확인: 명령 프롬프트(cmd)에서 아래 명령어 실행
     ```bash
     python --version
     ```

2. **VS Code 설치하기** (추천 개발 도구)

   - [VS Code 다운로드](https://code.visualstudio.com/download)
   - Python 확장 프로그램 설치: VS Code에서 Extensions(Ctrl+Shift+X) → 'Python' 검색 후 설치

3. **Git 설치하기**

   - [Git 다운로드](https://git-scm.com/downloads)
   - 설치 확인:
     ```bash
     git --version
     ```

4. **OpenAI API 키 발급받기**
   - [OpenAI 웹사이트](https://platform.openai.com/)에 가입
   - API 키 발급 받기 (Settings > API Keys)
   - 발급받은 키는 안전한 곳에 보관하세요!

## 프로젝트 시작하기

### 1. 프로젝트 다운로드

명령 프롬프트를 열고 아래 명령어를 순서대로 실행합니다:

```bash
# 원하는 폴더로 이동 (예: C드라이브의 MyProjects 폴더)
cd C:\MyProjects

# 프로젝트 복제
git clone [repository-url]
cd weseed-ai-agent
```

### 2. 가상환경 만들기

가상환경은 프로젝트별로 독립된 Python 환경을 만들어줍니다.

```bash
# 가상환경 생성
python -m venv venv

# 가상환경 활성화
# Windows의 경우:
venv\Scripts\activate

# macOS/Linux의 경우:
source venv/bin/activate

# 활성화 성공 시 (venv)가 명령줄 앞에 표시됩니다.
```

### 3. 필요한 패키지 설치하기

```bash
# pip 업그레이드
python -m pip install --upgrade pip

# 프로젝트에 필요한 패키지 설치
pip install -r requirements.txt
```

### 4. 환경 설정하기

1. 프로젝트 폴더에 `.env` 파일 만들기
2. 아래 내용을 복사하여 `.env` 파일에 붙여넣기
   ```env
   DEBUG=True
   PROJECT_NAME="WeSeed AI Agent"
   PROJECT_DESCRIPTION="AI Agent 서비스"
   VERSION="1.0.0"
   OPENAI_API_KEY="여기에_발급받은_API_키를_입력하세요"
   ```

### 5. 서버 실행하기

```bash
python main.py
```

- 서버가 정상적으로 실행되면 `http://localhost:8000`으로 접속할 수 있습니다.
- API 문서는 `http://localhost:8000/docs`에서 확인할 수 있습니다.

서버가 실행된 후, 아래 curl 명령어로 API를 테스트해볼 수 있습니다:

```bash
# 채팅 API 테스트 (Windows CMD)
curl -X POST http://localhost:8000/api/v1/chat/ask ^
-H "Content-Type: application/json" ^
-H "X-API-KEY: weseed-ai-dev-2025@dev" ^
-d "{\"text\": \"hello, world\"}"

# 채팅 API 테스트 (PowerShell)
curl -X POST http://localhost:8000/api/v1/chat/ask `
-H "Content-Type: application/json" `
-H "X-API-KEY: weseed-ai-dev-2025@dev" `
-d '{"text": "hello, world"}'

# 채팅 API 테스트 (Linux/macOS)
curl -X POST http://localhost:8000/api/v1/chat/ask \
-H "Content-Type: application/json" \
-H "X-API-KEY: weseed-ai-dev-2025@dev" \
-d '{"text": "hello, world"}'
```

## 프로젝트 구조 이해하기

```
프로젝트 폴더/
├── api/                    # API 관련 코드
│   └── chat.py            # 채팅 기능 구현
├── core/                  # 핵심 기능들
│   ├── auth.py           # 사용자 인증
│   ├── cache.py          # 데이터 임시 저장
│   ├── exceptions.py     # 예외 처리
│   ├── i18n.py          # 다국어 지원
│   ├── middleware.py    # 미들웨어
│   ├── session.py      # 세션 관리
│   ├── settings.py     # 환경 설정
│   └── utils.py        # 유틸리티 함수
├── model/               # 데이터 모델
│   └── schemas.py      # 데이터 스키마 정의
├── service/            # 비즈니스 로직
│   └── services.py     # 서비스 구현
├── resources/          # 리소스 파일들
│   └── ko.json        # 한국어 메시지
├── reference/         # 참조 문서
│   └── checklist-for-code-review.md  # 코드 리뷰 체크리스트
├── tests/             # 테스트 코드
│   └── test_api.py    # API 테스트
├── logs/              # 로그 파일
│   └── app.log       # 애플리케이션 로그
├── main.py           # 애플리케이션 진입점
├── pyproject.toml    # 프로젝트 설정
└── requirements.txt  # 프로젝트 의존성 목록
```

## 새로운 기능 추가하기

1. **채팅 기능 구현 예시**

   - `api/chat.py` 파일에서 새로운 엔드포인트 추가
   - `schemas.py`에 필요한 데이터 모델 정의
   - `services.py`에 비즈니스 로직 구현

2. **테스트 작성하기**

   ```bash
   # 테스트 실행
   pytest

   # 테스트 커버리지 확인
   pytest --cov
   ```

## 문제 해결하기

### 자주 발생하는 오류와 해결 방법

1. **ModuleNotFoundError 발생 시**

   - 가상환경이 활성화되어 있는지 확인 ((venv) 표시 확인)
   - `pip install -r requirements.txt` 다시 실행

2. **서버 실행 오류 시**

   - `.env` 파일이 프로젝트 루트 폴더에 있는지 확인
   - OpenAI API 키가 올바르게 입력되었는지 확인
   - 포트 8000번이 사용 중인 경우, 다른 프로그램 종료 후 재시도

3. **OpenAI API 오류 시**
   - API 키가 올바른지 확인
   - 키 잔액이 남아있는지 확인
   - 인터넷 연결 상태 확인

### 코드 품질 관리

```bash
# 코드 스타일 자동 수정
black .

# 타입 체크
mypy .

# 보안 검사
bandit -r .
```

## 도움이 필요하신가요?

1. 프로젝트 이슈 트래커 확인하기
2. 개발자 커뮤니티에 질문하기
3. 공식 문서 참고하기
   - FastAPI 문서: https://fastapi.tiangolo.com/
   - OpenAI API 문서: https://platform.openai.com/docs/
