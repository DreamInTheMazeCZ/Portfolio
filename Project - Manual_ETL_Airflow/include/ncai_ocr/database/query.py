from utils.postgresql import PostgreSQL

class QueryMethod(PostgreSQL):
    """
    PDF 처리 관련 DB 쿼리 클래스
    """
      
    def __init__(self):
        super().__init__() # PostgreSQL 연결 정보 상속

    def select_status_table(self, file_id_list:list):
        '''
        pdf_extraction_status 테이블 내 처리 내역 조회 메서드
        '''
        
        query = f'''
        SELECT file_id FROM pdf_extraction_status
        WHERE file_id IN ({','.join(file_id_list)})
        AND NOT is_extract
        GROUP BY file_id
        '''
        return list(map(lambda ele: ele[0], self.select_execute(query)))
    
    
    def select_exists_status(self):
        '''
        pdf_extraction_status 테이블 내 처리된 File ID 조회
        '''
        
        query = '''
        SELECT file_id FROM pdf_extraction_status
        WHERE is_extract
        '''
        return list(map(lambda ele: ele[0], self.select_execute(query)))
    
    
    def insert_status_table(self, data_list:list):
        '''
        pdf_extrtaction_status 테이블 메타데이터 인서트 수행 메서드
        '''
        
        query = '''
        INSERT INTO pdf_extraction_status
        (file_id, is_extract, is_ocr, is_insert, created_datetime)
        VALUES (%s, %s, %s, %s, NOW())
        '''
        
        if self.executemany_query(query, data_list):
            return True
        else:
            return False
        
    
    def insert_model_table(self, data_list:list):
        '''
        pdf_extrtaction_model 테이블 메타데이터 인서트 수행 메서드
        '''
        
        query = '''
        INSERT INTO pdf_extraction_model
        (file_id, model_name, created_datetime)
        VALUES (%s, %s, NOW())
        '''
        
        if self.executemany_query(query, data_list):
            return True
        else:
            return False
        
        
    def select_file_table(self, file_id_list:list, cmpn_nm:str):
        '''
        pdf_extrtaction_file 테이블 내 처리 내역 조회 메서드
        '''
        
        query = f'''
        SELECT id FROM pdf_extraction_file
        WHERE id IN ({','.join(file_id_list)})
        AND maker_company_name = '{cmpn_nm}'
        '''
        return list(map(lambda ele: ele[0], self.select_execute(query)))
        
    
    def insert_file_table(self, data_list:list):
        '''
        pdf_extrtaction_file 테이블 메타데이터 인서트 수행 메서드
        '''
        
        query = f'''
        INSERT INTO pdf_extraction_file
        (id, name, maker_company_name, category, created_datetime)
        VALUES (%s, %s, %s, %s, NOW())
        '''
        if self.executemany_query(query, data_list):
            return True
        else:
            return False
        
        
    def select_metadata(self):
        '''
        PDF 추출이 필요한 메타데이터 추출 메서드
        '''
        
        query = f'''        
        SELECT S.file_id, F.category, F.name, F.maker_company_name
        FROM pdf_extraction_status S JOIN pdf_extraction_file F
        ON S.file_id = F.id
        AND NOT S.is_extract
        '''
        return self.select_execute(query)
    
    
    def update_pdf_extract(self, file_id:int, is_start:bool=True):
        '''
        PDF 이미지 추출 상태 관련 업데이트 메서드
        '''
        
        query = f'''
        UPDATE pdf_extraction_status
        SET {'' if is_start else 'is_extract = true,'}
        extract_{'start' if is_start else 'end'}_datetime = NOW()
        WHERE file_id = {file_id}
        '''
        
        if self.query_execute(query):
            return True
        else:
            return False
        
    
    def update_pdf_file_length(self, file_id:int, total_page:int):
        '''
        PDF 총 페이지 수 업데이트 메서드
        '''
        
        query = f'''
        UPDATE pdf_extraction_file
        SET total_page = {total_page}
        WHERE id = {file_id}
        '''
        
        if self.query_execute(query):
            return True
        else:
            return False
        
        
    def select_ocr_metadata(self):
        '''
        이미지 OCR 대상 조회 메서드
        '''
        
        query = ''' 
        SELECT S.file_id, F.category, F.maker_company_name, F.total_page
        FROM pdf_extraction_status S JOIN pdf_extraction_file F
        ON S.file_id = F.id
        AND S.is_extract -- 추출 진행
        AND NOT is_ocr -- OCR 진행 ×
        LIMIT 3
        '''
        return self.select_execute(query)
    
    
    def update_ocr_status(self, file_id:int, is_start:bool=True):
        '''
        OCR 상태 관련 업데이트 메서드
        '''
        
        query = f'''
        UPDATE pdf_extraction_status
        SET {'' if is_start else 'is_ocr = true,'}
        ocr_{'start' if is_start else 'end'}_datetime = NOW()
        WHERE file_id = {file_id}
        AND is_extract
        '''
        
        if self.query_execute(query):
            return True
        else:
            return False
        
        
    def update_ocr_failure_status(self, file_id:int):
        '''
        OCR 상태 관련 업데이트 메서드
        '''
        
        query = f'''
        UPDATE pdf_extraction_status
        SET ocr_start_datetime = NULL
        WHERE file_id = {file_id}
        AND is_extract
        AND NOT is_ocr
        '''
        
        if self.query_execute(query):
            return True
        else:
            return False
        
        
    def select_insert_metadata(self):
        '''
        INSERT 대상 문서 데이터 추출 메서드
        '''
        query = f'''
        SELECT S.file_id, F.category, F.maker_company_name
        FROM pdf_extraction_status S
        JOIN pdf_extraction_file F
        ON S.file_id = F.id
        AND S.is_extract
        AND S.is_ocr
        AND NOT S.is_insert
        '''
        return self.select_execute(query)
    
    
    def select_exists_data(self):
        '''
        INSERT 완료 데이터 추출 메서드
        '''
        query = f'''
        SELECT S.file_id
        FROM pdf_extraction_status S
        JOIN pdf_extraction_data D
        ON S.file_id = D.file_id
        AND S.is_extract
        AND S.is_ocr
        AND S.is_insert
        GROUP BY S.file_id
        '''
        return list(map(lambda ele: ele[0], self.select_execute(query)))
    
    
    def update_data_extract(self, file_id:int, is_start:bool=True):
        '''
        PDF 이미지 추출 상태 관련 업데이트 메서드
        '''
        
        query = f'''
        UPDATE pdf_extraction_status
        SET {'' if is_start else 'is_insert = true,'}
        insert_{'start' if is_start else 'end'}_datetime = NOW()
        WHERE file_id = {file_id}
        AND is_extract
        AND is_ocr
        '''
        
        if self.query_execute(query):
            return True
        else:
            return False
    
    
    def insert_data_table(self, data_list:list):
        '''
        PDF 추출 데이터 인서트 수행 메서드
        '''
        query = f'''
        INSERT INTO pdf_extraction_data
        (file_id, page_number, contents, image_path, table_contents,
        sections, titles, emb, created_datetime,
        prompt_tokens, completion_tokens, usage, processing_time)
        VALUES
        (%s, %s, %s, %s, %s, %s, %s, %s, NOW(), %s, %s, %s, %s)
        '''
        
        if self.executemany_query(query, data_list):
            return True
        else:
            return False