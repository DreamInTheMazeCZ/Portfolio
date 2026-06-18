from config.config import *
from database.query import QueryMethod
from embeddings.embedder import clean_text, get_embeddings
from utils.logger import setup_logger, apply_logger

import os
import json
import pandas as pd

# DB 처리 인스턴스
qm = QueryMethod()

app_logger = setup_logger('DATA_INSERT', 'data_insert_log')

@apply_logger(logger_name='DATA_INSERT', log_file_suffix='data_insert_log')
def data_insert():
    app_logger.debug(f'========== PDF DATA INSERT 처리 시작 ==========')
    
    # 작업 리스트 추출
    insert_list = qm.select_insert_metadata()    
    
    if not insert_list:
        app_logger.debug(f'처리 필요한 데이터 없음.')
        app_logger.debug(f'========== PDF DATA INSERT 처리 완료 ==========\n')
        return 
    
    for metadata in insert_list:
        # 언패킹
        file_id, category, cmpn_nm = metadata
        
        app_logger.debug(f'{cmpn_nm} - {file_id} 임베딩 및 인서트 작업 수행')
        
        qm.update_data_extract(file_id)
        
        # OCR 결과 경로 설정
        # image_path는 IMG_URL 뒤에 붙는 웹 경로이므로, 컨테이너 절대경로가 아닌
        # BASE_DIR의 마지막 디렉토리명(예: 'extraction')만 사용한다.
        # (기존 './extraction' → 'extraction' 동작을 절대경로에서도 동일하게 유지)
        base_url_segment = os.path.basename(os.path.normpath(BASE_DIR))
        image_dir = f"{base_url_segment}/{cmpn_nm}/{category}/{file_id}/images"
        json_data_dir = f"{BASE_DIR}/{cmpn_nm}/{category}/{file_id}/ocr_data/ocr_result.json"
        
        with open(json_data_dir, 'r', encoding='utf-8') as f:
            ocr_data = json.loads(f.read())
        
        # 불필요 페이지 제외 처리
        exception_list = ['목차', '머리말', '메모', '색인', '', '목 차', '색 인', '품질보증서', '메 모']
        
        df = pd.DataFrame(ocr_data)
        df['section'] = df['section'].map(lambda x: str(x).strip().replace('  ', ' '))
        df = df[(~ df.section.isin(exception_list))
                 & (~ df.section.str.contains('감사합니다'))
                 & (~ df.section.str.contains('증서'))]
        
        # 데이터 통합
        df['file_id'] = file_id
        df = df[~ df.contents.isna()]
        
        # 텍스트 정규화
        df['contents'] = df['contents'].map(clean_text)
        # 벡터 임베딩
        df['emb'] = df['contents'].map(get_embeddings)
        # 이미지 URL 주소 생성
        df['image_path'] = df['page_num'].map(lambda x: f'{IMG_URL}{image_dir}/page_{str(x).zfill(3)}.png')
        
        # List[Tuple] 형태 변환
        insert_value = [
            (
                data['file_id'], data['page_num'], data['contents'],
                data['image_path'], data['table'], data['section'],
                data['header'], data['emb'].tolist(), data['prompt_tokens'],
                data['completion_tokens'], data['usage'], data['processing_time']
            )
            for _, data in df.iterrows()
        ]
        
        # 100개씩 인서트 처리
        batch_size = 100
        for i in range(0, len(insert_value), batch_size):
            chunk = insert_value[i:i + batch_size]
            qm.insert_data_table(chunk)        
        
        qm.update_data_extract(file_id, is_start=False)
        
        app_logger.debug(f'{cmpn_nm} - {file_id} 인서트 완료')
        
    app_logger.debug(f'========== PDF DATA INSERT 처리 완료 ==========\n')
    return
