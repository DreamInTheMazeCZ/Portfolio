from dotenv import load_dotenv
import os

load_dotenv()

# 공통 변수 (컨테이너 환경에서는 환경변수로 절대경로 주입)
PDF_DIR = os.getenv('PDF_DIR', '/opt/airflow/data/pdf_folder')   # PDF 파일 저장소
BASE_DIR = os.getenv('BASE_DIR', '/opt/airflow/data/extraction') # 작업 산출물 저장소

# 비동기 최대요청 수
MAX_CONCURRENT_REQUESTS = int(os.getenv('MAX_CONCURRENT_REQUESTS'))

# GPT 관련 설정
os.environ['OPENAI_API_KEY'] = os.getenv('GPT_API_KEY')
GPT_MODEL_NAME = os.getenv('GPT_MODEL_NAME')

# 이미지 URL
IMG_URL = os.getenv('IMG_URL')


def get_maker_list():
    '''
    pdf_folder 내 제조사별 폴더명 리스트 (런타임 평가).
    import 시점이 아닌 호출 시점에 디렉토리를 스캔하여,
    DAG 파싱/스케줄러 기동 시 PDF_DIR이 없어도 ImportError가 발생하지 않도록 한다.
    '''
    if not os.path.isdir(PDF_DIR):
        return []
    return [file for file in os.listdir(PDF_DIR)]
