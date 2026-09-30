# DB 접근과 데이터 처리

DB에서 데이터를 꺼내 pandas로 가공하고 다시 적재하는 작업의 컨벤션. 여러 프로젝트(`NCAI-price-prediction-api`, `NCAI-ocr-automation`, `NCAI-manual-chatbot`, `NCAI-price-predictor-feature`)에서 공통으로 관찰된 형태다.

## 목차

1. [DB 계층 구조](#1-db-계층-구조)
2. [파라미터 바인딩 — 반드시 지킬 것](#2-파라미터-바인딩--반드시-지킬-것)
3. [조회 결과를 DataFrame으로](#3-조회-결과를-dataframe으로)
4. [대량 삽입](#4-대량-삽입)
5. [pandas 컨벤션](#5-pandas-컨벤션)
6. [데이터 처리 함수의 독스트링](#6-데이터-처리-함수의-독스트링)
7. [로깅 — print와 logging의 경계](#7-로깅--print와-logging의-경계)
8. [파일 입출력](#8-파일-입출력)

---

## 1. DB 계층 구조

**커넥션 담당 베이스 클래스 + 쿼리 담당 서브클래스** 2층 구조가 현재 선호 형태다. 호출자는 서브클래스만 만진다.

### 베이스 — 커넥션과 실행만

```python
class PostgreSQL:
    def __init__(self):
        self.__conn_info = {
            'dbname': DB_NAME,
            'user': DB_USER,
            'password': DB_PW,
            'host': DB_HOST,
            'port': DB_PORT,
        }

    def __connect_postgresql(self):
        '''
        DB Connection
        데이터베이스 연결
        '''
        self.conn = psycopg2.connect(**self.__conn_info)
        return self.conn

    def __close_db(self):
        self.conn.close()
        return True
```

커넥션 정보와 연결/해제는 이중 밑줄로 감춘다. 실행 메서드는 용도별로 나눈다.

| 메서드 | 용도 | 반환 |
| --- | --- | --- |
| `select_execute_params(query, params)` | 조회 | `fetchall()` 결과 |
| `query_execute_params(query, params)` | INSERT/UPDATE | `True` |
| `executemany_query(query, data)` | 대량 삽입 | `True` |

커넥션은 **호출당 열고 닫는다.** 풀링을 두지 않는다. `finally`에서 커서와 커넥션을 반드시 정리한다.

### 서브클래스 — 쿼리 하나에 메서드 하나

```python
class QueryMethod(PostgreSQL):

    def __init__(self):
        super().__init__() # PostgreSQL 연결 정보 상속

    def select_exists_status(self):
        '''
        pdf_extraction_status 테이블 내 처리된 File ID 조회
        '''
        query = '''
        SELECT file_id FROM pdf_extraction_status
        WHERE is_extract
        '''
        return list(map(lambda ele: ele[0], self.select_execute_params(query, None)))
```

SQL 문자열이 호출자 코드에 새지 않게 막는 것이 핵심이다. 메서드 이름이 곧 쿼리의 목적이고, 독스트링에 **테이블명과 무엇을 꺼내는지**를 한글로 적는다.

단일 컬럼 조회는 튜플을 벗겨서 평평한 리스트로 돌려준다.

```python
        return list(map(lambda ele: ele[0], self.select_execute_params(query, params)))
```

쓰기 메서드는 성공 여부를 불리언으로 정리해서 돌려준다.

```python
    def insert_data_table(self, insert_value):
        '''
        pdf_contents 테이블 데이터 대량 삽입
        '''
        query = '''
        INSERT INTO pdf_contents (file_id, page_num, contents)
        VALUES (%s, %s, %s)
        '''
        if self.executemany_query(query, insert_value):
            return True
        else:
            return False
```

### 인스턴스 생성 위치

호출하는 모듈 상단에서 만든다. 주석을 단다.

```python
# DB 처리 인스턴스
qm = QueryMethod()
```

단일 모듈짜리 작은 프로젝트라면 `db/database.py` 맨 아래의 `pg = PostgreSQL()`처럼 DB 모듈 쪽에 둬도 된다.

---

## 2. 파라미터 바인딩 — 반드시 지킬 것

**값을 f-string으로 SQL에 끼워 넣지 않는다.** 위치 바인딩은 `%s`, 이름 바인딩은 `%(col)s`를 쓰고 값은 파라미터로 넘긴다.

```python
    query = '''
    SELECT file_id, page_num
    FROM pdf_contents
    WHERE file_id = %s
      AND maker_company_name = %s
    '''
    return self.select_execute_params(query, (file_id, cmpn_nm))
```

기존 프로젝트 일부(`NCAI-ocr-automation`, `NCAI-manual-chatbot`)에 아래 같은 코드가 남아 있다. **SQL 인젝션이며 복제 대상이 아니다.**

```python
# 이렇게 쓰지 않는다
query = f'''SELECT * FROM t WHERE file_id = {file_id}'''
query = f'''... WHERE maker_company_name = '{cmpn_nm}' '''
query = "... emb <=> '%s' LIMIT 10" % embedding
```

값이 내부에서 생성된 것이라 지금 당장 문제가 없어 보여도, 입력 경로는 나중에 바뀐다. 새 쿼리는 예외 없이 바인딩한다.

**구조는 f-string으로 조립해도 된다.** 값이 아니라 컬럼명·테이블명·조건절 유무처럼 코드가 결정하는 부분만 해당한다.

```python
    query = f'''
    UPDATE pdf_extraction_status
    SET {'' if is_start else 'is_extract = true,'}
        updated_at = NOW()
    WHERE file_id = %s
    '''
```

---

## 3. 조회 결과를 DataFrame으로

psycopg2 경로에서는 `fetchall()` 결과에 **컬럼명 리스트를 직접 붙인다.** 컬럼 리스트는 쿼리 바로 위에 주석과 함께 선언한다.

```python
    # DB 컬럼명
    col_nm = ['file_id', 'page_num', 'contents', 'created_at']

    query_result = qm.select_pdf_contents()
    contents_df = pd.DataFrame(query_result, columns=col_nm)
```

컬럼 리스트와 SELECT 절의 순서가 어긋나면 조용히 잘못된 데이터가 만들어진다. **둘을 항상 붙여 두고 같이 고친다.**

`pd.read_sql`은 pymysql `DBConnector`를 쓰는 곳에서만 등장한다. PostgreSQL 작업에서는 위의 수동 조립이 지배적이다.

```python
    def select_data(self, query) -> pd.DataFrame:
        '''
        조회 결과 DataFrame 반환
        '''
        return pd.read_sql(query, self.__connect_db())
```

---

## 4. 대량 삽입

`executemany`를 쓴다. `to_sql`이나 `execute_values`는 쓰지 않는다.

DataFrame을 튜플 리스트로 바꾸고, 100건 단위로 잘라서 넣는다.

```python
    # 인서트 데이터 가공
    insert_value = [
        (data['file_id'], data['page_num'], data['contents'])
        for _, data in df.iterrows()
    ]

    # 100건 단위 분할 삽입
    batch_size = 100
    for i in range(0, len(insert_value), batch_size):
        chunk = insert_value[i:i + batch_size]
        qm.insert_data_table(chunk)
```

컬럼 순서가 이미 맞으면 짧게 쓴다.

```python
    insert_value = [tuple(data.values) for _, data in df.iterrows()]
```

---

## 5. pandas 컨벤션

### import 위치

`from` 블록 다음, 압축 `import` 줄에 놓는다. 별칭은 `pd`, `np`.

```python
from sklearn.preprocessing import StandardScaler
from config import ML_PARAMS_FILE

import pandas as pd
import numpy as np
import warnings, json
warnings.filterwarnings("ignore")
```

### DataFrame 이름

**`df` 단독을 쓰지 않는다.** 무엇이 담겼는지 드러나는 이름에 `_df` 또는 `_data`를 붙인다.

```python
calc_df, aug_df_65, pred_used_df_70, result_aug_data, train_data, std_data
```

짧은 루프 변수로 `df`를 쓰는 것은 예외다. `df_a`, `df_b`처럼 단계 번호를 붙이는 방식은 레거시 EDA 스크립트에만 남아 있으니 따라 하지 않는다.

### 연산 방식

**한 줄에 한 연산, 위에 한글 주석.** 여러 줄에 걸친 메서드 체이닝을 쓰지 않는다. `inplace=True` 대신 재할당한다.

```python
    # 연식당 사용시간 산출
    calc_df['used_time_per_year'] = round((df['driving_time'] / df['manufacture_year']).fillna(0), 1)

    # 증강 데이터 병합
    result_aug_data = result_aug_data.merge(option_df, on='manufacture_year')
```

### 컬럼 접근

대괄호만 쓴다 (`df['col']`). 점 접근(`df.col`)은 쓰지 않는다. 컬럼명은 영문 snake_case, 의미는 후행 한글 주석으로 단다.

```python
    features = [self.model_nm, 'driving_time'] # 중고가, 사용시간
```

컬럼 리스트는 모듈 상수로 빼지 않고 쓰는 자리에 리터럴로 둔다. 다만 여러 함수가 공유하면 `config.py`로 올린다.

### 변환

| 목적 | 쓰는 것 |
| --- | --- |
| 스칼라 파생 | `.map(함수)` |
| 여러 컬럼 동시 반환 | `.apply(함수, axis=1, result_type='expand')` |
| 행 필터 | 불리언 마스크, `.isin()` |
| 학습/정답 분리 | `.iloc[:, 1:]`, `.iloc[:, 0]` 위치 슬라이싱 |

`.query()`는 쓰지 않는다.

```python
    # 제조연도 기준 사용시간 환산
    prediction_df['driving_time'] = prediction_df['manufacture_year'].map(calc_used_time)

    # 부착기 옵션 판별 (2개 컬럼 동시 생성)
    result_aug_data[['is_loader', 'is_rotary']] = result_aug_data.apply(
        self._check_tracktor_option,
        axis=1,
        result_type='expand'
    )
```

### 결측·형변환

`.fillna(0)`은 `round(...)`로 감싸 소수 자리를 정리하고, 읽기 직후 `.dropna(axis=0)`, 학습 분리 시점에 `.astype(float)`를 건다.

### 결합

```python
    merged_data = pd.concat([aug_df_65, aug_df_70], axis=0, ignore_index=True)
    result_data = base_df.merge(option_df, on='manufacture_year', how='outer')
```

`groupby`는 집계보다 순회에 쓴다.

```python
    for model_nm, group in grouped:
        ...
```

---

## 6. 데이터 처리 함수의 독스트링

서비스 코드와 규칙이 다르다. 서비스 함수는 한 줄 설명만 쓰지만, **데이터·ML 함수는 입출력을 레이블로 명시한다.** 인자가 DataFrame이면 시그니처만 봐서는 어떤 컬럼이 필요한지 알 수 없기 때문이다.

Google/NumPy 형식이 아니라 평문 레이블이다.

```python
    def make_augmentation_data(self, base_df, ratio):
        '''
        중고가 증강 데이터 생성

        Parameter
        base_df : 원본 학습 데이터 (manufacture_year, driving_time, 중고가 컬럼 필요)
        ratio : 증강 비율 (0.65, 0.70)

        Return
        증강 데이터가 병합된 DataFrame
        '''
```

레이블은 `Parameter` / `Output` / `Return`을 쓴다. 파일이나 모델을 떨구는 함수는 `Output`에 산출물 경로를 적는다.

처리 국면이 갈리는 곳은 배너 주석으로 나눈다.

```python
    # ===== ===== 트랙터 부착기 여부 학습 데이터 ===== =====
```

---

## 7. 로깅 — print와 logging의 경계

`print`만 쓰는 것이 아니다. **실행 수명에 따라 갈린다.**

| 상황 | 방식 |
| --- | --- |
| 상시 구동 서비스, 짧은 배치, 노트북 | `print(f"[DEBUG] ...")` — stdout이 곧 로그 |
| 장시간 학습, 스케줄 배치(Airflow 등) | `logging` + `TimedRotatingFileHandler` |

파일 로깅을 쓸 때는 `utils/logger.py`에 `setup_logger`를 두고 공유한다. **`encoding='utf-8'`을 반드시 준다** — 한글 메시지가 깨진다.

```python
    handler = TimedRotatingFileHandler(
        log_path,
        when='midnight',
        encoding='utf-8'
    )
```

예외는 `logger.exception(...)`으로 남겨 트레이스백을 보존한다.

두 방식이 섞여도 **메시지 형식은 같다**: `[레벨] 한글 설명 - 값`.

### 진행 상황

루프 경계에서 찍는다. `df.shape`이나 `len(df)`를 로그로 내지 않고, 확인된 행 수는 후행 주석으로 코드에 남긴다.

```python
    train_data = pd.read_excel(TRAIN_DATA_FILE) # 10635
```

---

## 8. 파일 입출력

### 저장

디렉터리 존재를 먼저 확인하고 만든다. `index=False`는 항상 준다.

```python
    if not os.path.isdir(OUTPUT_DATA_DIR):
        os.mkdir(OUTPUT_DATA_DIR)

    result_aug_data.sort_values(by=['manufacture_year', self.model_nm]).to_excel(
        f'{OUTPUT_DATA_DIR}/{self.model_nm}_aug_data.xlsx', index=False
    )
```

파일명은 f-string으로 조립하고, 구분자는 언더스코어다. 경로 상수(`OUTPUT_DATA_DIR`, `TRAIN_DATA_FILE`)는 `config.py`에 둔다.

### 인코딩

- Excel: `encoding` 인자 없음 (openpyxl이 처리)
- CSV: 한글이 있으면 `encoding='utf-8-sig'` — Excel에서 열었을 때 깨지지 않게
- JSON·로그: `encoding='utf-8'`

### 형식 선택

중간 산출물과 사람이 열어볼 데이터는 `.xlsx`, 설정·파라미터는 `.json`을 쓴다.
