from config.config import *
from database.query import QueryMethod
from gpt_ocr.gpt_ocr import gpt_ocr
from utils.logger import setup_logger, apply_logger

import os, asyncio, json

# DB 처리 인스턴스
qm = QueryMethod()

app_logger = setup_logger('IMAGE_OCR', 'image_ocr_log')


async def async_gpt_request(image_file_list:list):
    '''
    GPT 비동기 요청 함수
    '''
    tasks = [gpt_ocr(img_file) for img_file in image_file_list]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    ocr_results = []
        
    for img_file, result in zip(image_file_list, results):
        if isinstance(result, Exception):
            # 페이지 단위 실패
            ocr_results.append({
                "image": img_file,
                "success": False,
                "error": str(result)
            })
        else:
            ocr_results.append({
                "image": img_file,
                "success": True,
                **result
            })

    return ocr_results


@apply_logger(logger_name='IMAGE_OCR', log_file_suffix='image_ocr_log')
def image_ocr():
    '''
    GPT OCR 수행 작업
    '''
    app_logger.debug(f'========== IMAGE OCR 처리 시작 ==========')
    select_result = qm.select_ocr_metadata()
    
    if not select_result:
        app_logger.debug(f'처리 필요한 데이터 없음.')
        app_logger.debug(f'========== IMAGE OCR 처리 종료 ==========\n')
        return 
    
    for idx, pdf_data in enumerate(select_result):
        # 언패킹
        file_id, category, cmpn_nm, total_page = pdf_data
        
        # 경로 설정
        process_dir = f"{BASE_DIR}/{cmpn_nm}/{category}/{file_id}"
        
        image_dir = f"{process_dir}/images/"
        image_file_list = sorted(f'{image_dir}{file}' for file in os.listdir(image_dir) if file[-4:] == '.png')
        
        # # 테스트 슬라이싱
        # image_file_list = image_file_list[:3]
        
        # OCR 결과 저장 경로 설정
        if not os.path.exists(f'{process_dir}/ocr_data'):
            os.makedirs(f'{process_dir}/ocr_data')
        else:
            # 처리 내역 로컬에 존재할 경우 다음 작업 진행
            app_logger.warning(f'{file_id} 로컬 처리 내역 확인')
            continue

        # OCR 수행
        app_logger.debug(f'{file_id} 매뉴얼 GPT OCR 처리 중...')
        print(f'[DEBUG] {file_id} 매뉴얼 GPT OCR 처리 중...')
        
        # 시작 시각 업데이트
        qm.update_ocr_status(file_id)
        
        # 비동기 호출
        try:
            ocr_data = asyncio.run(async_gpt_request(image_file_list))
        except Exception as e:
            app_logger.error(f'{file_id} 매뉴얼 OCR 오류 : {e}')
            os.rmdir(f'{process_dir}/ocr_data')
            # 시작시간 제거
            qm.update_ocr_failure_status(file_id)
            continue
        
        app_logger.debug(f'GPT OCR 처리 완료')
        print('[DEBUG] GPT OCR 처리 완료')  
        
        with open(f'{process_dir}/ocr_data/ocr_result.json', 'w', encoding='utf-8') as file:
            file.write(json.dumps(ocr_data, ensure_ascii=False, indent=4))
            
        app_logger.debug(f'{process_dir}/ocr_data/ocr_result.json 저장 완료')
        print(f'[DEBUG] {process_dir}/ocr_data/ocr_result.json 저장 완료')
        
        # 상태값 및 종료 시각 업데이트
        qm.update_ocr_status(file_id, is_start=False)
        
        # # 테스트 루프
        # if idx == 2:
        #     break
    
    app_logger.debug(f'========== IMAGE OCR 처리 종료 ==========\n')
    return