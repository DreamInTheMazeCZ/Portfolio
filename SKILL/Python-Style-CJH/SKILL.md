---
name: python-style-cjh
description: 이 사용자(CJH)의 Python 코딩·데이터 작업 스타일 — 한글 독스트링/주석, `[DEBUG]`/`[INFO]`/`[WARN]`/`[ERROR]` 로깅, 압축형 import, 콜론 무공백 타입힌트, 계층별 패키지 구조, pandas/DB 처리 관례, 연구노트 YYMM 회차와 데이터 파일 이름 규칙, `Add:`/`Fix:`/`Mod:`/`Docs:` 한글 커밋. Python 파일이나 주피터 노트북을 만들거나 수정할 때, FastAPI 라우터·pydantic 모델·DB 조회/적재 코드·외부 API 연동을 작성할 때, pandas로 데이터를 가공하거나 DataFrame을 다루거나 엑셀/CSV를 읽고 쓸 때, ML 학습·전처리·증강 코드를 쓸 때, 프로젝트 구조를 잡거나 config/requirements/Dockerfile/README를 다룰 때, 실험 결과 파일 이름을 정하거나 커밋 메시지를 쓸 때 반드시 먼저 읽을 것. 사용자가 "스타일"을 명시하지 않아도 Python·데이터 작업이면 적용한다.
---

# CJH Python 스타일

이 사용자의 코드는 **읽는 사람이 한국어 사용자**라는 전제 위에 서 있다. 주석과 독스트링, 로그 메시지가 전부 한글인 이유가 그것이다. 영어로 바꾸면 스타일 위반일 뿐 아니라 실제로 덜 읽힌다.

동시에 **식별자·라이브러리 용어·SQL·로그 레벨 태그는 영문 그대로** 둔다. 한글은 설명에, 영문은 코드에 쓴다는 경계가 일관되게 지켜진다.

작업 시작 전 이 문서를 읽고, 세부 규칙이 필요하면:

- `references/conventions.md` — 명명·주석·독스트링·로깅·에러 처리·타입힌트 상세와 예시
- `references/structure.md` — 패키지 구조, config, FastAPI 계층, 산출물(README/커밋/Docker/의존성) 관리
- `references/data.md` — **DB 접근·조회·대량 삽입, pandas 데이터 처리, 파일 입출력.** DB에서 데이터를 꺼내거나 DataFrame을 다루면 반드시 읽을 것
- `references/research.md` — **노트북·실험 코드, 연구노트 회차 이름, 데이터 파일 이름.** `.ipynb`를 만들거나 데이터 산출물을 저장하면 읽을 것

## 핵심 규칙

기존 파일을 고칠 때는 **주변 코드를 먼저 보고 그 결을 따른다.** 아래는 주변에 근거가 없을 때의 기본값이다.

### 1. 한글로 쓰는 것 / 영문으로 쓰는 것

| 한글 | 영문 |
| --- | --- |
| 독스트링, 주석, 로그 메시지, README, 커밋 설명 | 변수·함수·클래스·모듈명, SQL, 라이브러리 API, `[DEBUG]` 등 레벨 태그, 커밋 접두사 |

### 2. 독스트링은 `'''`, 한글, 짧게

모든 함수·메서드에 붙인다. `"""`가 아니라 **작은따옴표 3개**다.

섹션 표기는 **코드 성격에 따라 갈린다.** 인자만 보고 무엇이 필요한지 알 수 있으면 생략하고, DataFrame처럼 시그니처가 말해주지 않으면 적는다.

| 코드 | 형식 |
| --- | --- |
| 서비스·API·DB 계층 | 섹션 없이 한글 한 줄 (필요하면 두세 줄) |
| ML·데이터 처리 | `Parameter` / `Output` / `Return` 평문 레이블 |
| 연구 노트북·분석 스크립트 | Google 스타일 `Args:` / `Returns:`, 타입은 괄호에 |

기본은 첫 줄짜리다.

```python
def calc_standard_price_fee(model_nm:str) -> dict:
    '''
    기준가액 기반 임대료 산출 함수
    '''
```

놓치면 사고나는 전제는 `*`로 단다.

```python
    '''
    직거래 수신 데이터 시세예측 후
    ml_trade_price_analysis 테이블 데이터 삽입

    * ml_trade_price_analysis 테이블은 형식명 + 제조연도 + 주행시간 기본키 설정으로 중복 인서트 방지
    '''
```

### 3. 로깅은 `print`, `[레벨] 한글 설명 - 값`

상시 서비스·짧은 배치·노트북은 `print`를 쓴다. 컨테이너가 `PYTHONUNBUFFERED=1`로 돌아 stdout이 곧 로그이기 때문이다. **장시간 학습이나 스케줄 배치(Airflow 등)에서만** `logging` + `TimedRotatingFileHandler`로 올린다 (`encoding='utf-8'` 필수 — 한글이 깨진다). 어느 쪽이든 메시지 형식은 같다.

```python
print("[INFO] 구독 시작 — 상시 구동")
print(f"[DEBUG] 수신 데이터 {subject} : {data}")
print(f"[ERROR] ML 예측 실패 - {e}")
```

레벨은 넷뿐이다: `[DEBUG]` 정상 흐름 추적 · `[INFO]` 수명주기 이벤트 · `[WARN]` 자동 복구되는 이상 · `[ERROR]` 실패. 값을 덧붙일 땐 ` - ` 또는 ` : `로 잇는다.

### 4. import — `from` 블록 먼저, 압축 `import` 마지막

```python
from db.insert_query import insert_ai_trade_price, insert_ml_trade_price
from config import NATS_SV, NATS_USER, NATS_PW
from service.preds import pred_price

from nats.aio.client import Client as NATS

import asyncio, json
```

`from ... import ...`를 출처별로 묶어 빈 줄로 나누고, 이름 없는 `import`는 **맨 아래에 쉼표로 한 줄에 몰아쓴다.** PEP 8은 이를 권하지 않지만 이 코드베이스의 확립된 관행이며, 파일 상단을 짧게 유지하려는 의도다. 경로는 `src/` 기준 절대 임포트다 (상대 임포트 `.`를 쓰지 않는다).

### 5. 타입힌트는 콜론 무공백, 반환형은 공백

```python
def calc_ml_predict_fee(model_nm:str, additional_ratio:int) -> dict:
```

`model_nm:str`처럼 콜론 뒤를 붙이고, `-> dict`는 띄운다. 신규 코드에는 반환형을 반드시 단다.

### 6. 주석은 다음 블록이 무엇을 하는지 한글로

코드가 *무엇인지*가 아니라 **왜/무슨 단계인지**를 적는다.

```python
        # 값 스케일링
        std_price = std_price * 1000

        # 이진 탐색
        idx = bisect_right(RENT_THRESHOLDS, std_price) - 1
```

처리 단계가 굵게 갈리는 지점은 구분선을 쓴다.

```python
        # ===== ===== ===== 수신 데이터 DB 적재 ===== ===== =====
```

상수·필드의 의미나 범위는 뒤에 붙인다.

```python
    model_name:str   # 형식명
    # 호출 모드 - 0 : 기준가액 기반, 1 : ML 기반 (default), 2 : 통합
    mode:int = Field(default=1, ge=0, le=2)
```

### 7. 에러 처리는 계층에 따라 갈린다

`except Exception as e:`로 받고 — 맨 `except:`는 쓰지 않는다 — 계층별로 다르게 끝낸다.

- **인프라 계층**(DB·커넥션): `[ERROR]` 출력 후 `raise`로 올린다. 삼키면 데이터 유실을 모른 채 지나간다.
- **도메인/응답 계층**(산출·API): 로그를 남기고 **형태가 같은 안전 기본값**을 반환한다. 호출자가 응답 구조를 신뢰할 수 있어야 하기 때문이다.

```python
    except Exception as e:
        print(e)
        return make_rent_response(model_nm, 0, 0, 'standard_price')
```

빈 `except: pass`는 쓰지 않는다. (기존 `subscribe.py`에 남아 있는 것은 알려진 부채이며 따라 할 본보기가 아니다.)

### 8. 문자열은 작은따옴표, 값 삽입은 f-string

딕셔너리 키·짧은 리터럴은 `'...'`. SQL은 `f'''...'''` 여러 줄로, 값은 **반드시 파라미터 바인딩**(`%s` / `%(col)s`)으로 넘긴다 — f-string에 값을 직접 끼워 넣으면 SQL 인젝션이다.

### 9. 설정과 상수는 전부 `config.py`

환경변수도, 비즈니스 상수(구간표·비율)도 한곳에 모으고 섹션 주석으로 나눈다. 필수값은 `int(...)`처럼 임포트 시점에 깨지게 두어 **시작 단계에서 바로 실패**시킨다.

```python
# DB Config
DB_PORT = int(os.getenv('DB_PORT'))

# 임대료 산출 설정
RENT_THRESHOLDS = [...]
```

### 10. 커밋은 `접두사: 한글 설명`

`Add:` 신규 · `Fix:` 버그 수정 · `Mod:` 기존 동작 변경 · `Docs:` 문서. 접두사는 대문자로 시작하는 영문, 설명은 한글 한 줄이다.

```
Add: 임대료 계산 로직 및 API 추가
Mod: ML 기반 가산율 추가 (-100 ~ 100) 및 통합 모드 (mode=2) 추가
```

### 11. DB는 2층, 값은 항상 바인딩

커넥션을 다루는 베이스 클래스(`PostgreSQL`)와 쿼리 하나에 메서드 하나인 서브클래스(`QueryMethod(PostgreSQL)`)로 나눈다. SQL 문자열이 호출자 코드에 새지 않게 하려는 것이다. 조회 결과를 DataFrame으로 만들 땐 컬럼명 리스트를 쿼리 바로 위에 두고 `pd.DataFrame(result, columns=col_nm)`로 붙인다. 대량 삽입은 `executemany` + 100건 청킹.

**값은 예외 없이 `%s` / `%(col)s`로 바인딩한다.** 기존 프로젝트 일부에 f-string으로 값을 끼워 넣은 쿼리가 남아 있으나 SQL 인젝션이며 복제 대상이 아니다. 자세한 것은 `references/data.md`.

### 12. pandas는 한 줄에 한 연산

이름 없는 `df` 대신 `calc_df`, `train_data`처럼 내용이 드러나는 이름을 쓴다. 여러 줄 체이닝이나 `inplace=True` 대신 **재할당하고, 각 줄 위에 한글 주석**을 단다. 컬럼은 대괄호로만 접근한다.

```python
    # 연식당 사용시간 산출
    calc_df['used_time_per_year'] = round((df['driving_time'] / df['manufacture_year']).fillna(0), 1)
```

## 하지 않는 것

이 코드베이스가 **의도적으로 채택하지 않은** 것들이다. 개선처럼 보여도 요청 없이 끌어들이지 않는다.

- 구조화 로깅(JSON 로그 등) (→ `[레벨] 한글 설명 - 값`)
- 테스트 프레임워크, 린터, 포매터 (repo에 설정이 없다 — `black`이 콜론 간격과 압축 import를 전부 되돌린다)
- ORM, 커넥션 풀 (→ psycopg2 직접 + 호출당 커넥션)
- 상대 임포트, `__init__.py` 패키지화
- 영문 주석/독스트링
- 추상 베이스 클래스, DI 컨테이너 등 선제적 추상화

pandas 쪽에서 쓰지 않는 것: 여러 줄 메서드 체이닝, `inplace=True`, `.query()`, `df.col` 점 접근, `to_sql`/`execute_values`, 이름 없는 `df`. 자세한 대체 형태는 `references/data.md`에 있다.

## 새 파일을 만들 때

**서비스 코드** — `references/structure.md`의 계층을 따른다. 요약하면: 라우터는 `api/`, 외부 연동은 `service/`, 영속은 `db/`, pydantic 스키마와 응답 조립은 `model/`, 도메인 계산은 자기 이름의 패키지에. `main.py`는 앱 수명주기와 라우터 등록만 한다.

**노트북·실험 코드** — `references/research.md`를 따른다. 연구노트는 `YYMM_Title_Case_Purpose.ipynb`, 탐색용은 날짜 없이 주제 계열 접두사를 공유한다. 데이터 파일은 한글 이름에 `YYYYMMDD`와 추출 조건을 붙인다. 노트북이 굳으면 같은 basename의 `.py`로 옮기고 노트북은 남긴다.
