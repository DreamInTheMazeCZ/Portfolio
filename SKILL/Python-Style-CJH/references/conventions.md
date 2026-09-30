# 코딩 컨벤션 상세

`SKILL.md`의 핵심 규칙을 보강한다. 예시는 전부 실제 코드베이스에서 가져왔다.

## 목차

1. [명명 규칙](#1-명명-규칙)
2. [독스트링](#2-독스트링)
3. [주석](#3-주석)
4. [로깅](#4-로깅)
5. [타입힌트와 시그니처](#5-타입힌트와-시그니처)
6. [에러 처리](#6-에러-처리)
7. [문자열과 따옴표](#7-문자열과-따옴표)
8. [공백과 줄바꿈](#8-공백과-줄바꿈)

---

## 1. 명명 규칙

기본은 PEP 8이다: 함수·변수 `snake_case`, 클래스 `PascalCase`, 모듈 상수 `UPPER_SNAKE_CASE`.

그 위에 이 코드베이스만의 접두·접미 관행이 있다. 이름만 보고 어느 계층인지 알 수 있게 하려는 것이다.

### 함수 접두사

| 접두사 | 역할 | 예시 |
| --- | --- | --- |
| `calc_` | 값 산출·계산 | `calc_standard_price_fee`, `calc_ml_predict_fee` |
| `insert_` | DB 삽입 | `insert_ai_trade_price`, `insert_ml_trade_price` |
| `select_` | DB 조회 | `select_recent_view_count` |
| `make_` | 응답·구조체 조립 | `make_rent_response` |
| `pred_` | 예측 호출 | `pred_price` |

표에 없는 동작이면 **같은 문법으로 새로 만든다**: `<동사>_<대상>` (`record_trade_view`, `count_recent_trade_view`). 동사는 그 계층이 하는 일을 그대로 쓰고, 대상은 도메인 명사를 쓴다. 억지로 기존 접두사에 끼워 맞추지 않는다.

### 변수 접미사

딕셔너리 형태의 데이터 뭉치에는 `_data`를, 외부로 보낼 요청 본문에는 `_form`이나 `_input`을 붙인다.

```python
sub_data          # 수신 페이로드
insert_data       # DB에 넣을 딕셔너리
result_data       # 병합 완료된 결과
db_data           # DB에서 꺼낸 것
requests_data     # 라우터가 받은 pydantic 객체
pred_input_form   # 외부 API 요청 본문
```

### 클래스 내부 비공개

이름 맹글링을 쓰는 이중 밑줄 `__`를 쓴다 (`_` 한 개가 아니다).

```python
class PostgreSQL:
    def __init__(self):
        self.__conn_info = {...}

    def __connect_postgresql(self):
        ...

    def __close_db(self):
        ...
```

### 모듈 싱글턴

인스턴스를 만들어 쓰는 클래스는 **파일 맨 아래에서 한 번 생성**하고, 다른 모듈은 그 인스턴스를 임포트한다.

```python
# db/database.py 맨 아래
pg = PostgreSQL()
```

```python
# 사용하는 쪽
from db.database import pg
```

### 축약

`model_nm`처럼 축약을 쓰는 곳이 있으나 신규 코드에서는 **풀네임(`model_name`)을 기본**으로 한다. 다만 기존 파일을 고칠 때는 그 파일의 이름을 따라간다 — 한 파일 안에서 두 표기가 섞이는 것이 더 나쁘다.

---

## 2. 독스트링

`'''` 세 개의 작은따옴표. 열고 닫는 줄에는 내용을 쓰지 않는다.

```python
def insert_ai_trade_price(insert_data):
    '''
    직거래 수신 데이터
    ai_trade_price_analysis_dev 테이블 데이터 삽입
    '''
```

### 길이

한 줄이 기본, 맥락이 필요하면 두세 줄. `Args:` / `Returns:` / `Raises:` 섹션은 쓰지 않는다 — 시그니처와 타입힌트가 같은 말을 이미 하고 있어 중복될 뿐이고, 갱신되지 않으면 거짓말이 된다.

### 무엇을 적나

함수가 **무슨 일을 하는 물건인지** 명사형으로 적는 것이 지배적이다.

```python
'''
기준가액 기반 임대료 산출 함수
'''
```

```python
'''
파라미터 바인딩 INSERT, UPDATE 수행 메서드
'''
```

동작 설명이 필요하면 `~한다` 평서형으로 잇는다.

```python
'''
앱 시작 시 NATS 연결 및 구독을 자동 시작하고,
종료 시 정리한다. (단일 프로세스 상시 구동)
'''
```

### 놓치면 안 되는 전제

호출자가 모르면 사고나는 제약은 빈 줄 뒤 `*`로 단다.

```python
'''
직거래 수신 데이터 시세예측 후
ml_trade_price_analysis 테이블 데이터 삽입

* ml_trade_price_analysis 테이블은 형식명 + 제조연도 + 주행시간 기본키 설정으로 중복 인서트 방지
'''
```

### API 엔드포인트

라우터 함수의 독스트링은 FastAPI 자동 문서에 그대로 노출된다. 모드·분기가 있으면 표처럼 나열한다.

```python
'''
임대료 산출 API
mode 0 : 기준가액 기반 산출
mode 1 : ML 모델 예측가 기반 산출 (default)
mode 2 : 통합 반환 모드
'''
```

---

## 3. 주석

전부 한글. 코드가 *무엇인지*를 되풀이하지 않고 **무슨 단계인지, 왜 그런지**를 적는다.

### 블록 선행 주석

다음에 오는 몇 줄이 하나의 단계임을 표시한다. 가장 흔한 형태다.

```python
        # 값 스케일링
        std_price = std_price * 1000

        # 이진 탐색
        idx = bisect_right(RENT_THRESHOLDS, std_price) - 1
        fee = RENT_FEES[idx]
```

```python
        # 0년 중고가 가정
        inputs = {...}

        # 가산율 적용
        pred_price = pred_price * (1 + (additional_ratio / 100))
```

### 구분선

한 함수 안에서 처리 국면이 굵게 갈릴 때만 쓴다. 남발하면 의미가 죽는다.

```python
        # ===== ===== ===== 수신 데이터 DB 적재 ===== ===== =====
        ...
        # ===== ===== ===== 수신 데이터 시세예측 및 DB 적재 ===== ===== =====
```

### 후행 주석

필드의 의미, 값의 범위, 단위를 붙인다.

```python
    model_name:str   # 형식명
    allow_origins=["*"],           # 운영 가동 시 특정 도메인만 적용
    allow_methods=["POST", "GET"], # 해당 메서드만 처리
```

### 값이 왜 그 값인지

숫자가 비즈니스 규칙에서 나온 것이면 반드시 적는다. 나중에 바꿀 사람이 근거를 찾을 수 있어야 한다.

```python
        # 사용연수 변환 및 20년 초과 사용 처리
        used_year = datetime.now().year - manufacture_year if manufacture_year > 1900 else manufacture_year
        used_year = used_year if used_year < 20 else 20 # 데이터베이스에는 manufacture_year로 기록
```

### 미래 작업

지금 안 하는 것은 주석으로 남긴다.

```python
        # 추후에 추가
        # working_machine = sub_data.get('working_machine')
```

### 흐름 표시

`yield`처럼 제어가 넘어가는 지점은 눈에 띄게 표시하기도 한다.

```python
    yield  # ── 앱이 요청을 받는 동안 구독 유지 ──
```

---

## 4. 로깅

`print()`만 쓴다. 컨테이너가 `PYTHONUNBUFFERED=1`로 돌아 stdout이 그대로 로그 수집 대상이 되기 때문에, logging 설정을 얹어 얻을 것이 적다고 판단한 구조다.

### 형식

```
[레벨] 한글 설명 - 값
[레벨] 한글 설명 : 값
```

레벨 태그는 대괄호 대문자 영문, 설명은 한글. 값을 덧붙일 땐 ` - ` 또는 ` : `로 잇고, 값이 없으면 설명만 쓴다.

### 레벨 선택

| 레벨 | 쓰는 때 | 예시 |
| --- | --- | --- |
| `[DEBUG]` | 정상 흐름의 추적점. 메시지 수신, 인서트 완료 | `print(f"[DEBUG] 수신 데이터 {subject} : {data}")` |
| `[INFO]` | 프로세스 수명주기 사건. 시작, 구독 개시, 종료 | `print("[INFO] 구독 시작 — 상시 구동")` |
| `[WARN]` | 자동 복구되는 이상. 재접속 시도 중 | `print("[WARN] NATS 연결 끊김 — 재접속 시도 중")` |
| `[ERROR]` | 실패. 예외 포착 지점 | `print(f"[ERROR] ML 예측 실패 - {e}")` |

### 예외를 찍을 때

타입까지 필요하면 `type(e).__name__`을 함께 낸다.

```python
            print(f"[ERROR] {type(e).__name__}: {e}")
```

### 한글 문장부호

설명을 잇는 대시는 em dash(`—`)를 쓴다. 값 구분자 ` - `(hyphen)와 역할이 다르다.

```python
print("[INFO] 구독 시작 — 상시 구동")     # 설명 잇기
print(f"[ERROR] ML 예측 실패 - {e}")      # 값 붙이기
```

---

## 5. 타입힌트와 시그니처

### 콜론은 붙이고, 화살표는 띄운다

```python
def calc_standard_price_fee(model_nm:str) -> dict:
def calc_ml_predict_fee(model_nm:str, additional_ratio:int) -> dict:
def calc_rent_fee(requests_data:RequestCalculator) -> dict:
```

`model_nm: str`이 아니라 `model_nm:str`이다. 포매터(`black`, `ruff format`)를 돌리면 이게 전부 바뀌므로 **요청 없이 포매터를 도입하지 않는다.**

pydantic 모델 필드도 같다.

```python
class RequestCalculator(BaseModel):
    model_name:str
    additional_ratio:int = Field(default=0, ge=-100, le=100)
```

### 반환형

신규 함수에는 반드시 단다. 대부분 `dict`를 반환한다 — 이 코드베이스는 응답 객체 대신 평범한 딕셔너리를 돌려주는 쪽을 택했다.

### 인자가 많을 때

세로로 펼치고 닫는 괄호를 한 단 들여쓴 자리에 둔다.

```python
def make_rent_response(
        model_name:str,
        predict_price:int,
        rent_fee:int,
        source:str
    ) -> dict:
```

---

## 6. 에러 처리

### 항상 `Exception as e`

맨 `except:`도, `BaseException`도 쓰지 않는다. 잡은 예외는 반드시 로그에 남긴다.

### 계층별 종결 방식

**인프라 계층** — 실패를 위로 올린다. 롤백하고, 찍고, `raise`.

```python
    def query_execute_params(self, query, params):
        conn = self.__connect_postgresql()
        cur = conn.cursor()
        try:
            cur.execute(query, params)
            self.conn.commit()
            return True
        except Exception as e:
            self.conn.rollback()
            print(f"[ERROR] {type(e).__name__}: {e}")
            raise
        finally:
            cur.close()
            self.__close_db()
```

`finally`에서 커서와 커넥션을 반드시 정리한다.

**도메인·응답 계층** — 형태가 같은 안전 기본값을 돌려준다. 호출자(대개 API 라우터)가 응답 구조를 신뢰할 수 있어야 하므로, 실패했다고 `None`이나 다른 모양을 주지 않는다.

```python
    except Exception as e:
        print(e)
        return make_rent_response(model_nm, 0, 0, 'standard_price')
```

값이 0인 것으로 실패를 표현하고, 키 구성은 성공 응답과 동일하게 유지한다.

### 성공 여부 검사 후 예외 발생

DB 헬퍼가 `True`/`False`를 돌려주면 호출부에서 판단해 올린다.

```python
    if pg.query_execute_params(query, insert_data):
        print(f"[DEBUG] DB 인서트 성공 - {insert_data}")
    else:
        raise Exception(f"[ERROR] 수신 데이터 DB 인서트 실패 - {insert_data}")
```

### 하지 말 것

```python
        except Exception as e:
            pass          # 실패를 소리 없이 삼킨다
```

`subscribe.py`에 이 형태가 남아 있지만 **알려진 부채**이며 주석(`인서트 실패 시 작동 중단`)과도 어긋난다. 새 코드에 복제하지 않는다.

---

## 7. 문자열과 따옴표

작은따옴표 `'...'`가 기본이다. 딕셔너리 키, 짧은 리터럴, 경로 모두.

```python
    inputs = {
        'model_name':model_nm,
        'manufacture_year':0,
        'category':'AC',
    }
```

**딕셔너리 콜론은 띄운다** (`'model_name': model_name`). 타입힌트 콜론을 붙이는 것과 반대이므로 헷갈리기 쉽다 — 타입은 붙이고, 값은 띄운다.

```python
    result_data = {
        'trade_idx': sub_data.get('trade_idx'),
        'product_price': sub_data.get('product_price'),
    }
```

붙여 쓴 리터럴이 일부 남아 있으나(`calculation.py`의 `inputs`) 소수다. 기존 파일을 고칠 때는 그 리터럴의 기존 간격을 따라가고, 새로 쓰는 딕셔너리는 띄운다.

### f-string

값 삽입은 전부 f-string. `%` 포매팅이나 `.format()`은 쓰지 않는다.

### SQL

여러 줄 `f'''...'''`로 쓰고 들여쓴다. 키워드는 대문자.

```python
    query = f'''
    SELECT model_name, machine_price
    FROM trained_result
    WHERE model_name = %s
    '''
```

**값은 절대 f-string으로 끼워 넣지 않는다.** 위치 바인딩은 `%s`, 이름 바인딩은 `%(col)s`를 쓰고 실제 값은 파라미터로 넘긴다. 컬럼명을 동적으로 조립할 때도 값은 분리한다.

```python
    columns = insert_data.keys()
    query = f"""
    INSERT INTO ai_trade_price_analysis_dev ({', '.join(columns)})
    VALUES ({', '.join([f'%({col})s' for col in columns])})
    """
    pg.query_execute_params(query, insert_data)
```

이 방식은 페이로드 키가 곧 컬럼명이 된다는 뜻이므로, **키 출처가 신뢰할 수 있는 내부 생산자일 때만** 쓴다. 외부 입력에는 컬럼 화이트리스트를 둔다.

### 조건부 치환

짧은 매핑은 삼항 연쇄로 한 줄에 쓴다.

```python
        category_name = 'AC' if category_name == '트랙터' else 'AD' if category_name == '이앙기' else 'AE'
```

---

## 8. 공백과 줄바꿈

- 최상위 함수 사이는 **2줄**, 클래스 메서드 사이는 1~2줄.
- 함수 본문 안에서 논리 단계마다 빈 줄로 끊고, 그 앞에 선행 주석을 단다.
- 딕셔너리 리터럴은 항목당 한 줄, 마지막 항목에도 쉼표를 남긴다.
- 줄 길이에 엄격한 상한을 두지 않는다. 삼항 연쇄나 긴 계산식이 한 줄에 그대로 있는 편이 읽기 낫다고 보면 그대로 둔다.
