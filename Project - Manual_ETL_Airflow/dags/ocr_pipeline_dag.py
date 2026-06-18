"""
NCAI OCR 파이프라인 DAG

농기계 매뉴얼 PDF를 처리하는 4단계 배치를 단일 DAG의 의존성 체인으로 실행한다.

    pdf_checker  →  pdf_extract  →  image_ocr  →  data_insert

기존 APScheduler의 시각 기반(15:00/15:30/17:00/18:00) 실행을 대체하여,
"이전 단계가 성공해야 다음 단계가 실행"되도록 보장한다. 각 단계의 실제 대상 선별은
여전히 DB 상태 플래그(is_extract → is_ocr → is_insert)로 이루어지므로 멱등성이 유지된다.

주의: 무거운 import(SentenceTransformer 로드, PDF_DIR 스캔 등)는 스케줄러의 DAG 파싱
시점에 실행되면 안 되므로, 모든 비즈니스 로직 import는 각 task 콜러블 *내부*에서 수행한다.
"""

from datetime import timedelta

import pendulum
from airflow import DAG
from airflow.operators.python import PythonOperator

KST = pendulum.timezone("Asia/Seoul")


# ----- task 콜러블 (런타임 import) -----
def run_pdf_checker():
    from batchs.pdf_checker import pdf_file_checker
    pdf_file_checker()


def run_pdf_extract():
    from batchs.pdf_extract import pdf_extract
    pdf_extract()


def run_image_ocr():
    from batchs.image_ocr import image_ocr
    image_ocr()


def run_data_insert():
    from batchs.pdf_data_insert import data_insert
    data_insert()


default_args = {
    "owner": "ncai",
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
    "email_on_failure": False,
    "email_on_retry": False,
}

with DAG(
    dag_id="ncai_ocr_pipeline",
    description="농기계 매뉴얼 PDF → 이미지 추출 → GPT OCR → 임베딩 적재 파이프라인",
    default_args=default_args,
    schedule="0 15 * * *",  # 매일 15:00 KST (기존 첫 배치 시각)
    start_date=pendulum.datetime(2026, 1, 1, tz=KST),
    catchup=False,
    max_active_runs=1,
    tags=["ncai", "ocr", "pdf"],
) as dag:

    t_checker = PythonOperator(
        task_id="pdf_checker",
        python_callable=run_pdf_checker,
    )

    t_extract = PythonOperator(
        task_id="pdf_extract",
        python_callable=run_pdf_extract,
    )

    t_ocr = PythonOperator(
        task_id="image_ocr",
        python_callable=run_image_ocr,
    )

    t_insert = PythonOperator(
        task_id="data_insert",
        python_callable=run_data_insert,
    )

    t_checker >> t_extract >> t_ocr >> t_insert
