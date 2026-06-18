# 베이스: 공식 Airflow 이미지 (Python 3.10 — 기존 프로젝트 권장 버전과 일치)
FROM apache/airflow:2.10.4-python3.10

# 프로젝트 의존성 설치
# 주의: sentence-transformers는 torch/transformers를 끌어오므로 이미지가 크고
#       빌드 시간이 오래 걸린다(수 GB / 수 분).
COPY requirements.txt /requirements.txt
RUN pip install --no-cache-dir -r /requirements.txt
