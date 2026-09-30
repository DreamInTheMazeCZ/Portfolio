# 프로젝트 구조와 산출물 관리

## 목차

1. [디렉터리 레이아웃](#1-디렉터리-레이아웃)
2. [계층별 책임](#2-계층별-책임)
3. [config.py](#3-configpy)
4. [FastAPI 패턴](#4-fastapi-패턴)
5. [DB 계층](#5-db-계층)
6. [비동기 처리](#6-비동기-처리)
7. [산출물 관리](#7-산출물-관리)
8. [커밋 컨벤션](#8-커밋-컨벤션)

---

## 1. 디렉터리 레이아웃

소스는 전부 `src/` 아래에, repo 루트에는 빌드·문서 파일만 둔다.

```
<repo>/
├── src/
│   ├── main.py             # 앱 수명주기, 라우터 등록, 상태 확인
│   ├── config.py           # .env 로드, 환경변수 + 비즈니스 상수
│   ├── .env                # 실제 설정값 (git 제외)
│   ├── api/                # FastAPI 라우터
│   ├── service/            # 외부 시스템 연동 (ML API 등)
│   ├── db/                 # 영속 계층
│   ├── model/              # pydantic 스키마, 응답 조립
│   ├── subscribe/          # 메시지 버스 구독/핸들러
│   └── <domain>/           # 도메인 계산 로직 (예: rent/)
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── README.md               # 한글 사용자 문서
├── CLAUDE.md               # Claude Code용 영문 가이드
├── AGENTS.md               # 타 에이전트용 영문 가이드
├── .gitignore
└── .dockerignore
```

### 중요한 전제 두 가지

**임포트 루트가 repo 루트가 아니라 `src/`다.** 그래서 실행도 `cd src` 후에 한다. 새 모듈은 `from db.database import pg`처럼 `src/` 기준 절대 경로로 임포트한다.

**`__init__.py`를 두지 않는다.** 하위 디렉터리는 암묵적 네임스페이스 패키지로 동작한다. 새 패키지를 만들 때도 빈 `__init__.py`를 추가하지 않는다.

### 패키지 이름

기능 단위 단수 명사를 쓴다 (`api`, `service`, `db`, `model`, `rent`). 파일명이 패키지명과 같아도 무방하다 (`model/model.py`, `subscribe/subscribe.py`) — 이 코드베이스에서 확립된 형태다.

---

## 2. 계층별 책임

| 디렉터리 | 하는 일 | 하지 않는 일 |
| --- | --- | --- |
| `main.py` | 앱 생성, lifespan, 미들웨어, 라우터 등록 | 비즈니스 로직 |
| `api/` | 요청 수신, 모드 분기, 도메인 함수 호출 | 계산, DB 접근, 외부 호출 |
| `<domain>/` | 계산·규칙 적용, DB/외부 조회 조합 | HTTP 관심사 |
| `service/` | 외부 API 호출과 응답 가공 | 도메인 규칙 판단 |
| `db/` | 커넥션, 쿼리 실행, 쿼리 조립 | 비즈니스 규칙 |
| `model/` | pydantic 요청 스키마, 응답 딕셔너리 조립 | 계산 |
| `subscribe/` | 메시지 수신, 핸들러 오케스트레이션 | 계산, 쿼리 문자열 |

라우터는 얇게 유지한다 — 받은 값을 풀고, 분기하고, 도메인 함수에 넘기는 것까지다.

```python
@router.post('/calc')
def calc_rent_fee(requests_data:RequestCalculator) -> dict:
    '''
    임대료 산출 API
    mode 0 : 기준가액 기반 산출
    mode 1 : ML 모델 예측가 기반 산출 (default)
    mode 2 : 통합 반환 모드
    '''

    model_name = requests_data.model_name
    additional_ratio = requests_data.additional_ratio
    mode = requests_data.mode

    # ML 학습모델 기반 모드
    if mode == 1:
        return calc_ml_predict_fee(model_name, additional_ratio)
    # 기준가액 기반 모드
    elif mode == 0:
        return calc_standard_price_fee(model_name)
    else:
        # 통합 모드
        return {
            "standard_price_response" : calc_standard_price_fee(model_name),
            "ml_price_response" : calc_ml_predict_fee(model_name, additional_ratio)
        }
```

---

## 3. config.py

`src/config.py` 한 파일에 **환경변수와 비즈니스 상수를 모두** 모은다. 흩어진 매직 넘버를 코드에서 없애려는 의도다.

```python
from dotenv import load_dotenv
import os

load_dotenv()

# API Config
API_URL = os.getenv('API_URL', 'http://localhost:8000')

# DB Config
DB_NAME = os.getenv('DB_NAME')
DB_PORT = int(os.getenv('DB_PORT'))

# NATS Config
NATS_SV = os.getenv('NATS_SV')

# 임대료 산출 설정
RENT_THRESHOLDS = [0, 1000000, ...]
RENT_FEES = [10000, 12000, ...]
RENT_RATIO = round(float(os.getenv('RENT_RATIO')), 2)
```

### 규칙

- 섹션 주석으로 나눈다. 인프라 설정은 영문(`# DB Config`), 도메인 설정은 한글(`# 임대료 산출 설정`).
- **필수값에는 기본값을 주지 않는다.** `int(os.getenv('DB_PORT'))`는 값이 없으면 임포트 시점에 터진다. 이게 의도다 — 잘못된 설정으로 뜬 뒤 첫 요청에서 실패하는 것보다 시작 단계에서 죽는 편이 낫다.
- 선택값에만 `os.getenv('X', 기본값)`을 쓴다.
- `.env`는 `src/.env`에 둔다. `load_dotenv()`와 docker-compose의 `env_file` 둘 다 이 경로를 본다.
- 구간표는 리스트 두 개(경계값·해당값)를 나란히 두고 `bisect_right`로 찾는다.

---

## 4. FastAPI 패턴

### 앱 조립

`main.py`는 lifespan으로 장기 자원의 생애를 소유한다.

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    '''
    앱 시작 시 NATS 연결 및 구독을 자동 시작하고,
    종료 시 정리한다. (단일 프로세스 상시 구동)
    '''
    nc = NATS()
    await nc.connect(...)
    await subscribe(nc)
    app.state.nc = nc

    yield  # ── 앱이 요청을 받는 동안 구독 유지 ──

    if nc.is_connected:
        await nc.drain()


app = FastAPI(lifespan=lifespan)
```

자원 핸들은 `app.state`에 실어 다른 곳에서 꺼내 쓴다.

### 라우터

기능별 모듈에 `router = APIRouter()`를 만들고, `main.py`에서 prefix와 tags를 붙여 등록한다. prefix는 라우터 쪽이 아니라 **등록하는 쪽**에서 준다.

```python
# api/rent_fee.py
router = APIRouter()

@router.post('/calc')
def calc_rent_fee(...): ...
```

```python
# main.py
app.include_router(rent_fee.router, prefix='/api/rent', tags=['Rent'])
```

### 엔드포인트 함수

I/O 대기가 없으면 `async def`가 아니라 **동기 `def`**로 둔다 (FastAPI가 스레드풀에서 돌린다). 반환형은 `dict`.

### 요청 스키마

`model/` 안 pydantic `BaseModel`. 제약은 `Field(default=, ge=, le=)`로 걸고, 의미는 한글 주석으로 단다.

```python
class RequestCalculator(BaseModel):
    model_name:str   # 형식명
    # ML 기능 예측값 가산율 preds * (1 + (additional_ratio / 100)), 기본값 0
    additional_ratio:int = Field(default=0, ge=-100, le=100)
    # 호출 모드 - 0 : 기준가액 기반, 1 : ML 기반 (default), 2 : 통합
    mode:int = Field(default=1, ge=0, le=2)
```

### 응답

응답 pydantic 모델 대신 **조립 함수가 딕셔너리를 만든다.** 요청 에코와 결과를 나눠 담는 중첩 구조다.

```python
    return {
        'request':
            {
                'model_name': model_name
            },
        'response':
            {
                'predict_price': predict_price,
                'rent_fee': rent_fee,
                'lower_rent_fee': lower_rent_fee,
                'upper_rent_fee': upper_rent_fee,
                'source': source
            }
        }
```

이 함수를 한 곳에 두면 성공·실패 경로가 같은 모양을 내보내게 강제된다.

### 상태 확인 엔드포인트

장기 연결을 쓰는 서비스에는 연결 상태를 알려주는 GET을 둔다.

```python
@app.get('/api/tradeSubscribe')
def trade_subscribe() -> JSONResponse:
    '''
    직거래 구독 상태 확인 API
    '''
    connected = getattr(app.state, 'nc', None) is not None and app.state.nc.is_connected
    return JSONResponse(
        status_code=200,
        content={'detail': 'Subscription running' if connected else 'Disconnected'},
    )
```

---

## 5. DB 계층

psycopg2를 직접 쓴다. ORM도, 커넥션 풀도 두지 않는다.

### 구조

`db/database.py`가 커넥션과 실행을, `db/insert_query.py`가 쿼리 조립을 맡는다. 클래스는 접속 정보를 비공개로 들고, 호출당 커넥션을 열고 닫는다.

```python
class PostgreSQL:
    def __init__(self):
        self.__conn_info = {'dbname': DB_NAME, 'user': DB_USER, ...}

    def __connect_postgresql(self):
        '''
        DB Connection
        데이터베이스 연결
        '''
        self.conn = psycopg2.connect(**self.__conn_info)
        return self.conn

    def query_execute_params(self, query, params):  # INSERT/UPDATE
    def select_execute_params(self, query, params):  # SELECT

pg = PostgreSQL()
```

메서드는 두 개로 나눈다: 쓰기는 `commit`/`rollback`하고 `True`를 반환, 읽기는 `fetchall()` 결과를 반환. 둘 다 `finally`에서 커서와 커넥션을 닫는다.

### 쿼리 조립

INSERT는 페이로드 딕셔너리의 키에서 컬럼과 플레이스홀더를 만든다.

```python
    columns = insert_data.keys()
    query = f"""
    INSERT INTO ml_trade_price_analysis ({', '.join(columns)})
    VALUES ({', '.join([f'%({col})s' for col in columns])})
    """
```

**대가를 알고 쓴다**: 생산자가 보내는 필드 구성이 곧 테이블 컬럼 구성과 직결된다. 예상 못 한 키가 오면 SQL이 깨진다. 내부 신뢰 경로에서만 쓰고, 외부 입력에는 컬럼 화이트리스트를 둔다.

### 중복 방지

애플리케이션에서 검사하지 않고 **DB 복합 기본키로 막는다.** 어떤 컬럼이 키인지는 삽입 함수 독스트링에 `*`로 명시한다.

---

## 6. 비동기 처리

### 블로킹 라이브러리는 스레드로

psycopg2는 동기다. 이벤트 루프 위에서 부르면 루프가 멈추므로 `asyncio.to_thread`로 감싼다.

```python
        await asyncio.to_thread(insert_ai_trade_price, sub_data)
```

### 메시지 핸들러

구독 함수는 콜백만 등록하고 **즉시 반환**한다 (블로킹하지 않는다). 연결 유지와 재접속은 클라이언트에 맡긴다.

```python
async def subscribe(nc: NATS):
    '''
    NATS 농민카 직거래 데이터 수신 및 DB 적재, 시세예측 처리

    콜백을 이벤트 루프에 등록만 하고 반환한다(블로킹하지 않음).
    연결 유지 및 자동 재접속은 전달받은 NATS 클라이언트가 담당한다.
    '''
    async def message_handler(msg):
        ...

    await nc.subscribe("nc.trade.review", cb=message_handler)
```

핸들러는 중첩 함수로 두어 `subscribe`의 스코프를 공유한다.

### 재접속

무한 재시도(`max_reconnect_attempts=-1`)에 상태 콜백을 붙여 로그를 남긴다.

```python
    async def on_disconnected():
        print("[WARN] NATS 연결 끊김 — 재접속 시도 중")

    await nc.connect(
        servers=[NATS_SV],
        max_reconnect_attempts=-1,
        disconnected_cb=on_disconnected,
        reconnected_cb=on_reconnected,
        error_cb=on_error,
    )
```

### 주의

`async with httpx.AsyncClient()`를 열었으면 `await client.post(...)`를 써야 한다. `service/preds.py`에 클라이언트를 열고 동기 `httpx.post(...)`를 부르는 곳이 있는데 **알려진 부채**다. 새 코드에 따라 하지 않는다.

---

## 7. 산출물 관리

### README.md — 한글, 운영자용

순서가 정해져 있다: 한 문단 개요 → ASCII 처리 흐름도 → 번호 매긴 단계 설명 → 산출 규칙 표 → 요구사항 → 환경변수(`dotenv` 코드블록) → 실행(로컬/Docker) → API 표 → 프로젝트 구조 트리 → 데이터베이스.

흐름도는 이미지가 아니라 코드블록 안의 박스 그림으로 그린다. 텍스트라 diff로 추적되기 때문이다.

```
NATS (nc.trade.review)
        │  직거래 매물 수신
        ▼
┌───────────────────────────────────────┐
│  message_handler                       │
│  ① 원본 데이터 적재                     │
└───────────────────────────────────────┘
```

계산식·API 목록은 마크다운 표로. 주의사항은 `>` 인용으로.

### CLAUDE.md / AGENTS.md — 영문, 에이전트용

README와 **독자가 다르다.** 사용법이 아니라 코드베이스의 구조와 함정을 적는다. 구성: Overview → Commands → Configuration → Architecture(번호 매긴 모듈별 설명) → **Gotchas**.

`Gotchas` 절이 핵심이다. 주석과 실제 동작이 어긋난 곳, 섞여 있는 비동기/동기, 암묵적 결합처럼 **코드만 봐서는 놓치는 것**을 적는다.

두 파일은 같은 내용을 담되 대상 도구만 다르다 (`CLAUDE.md`는 Claude Code, `AGENTS.md`는 그 외). 한쪽을 고치면 다른 쪽도 맞춘다.

### requirements.txt — 정확한 핀 고정

범위가 아니라 `==`로 못 박는다. 재현 가능한 빌드를 위해서다.

```
fastapi==0.115.6
uvicorn[standard]==0.34.0
nats-py==2.9.0
psycopg2-binary==2.9.10
httpx==0.28.1
python-dotenv==1.0.1
```

### Dockerfile — 한글 주석, 레이어 캐시 의식

```dockerfile
FROM python:3.12-slim

# 파이썬 런타임 설정
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# 의존성 먼저 설치 (레이어 캐시 활용)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 소스 복사 (임포트가 src 기준이므로 src 내부를 작업 디렉터리로 사용)
COPY src/ ./src/
WORKDIR /app/src
```

`PYTHONUNBUFFERED=1`은 선택이 아니다 — `print` 로깅이 이것에 의존한다.

### docker-compose.yml

이미지·컨테이너 이름을 명시하고, `restart: unless-stopped`로 상시 구동시킨다. 호스트 포트는 겹치지 않는 대역을 골라 컨테이너 8000에 매핑한다.

```yaml
services:
  ml-trade-price:
    build: .
    image: ncai-ml-trade-price-analysis:latest
    container_name: ncai-ml-trade-price-analysis
    restart: unless-stopped
    ports:
      - "19220:8000"
    env_file:
      - ./src/.env
```

### .gitignore / .dockerignore

`.env`, 로그, `__pycache__`는 git에서 뺀다. 이미지에는 문서(`*.md`)와 빌드 파일까지 빼서 가볍게 만든다.

### 없는 것

테스트 스위트, 린터 설정, CI 파이프라인, 타입 체커 설정이 없다. **요청 없이 추가하지 않는다.** 필요해 보이면 먼저 물어본다.

---

## 8. 커밋 컨벤션

```
<접두사>: <한글 설명>
```

접두사는 첫 글자만 대문자인 영문, 콜론 뒤 한 칸, 설명은 한글 한 줄.

| 접두사 | 쓰는 때 |
| --- | --- |
| `Add:` | 신규 기능·파일 추가 |
| `Fix:` | 버그 수정 |
| `Mod:` | 기존 동작 변경·개선 |
| `Docs:` | 문서만 변경 |

실제 이력:

```
Mod: ML 기반 가산율 추가 (-100 ~ 100) 및 통합 모드 (mode=2) 추가
Add: 임대료 계산 로직 및 API 추가
Fix: 사용연수 변환 로직 수정
Docs: 기능 가이드 및 CLAUDE.md 파일 커밋
Add: 직거래 데이터 수신 및 ML 시세예측 최초 커밋
```

값 범위나 플래그가 바뀌면 괄호로 구체적인 값을 적는다 (`(-100 ~ 100)`, `(mode=2)`). 나중에 어느 커밋에서 바뀌었는지 찾기 쉽다.

Conventional Commits(`feat:`, `chore:` 소문자)는 쓰지 않는다. 본문이나 푸터도 쓰지 않는 것이 기본이다 — 제목 한 줄로 끝낸다.
