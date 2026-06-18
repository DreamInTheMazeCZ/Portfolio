# NCAI OCR Automation — Airflow

기존 FastAPI + APScheduler 기반 OCR 파이프라인을 **Docker + Airflow**로 재구축한 프로젝트입니다.
검증된 기존 배치 로직(`config`/`batchs`/`database`/`embeddings`/`gpt_ocr`/`utils`)을 그대로 재사용하고,
4단계 배치를 **단일 DAG의 의존성 체인**으로 실행합니다.

```
pdf_checker  →  pdf_extract  →  image_ocr  →  data_insert
```

## 아키텍처

- **DAG**: `dags/ocr_pipeline_dag.py` — `ncai_ocr_pipeline`. 매일 15:00 KST 실행(`catchup=False`, `max_active_runs=1`).
  4개 `PythonOperator`가 의존성으로 연결되어 "이전 단계 성공 시 다음 실행"을 보장합니다.
- **재사용 로직**: `include/ncai_ocr/` 에 위치하며 `PYTHONPATH=/opt/airflow/include/ncai_ocr` 로 import됩니다.
  무거운 import(SentenceTransformer 로드 등)가 DAG 파싱 시 실행되지 않도록, DAG의 각 task는
  콜러블 **내부에서** 런타임 import합니다.
- **상태 머신**: 실제 처리 대상 선별은 여전히 외부 DB의 `pdf_extraction_status` 플래그
  (`is_extract → is_ocr → is_insert`)로 이루어져 멱등성이 유지됩니다. Airflow 의존성은 그 위에
  실행 순서를 보장하는 계층입니다.
- **DB**: 데이터 저장용 PostgreSQL은 **컨테이너화하지 않고** `.env`의 `DB_*`로 외부 접속합니다.
  Airflow 메타데이터 DB(`postgres` 서비스)는 이와 완전히 별개입니다.

## 빠른 시작

```bash
cd Airflow
cp .env.example .env          # 값 입력: GPT 키, 외부 DB 접속정보 등
# Linux/Mac: .env의 AIRFLOW_UID 를 `id -u` 값으로 변경
# 호스트에서 도는 DB면 DB_HOST=host.docker.internal 유지

docker compose build          # sentence-transformers/torch 포함 → 수 분 소요
docker compose up airflow-init
docker compose up -d
docker compose ps             # scheduler/webserver healthy 확인
```

웹 UI: http://localhost:8080 (기본 계정 `airflow` / `airflow`, `.env`에서 변경 가능)

## 실행

1. 입력 PDF를 호스트의 `data/pdf_folder/<제조사>/<file_id>.pdf` 에 배치 (컨테이너 `/opt/airflow/data/pdf_folder`).
2. UI에서 `ncai_ocr_pipeline` DAG를 unpause 후 수동 트리거(또는 스케줄 대기).
3. 산출물:
   - `data/extraction/<제조사>/<category>/<file_id>/images/*.png`
   - `.../ocr_data/ocr_result.json`
   - 외부 DB `pdf_extraction_data` 테이블 적재

## 단일 task 디버깅

```bash
docker compose run --rm airflow-scheduler airflow tasks test ncai_ocr_pipeline pdf_extract 2026-06-18
```

## 디렉토리

```
Airflow/
├── docker-compose.yaml   # postgres(메타) + init + scheduler + webserver (LocalExecutor)
├── Dockerfile            # apache/airflow:2.10.4-python3.10 + requirements.txt
├── requirements.txt      # PyMuPDF, openai, sentence-transformers, pandas, psycopg2-binary ...
├── .env.example
├── dags/ocr_pipeline_dag.py
├── include/ncai_ocr/     # 재사용 비즈니스 로직 (PYTHONPATH 등록)
├── data/{pdf_folder,extraction}/   # 입출력 볼륨
├── hf_cache/             # HuggingFace 모델 캐시 볼륨
├── gpt_error_txt/        # OCR JSON 파싱 실패 덤프
└── logs/
```

## 컨테이너화를 위해 기존 코드에 가한 수정

원본 루트 프로젝트는 보존되며, `include/ncai_ocr/` 복사본에만 최소 수정을 적용했습니다.

- `config/config.py`: `PDF_DIR`/`BASE_DIR`를 환경변수로 주입(절대경로). `MAKER_LIST` 상수를
  `get_maker_list()` 함수로 변경하여 import 시점 디렉토리 스캔을 제거.
- `batchs/pdf_checker.py`: `get_maker_list()`를 런타임 호출.
- `batchs/pdf_data_insert.py`: `BASE_DIR[2:]` 슬라이싱(`./` 가정)을
  `os.path.basename(os.path.normpath(BASE_DIR))`로 교체하여 절대경로에서도 동일한 URL 경로 유지.
