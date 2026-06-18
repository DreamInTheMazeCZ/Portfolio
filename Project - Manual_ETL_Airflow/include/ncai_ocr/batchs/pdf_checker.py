from config.config import *
from database.query import QueryMethod
from utils.logger import setup_logger, apply_logger

import os
import pandas as pd

# DB 처리 인스턴스
qm = QueryMethod()

app_logger = setup_logger('FILE_CHECKER', 'pdf_file_check_log')

def info_extract(pdf_file:str):
    '''
    파일명에서 농기계 형식명, File_ID 등 추춣
    '''
    pdf_model_nm = pdf_file.split('트랙터')[0].split(' ')[1]
    
    series_nm = ''

    if ',' in pdf_model_nm:
        for s in pdf_model_nm:
            if s != ',' and s.isalpha():
                series_nm += s
            elif s != ',' and not s.isalpha():
                break
            elif s == ',':
                break
            
    if series_nm:
        model_nm_list = [f"{series_nm}{nm.replace(series_nm, '')}" for nm in pdf_model_nm.split(',')]
        model_nm = ','.join(model_nm_list)
    else:
        if ',' in pdf_model_nm:
            model_nm_list = [f"{series_nm}{nm.replace(series_nm, '')}" for nm in pdf_model_nm.split(',')]
            model_nm = ','.join(model_nm_list)
        else:
            model_nm = pdf_model_nm

    file_id = int(pdf_file.split('.')[0])
    
    return (model_nm, file_id)


@apply_logger(logger_name='FILE_CHECKER', log_file_suffix='pdf_file_check_log')
def pdf_file_checker():
    '''
    클라이언트 내 PDF 파일과 DB PDF 파일 확인하여 필요 데이터 DB 삽입 작업
    '''
    app_logger.debug(f'========== PDF CHECKER 처리 시작 ==========')

    # 파일명에서 필요 정보 추출 (제조사 목록은 런타임에 디렉토리 스캔)
    for cmpn_nm in get_maker_list():
        # 데이터 컨테이너
        status_data_container = []
        file_data_container = []
    
        pdf_file_list = [file for file in os.listdir(f'{PDF_DIR}/{cmpn_nm}') if file[-4:] == '.pdf']
        # 매뉴얼 파일이 없는 경우
        if not pdf_file_list:
            app_logger.debug(f'{cmpn_nm} 데이터 없음.')
            print(f'[DEBUG] {cmpn_nm} 데이터 없음.')
            continue
        
        for idx, file_nm in enumerate(pdf_file_list):
            if '트랙터' in file_nm:
                category = 'AC'
            elif '콤바인' in file_nm:
                category = 'AD'
            elif '이앙기' in file_nm:
                category = 'AE'
            else:
                category = 'AZ'
            model_nm, file_id = info_extract(file_nm)
            
            status_data_container.append((file_id, False, False, False, file_nm, cmpn_nm, category, model_nm))

        # 로컬 데이터 취합
        local_file_df = pd.DataFrame(
            status_data_container,
            columns=['file_id', 'is_extract', 'is_ocr', 'is_insert', 'file_nm', 'cmpn_nm', 'category', 'model_name']
        )

        file_id_list = local_file_df.file_id.map(str).tolist()
        
        # 테이블에 존재하는 FILE ID 제외하고 처리
        select_result = qm.select_status_table(file_id_list)
        
        print(f'[DEBUG] pdf_extraction_status 조회된 매뉴얼 파일 개수 : {len(select_result)}개')
        app_logger.debug(f'pdf_extraction_status 조회된 매뉴얼 파일 개수 : {len(select_result)}개')

        status_insert_df = local_file_df[~ local_file_df.file_id.isin(select_result)].iloc[:,:4].copy()
        print(f'[DEBUG] {cmpn_nm} 로컬 존재 매뉴얼 파일 개수 : {len(local_file_df)}개')
        app_logger.debug(f'{cmpn_nm} 로컬 존재 매뉴얼 파일 개수 : {len(local_file_df)}개')
        
        # 처리된 내역 제외
        exists_list = qm.select_exists_status()
        status_insert_df = status_insert_df[~ status_insert_df.file_id.isin(exists_list)]
            
        # 테이블에 존재하지 않는 FILE ID가 있는 경우에만 DB INSERT
        if not len(status_insert_df) == 0:
            
            status_insert_values = [tuple(data.values) for _, data in status_insert_df.iterrows()]
            
            # ===== pdf_extraction_status 인서트 =====
            qm.insert_status_table(status_insert_values)
            
            print(f'[DEBUG] pdf_extraction_status INSERT 완료.')
            app_logger.debug(f'pdf_extraction_status INSERT 완료 {len(status_insert_df)}개 -\n{status_insert_df.file_id.tolist()}')
            
            # 모델명 정규화 처리
            model_insert_df = local_file_df.iloc[:, [0, -1]]
            model_insert_df['model_name'] = model_insert_df.model_name.str.split(',')
            model_insert_df = model_insert_df.explode('model_name').reset_index(drop=True)
            
            model_insert_values = [tuple(data.values) for _, data in model_insert_df.iterrows()]
            
            # ===== pdf_extraction_model 인서트 =====
            qm.insert_model_table(model_insert_values)
            
            print(f'[DEBUG] pdf_extraction_model INSERT 완료.')
            app_logger.debug(f'pdf_extraction_model INSERT 완료 {len(model_insert_df)}개')
            
        else:
            print(f'[DEBUG] pdf_extraction_status 신규 처리 없음.')
            app_logger.debug(f'pdf_extraction_status 신규 처리 없음.')
        
        # FILE 테이블 확인
        select_result = qm.select_file_table(file_id_list, cmpn_nm)
        app_logger.debug(f'pdf_extraction_file 조회 FILE ID : {select_result}')

        file_insert_df = local_file_df[~ local_file_df.file_id.isin(select_result)].iloc[:, [0, -4, -3, -2]].copy()
        
        if not len(file_insert_df) == 0:
            # ===== pdf_extraction_file 인서트 =====
            file_insert_values = [
                (data['file_id'], data['file_nm'], data['cmpn_nm'], data['category'])
                for _, data in file_insert_df.iterrows()
            ]
            
            qm.insert_file_table(file_insert_values)
            
            print(f'[DEBUG] pdf_extraction_file INSERT 완료.')
            app_logger.debug(f'pdf_extraction_file INSERT {len(file_insert_df)}개 -\n{file_insert_df.file_id.drop_duplicates().tolist()}')
        else:
            print(f'[DEBUG] pdf_extraction_file 신규 처리 없음.')
            app_logger.debug(f'pdf_extraction_file 신규 처리 없음.')
            
    app_logger.debug(f'========== PDF CHECKER 처리 종료 ==========\n')
    return