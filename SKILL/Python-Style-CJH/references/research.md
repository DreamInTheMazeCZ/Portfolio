# 연구·실험 코드와 데이터 산출물

노트북, 파일 이름, 데이터 산출물을 어떻게 이름 짓고 어디에 두는지. **추적 가능성이 목적**이다 — 몇 달 뒤 "그 실험 언제 뭘로 했더라"에 답할 수 있어야 한다.

## 목차

1. [디렉터리 taxonomy](#1-디렉터리-taxonomy)
2. [연구노트 파일명 — YYMM 회차](#2-연구노트-파일명--yymm-회차)
3. [탐색용 노트북 이름](#3-탐색용-노트북-이름)
4. [노트북 내부 구조](#4-노트북-내부-구조)
5. [데이터 파일 이름](#5-데이터-파일-이름)
6. [노트북에서 운영 코드로](#6-노트북에서-운영-코드로)
7. [git 관리](#7-git-관리)

---

## 1. 디렉터리 taxonomy

용도가 다르면 디렉터리가 다르다. 섞지 않는 것이 추적의 출발점이다.

| 위치 | 성격 | 날짜 | 예시 |
| --- | --- | --- | --- |
| `Research_Note_Code/` | 연구노트 제출물. 주제 하나당 파일 하나 | 파일명에 `YYMM` | `2609_Model_Name_Fixer_Validate.ipynb` |
| `Research_Note_Code/HTML/` | 위 노트북의 `.html` 내보내기 | — | `Data_Augmentation_Code.html` |
| `Jupyter_Code/` | 탐색·EDA. 주제 계열별로 묶임 | 없음 (데이터 연식은 붙음) | `Loan_Data_EDA.ipynb` |
| 프로젝트 루트 | 작업 중 스크래치 | 없음 | `test.ipynb`, `price_calc.ipynb` |
| `Data/` | 입력 데이터. 도메인 하위 폴더 | 파일명에 | `Data/기준가액/…` |
| `src/` | 운영 코드 | 없음 | `agris_crawler.py` |

루트 스크래치는 **지우지 않고 남긴다.** 나중에 근거를 되짚을 때 쓰인다.

---

## 2. 연구노트 파일명 — YYMM 회차

```
YYMM_Title_Case_Purpose.ipynb
```

앞 4자리는 **연월**이다. 월 1회 정도 쌓이며 건너뛴 달이 있어도 된다.

```
2508_Oversampling_Test_Code.ipynb
2512_Data_Augmentation_Code.ipynb
2601_PDF_Extract_Code.ipynb
2603_Get_Average_Price.ipynb
2604_Generate_Train_Data_Code.ipynb
2606_Add_Option_Test_Code.ipynb
2609_Model_Name_Fixer_Validate.ipynb
```

제목은 **영문 TitleCase를 언더스코어로 이어** 쓴다 (한글 아님). 끝에는 무슨 활동인지를 붙인다: `_Code`, `_Test_Code`, `_Validate`.

이 파일들은 국가 R&D 과제 제출물이므로 `.html`로 내보내 `HTML/`에 함께 보관한다. 노트북을 고쳤으면 HTML도 다시 내보낸다.

---

## 3. 탐색용 노트북 이름

날짜를 붙이지 않는다. 대신 **주제 계열로 묶어** 접두사를 공유한다.

```
Loan_Data_Extract.ipynb
Loan_Data_Concat.ipynb
Loan_Data_EDA.ipynb
Loan_Data_Groupby_EDA.ipynb
Loan_Data_Agriis_Valid.ipynb
```

같은 데이터를 다루는 파일이 늘어나면 접두사를 맞춰 붙여 나간다. 파일 목록만 봐도 작업 흐름(추출 → 병합 → 탐색 → 검증)이 읽힌다.

끝의 연도는 만든 날짜가 아니라 **데이터 연식**이다.

```
Standard_Price_Table_EDA_2023.ipynb   # 2023년 기준가액표 분석
Standard_Price_Table_EDA_2026.ipynb   # 2026년 기준가액표 분석
```

---

## 4. 노트북 내부 구조

### 첫 셀은 한글 제목

마크다운 `##`로 목적을 적는다.

```markdown
## 형식명 보정 결과 검증
```

테스트 시나리오가 갈리면 `###`로 나눈다.

```markdown
### Case 1. 대소문자만 다른 경우
### Case 2. 하이픈 유무 차이
```

### import는 한 셀에

`.py`와 같은 규칙이다 — `from` 블록 먼저, 압축 `import` 마지막.

### 출력은 지우지 않고 커밋한다

연구노트는 **결과 자체가 근거**다. 실행 출력을 남긴 채 저장한다. 운영 코드 저장소의 노트북도 마찬가지로 남긴다.

### 죽은 코드는 주석으로 남긴다

지우지 않는다. 그때 무엇을 시도했는지가 기록이다.

```python
# tractor_df.to_excel('../보정_모델명_결과.xlsx', index=False)
```

### 데이터는 상대경로로 읽는다

```python
tractor_df = pd.read_excel('../Data/기준가액/2026년_기준가액_트랙터.xlsx')
```

### 독스트링

연구·분석 코드에서는 **Google 스타일 `Args:` / `Returns:`**를 쓰고 괄호에 타입을, 설명은 한글로 단다. 운영 서비스 코드(한 줄 설명)나 ML 파이프라인 코드(`Parameter` / `Return` 평문 레이블)와 규칙이 다르다.

```python
def get_mean_price(model_nm, page_cnt):
    '''
    아그리즈 평균판매가 조회

    Args:
        model_nm (str): 형식명
        page_cnt (int): 조회할 페이지 수

    Returns:
        dict: 형식명별 평균판매가
    '''
```

---

## 5. 데이터 파일 이름

한글 단어를 언더스코어로 잇는다. 코드 파일과 반대로 **한글이 기본**이다 — 사람이 탐색기에서 찾는 파일이기 때문이다.

### 날짜는 `YYYYMMDD`

앞이나 뒤 어디든 붙지만 형식은 고정이다.

```
20250101_정부지원_농업기계_융자가액표.xlsx     # 앞 — 자료 기준일
아그리즈_옵션포함_20260305.xlsx                # 뒤 — 추출일
```

연식만 필요하면 연도만 앞에 붙인다.

```
2026년_기준가액_트랙터.xlsx
```

### 조건을 이름에 적는다

어떤 조건으로 뽑았는지가 이름에 들어간다. 나중에 재현할 때의 단서다.

```
아그리즈_평균판매가_20페이지.xlsx
아그리즈_콤바인_평균판매가_20페이지.xlsx
추가_학습_데이터_트랙터_테스트.xlsx
```

### 정식 산출물은 순번 + 건수 + 날짜

제출·공유용 데이터셋은 앞에 순번을, 뒤에 레코드 수와 날짜를 단다.

```
01-2. 대소문자_처리_후_시세예측_가능_형식명_Rawdata_78건_20260407.xlsx
```

담는 폴더는 `YYMMDD`를 쓴다 (파일과 자릿수가 다름에 주의).

```
형식명_보정추천_데이터_분류_260407/
```

---

## 6. 노트북에서 운영 코드로

노트북으로 먼저 만들고, 굳으면 `.py`로 옮긴다. **노트북은 지우지 않고 나란히 둔다.**

```
src/agris_crawler/
├── agris_crawler.py
└── jupyter_notebook/
    └── agris_crawler.ipynb
```

규칙:

- `.py`와 `.ipynb`의 **basename을 같게** 한다.
- 노트북은 `jupyter_notebook/` 하위에 둔다.
- `.py`는 셀을 이어붙인 것에 가깝다 — 마크다운 제목과 맨 끝 `# 스크립트 사용 예제` 셀만 뺀다.
- 연구노트(`2603_Get_Average_Price.ipynb`)가 조상인 경우가 많다. 옮길 때 그 계보를 주석이나 커밋 메시지에 남기면 추적이 쉬워진다.

---

## 7. git 관리

`.gitignore`의 섹션 주석도 한글로 단다.

```gitignore
.env

# 데이터
*.xlsx
*.csv

# 노트북
.ipynb_checkpoints

__pycache__/
```

데이터 파일은 저장소에 넣지 않는다 — 용량이 크고 자주 바뀐다. 대신 `Data/` 경로와 파일명 규칙을 README에 적어 어디서 오는지 밝힌다.

`.ipynb_checkpoints`는 항상 제외한다.

개인 작업 공간(`01_Price_Prediction` 등)은 git 저장소가 아니며 체크포인트가 쌓여도 정리하지 않는다. **저장소로 만들 때 `.gitignore`부터 넣는다.**
