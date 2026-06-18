from config.config import *
from database.query import QueryMethod
from utils.logger import setup_logger, apply_logger

from concurrent.futures import ThreadPoolExecutor
import concurrent.futures

from tqdm import tqdm

import fitz, os

# DB 처리 인스턴스
qm = QueryMethod()

app_logger = setup_logger('PDF_EXTRACT', 'pdf_extract_log')

def image_file_save_func(image_dir:str, page_num:int, page):
    # 이미지 파일명 및 저장 경로
    image_file_nm = f"page_{str(page_num + 1).zfill(3)}_image.png"
    image_file_save = f"{image_dir}/{image_file_nm}"
    
    # 페이지 이미지 추출
    pix = page.get_pixmap(matrix=fitz.Matrix(2.5, 2.5))
    pix.save(image_file_save)
    return True


@apply_logger(logger_name='PDF_EXTRACT', log_file_suffix='pdf_extract_log')
def pdf_extract():
    '''
    PDF → 이미지 추출 및 DB 상태 관련 처리 작업
    '''
    app_logger.debug(f'========== PDF EXTRACT 처리 시작 ==========')
    
    app_logger.debug(f'미처리 PDF 파일 확인 중 ...')
    print(f'[DEBUG] 미처리 PDF 파일 확인 중 ...')
    
    # 메타데이터 추출
    select_result = qm.select_metadata()

    app_logger.debug(f'미처리 PDF 파일 : {len(select_result)}개')
    print(f'[DEBUG] 미처리 PDF 파일 : {len(select_result)}개')
    
    if not select_result:
        app_logger.debug(f'처리 필요한 데이터 없음.')
        app_logger.debug(f'========== PDF EXTRACT 처리 종료 ==========\n')
        return 
    
    # 추출 파일 디렉토리 설정
    for pdf_data in select_result:
        # 언패킹
        file_id, category, pdf_file, cmpn_nm = pdf_data
        
        app_logger.info(f'{pdf_file} PDF 파일 처리 시작.')
        print(f'[INFO] {pdf_file} PDF 파일 처리 시작.')
        
        # 작업 시작 일시 업데이트
        qm.update_pdf_extract(file_id)

        # ===== ===== PDF 파일 처리부 ===== ===== 
        # PDF 파일 경로
        pdf_file_dir = f'{PDF_DIR}/{cmpn_nm}/{pdf_file}'

        doc = fitz.open(pdf_file_dir)

        # 이미지 저장 경로 설정    
        image_dir = f"{BASE_DIR}/{cmpn_nm}/{category}/{file_id}/images/"
    
        # 폴더 생성
        if not os.path.exists(image_dir):
            os.makedirs(image_dir)
    
        app_logger.info(f"{image_dir} 디렉토리 신규 생성.")
        
        # 병렬처리
        with ThreadPoolExecutor(max_workers=4) as executor:
            jobs = []
            # 페이지별 처리
            for page_num, page in tqdm(enumerate(doc), total=len(doc)):
                try:
                    jobs.append(executor.submit(image_file_save_func, image_dir, page_num, page))
                except:
                    app_logger.exception(f'{image_dir}/page_{str(page_num + 1).zfill(3)}_image.png 저장 실패')
                    
            results = [job.result() for job in concurrent.futures.as_completed(jobs)]
        
        # 작업 상태 및 일시 업데이트
        if all(results):
            
            # 업데이트 수행
            qm.update_pdf_extract(file_id, is_start=False)
            qm.update_pdf_file_length(file_id, len(doc))
            
            app_logger.info(f'{pdf_file} PDF 파일 처리 종료.')
            print(f'[INFO] {pdf_file} PDF 파일 처리 종료.')
    
    app_logger.debug(f'========== PDF EXTRACT 처리 종료 ==========\n')
    return