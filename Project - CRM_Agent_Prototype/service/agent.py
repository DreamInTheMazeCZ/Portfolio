#!/usr/bin/env python
# coding: utf-8

from langchain.prompts import ChatPromptTemplate
from langchain.schema.output_parser import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

from langchain.text_splitter import RecursiveCharacterTextSplitter

from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.document_loaders.csv_loader import CSVLoader
from langchain_community.vectorstores import Chroma

from langchain_openai import ChatOpenAI

from langchain.callbacks import get_openai_callback

from dotenv import load_dotenv
from logging import handlers

import os, warnings, re, datetime, ast, logging, pymysql

load_dotenv()
warnings.filterwarnings('ignore')

# ===== Logging =====
now_date = datetime.datetime.now().strftime("%Y-%m-%d") # Current Date
now_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") # Current Time

if not os.path.isdir(f'./logs'):
    os.mkdir(f'./logs')

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler = handlers.TimedRotatingFileHandler(
    f'logs/ai_agent_log_{now_date}.log',
    when='d',
    interval=7,
    backupCount=7,
    atTime='midnight',
    encoding='utf-8'
)
file_handler.setFormatter(formatter)
file_handler.setLevel(logging.INFO)

logger = logging.getLogger()
if not logger.handlers:
    logger.addHandler(file_handler)
logger.setLevel(logging.INFO)

# ===== DB Connection Info =====
DB_HOST = os.getenv('DB_HOST')
DB_USER = os.getenv('DB_USER')
DB_PW = os.getenv('DB_PW')
DB_NM = os.getenv('DB_NM')
DB_PORT = os.getenv('DB_PORT')

conn_info = {
    'host':DB_HOST,
    'user':DB_USER,
    'password':DB_PW,
    'db':DB_NM,
    'port':int(DB_PORT),
    'cursorclass':pymysql.cursors.DictCursor
}

# ===== Vector Embedding 모델 (Hugging Face) =====
embeddings_model = HuggingFaceEmbeddings(
    model_name='jhgan/ko-sroberta-nli',
#     model_kwargs={'device':'cpu'},  # GPU / CPU Toggle
    encode_kwargs={'normalize_embeddings':True},
)

# ===== Vector DB 디렉토리 =====
DB_PATH_HF = "./VectorDB"

# ===== OpenAI 연결 설정 =====
os.environ['OPENAI_API_KEY'] = os.getenv('CONVAI_API_KEY')
os.environ['OPENAI_API_BASE'] = os.getenv('CONVAI_API_BASE')

# ===== OpenAI 객체 생성 =====
llm = ChatOpenAI(
    model=os.getenv('CONVAI_MODEL'),
    organization=os.getenv('CONVAI_OR_ID'),
    api_key=os.getenv('CONVAI_API_KEY'),
    seed=2025
    # 시드 설정은 가능하나 작동은 안 하는듯
)

# 조회 필요 테이블 추가
DB_TABLE = ['customer', 'client']

# ===== Vector DB 데이터 덤프 =====

# 기존 DB 존재
if os.path.isdir(DB_PATH_HF):
    if os.path.isfile(f'{DB_PATH_HF}/chroma.sqlite3'):
        vectorstore = Chroma(
            persist_directory=DB_PATH_HF,
            embedding_function=embeddings_model
        )

# 따로 컨트롤러를 만드는 것이 효율적일 듯
else:
    # ===== 전처리 파일 로드 =====
    loader = CSVLoader(file_path=f'./service/rag_form_data.csv', encoding='utf-8')
    csv_data = loader.load()

    # ===== 분할 객체 생성 =====
    splitter = RecursiveCharacterTextSplitter(
        chunk_size = 1500,      # Title:Contents 내용을 모두 담을 수 있을 정도의 크기 설정
        chunk_overlap  = 100,
        length_function = len,
    )

    # ===== 분할 =====
    splits = splitter.split_documents(csv_data)

    # ===== Vector DB 생성 =====
    vectorstore = Chroma.from_documents(
        documents=splits,
        embedding=embeddings_model,
        persist_directory = f'{DB_PATH_HF}',
        collection_metadata = {'hnsw:space': 'cosine'}, # 코사인 유사도
        collection_name = 'agent'             # DB 이름
    )

def db_select(query: str, connection_info: dict = conn_info) -> list:
    '''
    DB 조회 (R)
    input : 쿼리문 str, 접속정보 dict
    output : 쿼리 결과
    '''
    try:
        logger.info('DB connecting')
        conn = pymysql.connect(**connection_info)  # Keyword arguments
        cur = conn.cursor()
        cur.execute(query)
        data = cur.fetchall()
    except Exception as e:
        logger.exception('DB exception')
    else:
        logger.info('DB connection complete')
        return data
    finally:
        conn.close()
        logger.info('DB closed')


def get_cust_nm_list() -> list:
    cust_nm_query = '''
SELECT DISTINCT CustNm FROM customer
WHERE 1=1
AND CustNm IS NOT NULL
AND CustNm <> ''
AND CustNm NOT LIKE '%고객%'
'''
    cust_nm = db_select(cust_nm_query)
    pre_process_1 = [nm['CustNm'].split(')')[1] if ')' in nm['CustNm'] else nm['CustNm'] for nm in cust_nm ]
    pre_process_2 = [re.sub(r'[^가-힣]', '', nm) for nm in pre_process_1 if re.sub(r'[^가-힣]', '', nm)]
    return pre_process_2


def get_client_nm_list() -> list:
    cilent_nm_query = '''
SELECT DISTINCT ClientNm FROM client
WHERE 1=1
AND ClientNm IS NOT NULL
AND ClientNm <> ''
AND ClientNm NOT LIKE '%고객사%'
'''
    cilent_nm = db_select(cilent_nm_query)
    pre_process = [nm['ClientNm'].replace('(주)','').replace('(사)','').replace('(재)','').replace('㈜','').strip() for nm in cilent_nm]
    return pre_process


# ***** 추후 Cashing 등 프로그래밍적 처리가 필요할 경우 Class로 묶어 개발 ***** 


# ===== Vector DB 검색기 =====
# k값을 적정한 수로 설정 (retriever.get_relevant_documents('질문') 메서드를 통해 Vector DB 검색값 확인 가능)
retriever = vectorstore.as_retriever(
    search_kwargs={"k": 7},
)

# ===== RAG 문서 결합 =====
def format_docs(docs:list) -> str:
    return '\n\n'.join(doc.page_content for doc in docs)

def return_now_time():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def return_classifier_result(user_question:str) -> dict:
    '''
    사용자 입력(질문) 의도 분류 함수
    '''
    # ===== Prompt =====
    # RAG를 활용하면 토큰 비용을 감소시킬 수 있을 듯

    template = '''당신은 자연어를 3개의 값으로 분류해 JSON 형태로 반환해주는 전문 AI입니다.
분류가 필요한 값으로는 ["정보", "일정", "영업"] 세 가지입니다.
분류가 필요한 값의 예를 들면 다음과 같습니다.

정보 : 홍길동의 전화번호와 주소를 알려주세요.
정보 : SZ사의 대표와 사업자번호를 알려주세요.

일정 : 오늘 일정 확인
일정 : 모레 회의 몇시야?
일정 : 교육 시간 알려주세요.

영업 : CRM 시스템 도입 건 관련 영업기회 보여줘
영업 : 솔루션 계약 조건 확인하고 싶어.
영업 : SZ사와 협상 내용이 뭐였지?

예를 들어 "이번주 수요일 오후 3시에 SZ사 [CRM 시스템 도입 건] 영업기회와 관련하여 [홍길동] 차장에게 WESEED CRM 견적서 제출 일정 등록해주세요."라는 질문은
{{"일정":"이번주 수요일 오후 3시 홍길동 차장 견적서 제출 일정", "영업":"CRM 시스템 도입 건"}}으로 분류해야 합니다. Question을 참고하여 답변해주세요.

Question: {question}
'''

    prompt = ChatPromptTemplate.from_template(template)

    # ===== LangChain =====
    rag_chain = (
        {'question': RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )
    
    with get_openai_callback() as cb:
        llm_return = rag_chain.invoke(user_question)
        cost = cb.total_cost
        
    # ===== 인풋 - LLM 결과 - 타입 변환 값 로깅 =====
    # 해당 부분 추후 LangSmith 연동하여 모니터링 하는 것이 좋을 듯        
    logger.info(f'\nINTENT PROCESSOR\n\nUSER :\n{user_question}\n\nLLM :\n{llm_return}')
    
    try:
        return dict({'Cost':cost}, **ast.literal_eval(llm_return))
    except:
        logger.exception(f'Intent processing error : {user_question}')
        return [{"message":"Intent processing error"}]


def return_information_result(user_question:str) -> list:
    '''
    정보로 분류된 질문에 대한 JSON 반환 함수
    '''
    # ===== Prompt =====
    # txt 등 파일 형태로 관리해 여러 프롬프트 사용하는 방법으로 확장 가능할 듯
    
    template = '''당신은 자연어를 JSON 형태의 정형 데이터로 변환해주는 전문 AI입니다.
형식은 {{"inquiryPhysicalColumn": inquiryPhysicalColumn, "inquiryLogicalColumn": inquiryLogicalColumn, "actionItem": actionItem, "inquiryWhere": inquiryWhere}} 입니다.
예를 들면 {{"inquiryPhysicalColumn": ["TelNo", "Mobile"], "inquiryLogicalColumn": "전화번호", "actionItem": "전화번호", "inquiryWhere": "홍길동"}}의 형태입니다.
inquiryPhysicalColumn과 inquiryLogicalColumn, actionItem의 값은 아래의 Context에서 참고하고, 자연어에서는 inquiryWhere를 추출합니다.
inquiryWhere는 명사이고, 모든 Value는 여러 개일 수 있습니다.

또한 "홍길동 전화번호 알려주고 김길동 주소 알려줘" 와 같은 질문의 경우,
{{"inquiryPhysicalColumn": ["TelNo", "Mobile"], "inquiryLogicalColumn": "전화번호", "actionItem": "전화번호", "inquiryWhere": "홍길동"}},
{{"inquiryPhysicalColumn": ["Addr1", "Addr2"], "inquiryLogicalColumn": "주소", "actionItem": "주소", "inquiryWhere": "김길동"}}
형태로 출력해주세요.

Context: {context}

Question: {question}
'''

    prompt = ChatPromptTemplate.from_template(template)

    # ===== LangChain =====
    rag_chain = (
    {'context': retriever | format_docs, 'question': RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
    )
    
    with get_openai_callback() as cb:
        llm_return = rag_chain.invoke(user_question)    
        cost = cb.total_cost
    
    # ===== LLM 답변 타입 처리 =====
    try:
        if '},' in llm_return:
            result_list = [ast.literal_eval(f'{i}}}'.replace('}}','}')) for i in llm_return.replace('\n','').replace(' ','').strip('`json').split('},') if i]
        else:
            result_list = [ast.literal_eval(i) for i in llm_return.strip('`json').split('\n') if i]
    except:
        logger.exception(f'Type transformation error : {llm_return}')
        return [{"message":"Type transformation error"}]
    
    # ===== 인풋 - LLM 결과 - 타입 변환 값 로깅 =====
    # 해당 부분 추후 LangSmith 연동하여 모니터링 하는 것이 좋을 듯
    logger.info(f'\nINFORMATION PROCESSOR\n\nUSER :\n{user_question}\n\nLLM :\n{llm_return}\n\nPROCESSING :\n{result_list}')
    
    # ===== inquiryTable 검색 =====
    # 정확하지 않으면 개인정보 등의 문제를 야기할 수 있으므로 정보를 찾을 수 없다는 내용으로 개발하는 것이 좋을 듯
    
    try:
        
        # CustNm, ClientNm DB 추출
        cust_nm_list = get_cust_nm_list()
        client_nm_list = get_client_nm_list()
        
        for idx, answer in enumerate(result_list):
            
            # LIST 타입 반환 시 오류 방지
            try:
                find_nm = answer['inquiryWhere']
            except:
                find_nm = answer['inquiryWhere'][0]

            # ===== CustNm 검색 =====
            if ', '.join(cust_nm_list).find(find_nm) != -1 or find_nm in cust_nm_list:
                result_dict = dict({'inquiryTable':'customer'}, **answer)

            # ===== ClientNm 검색 =====
            if ', '.join(client_nm_list).find(find_nm) != -1  or find_nm in client_nm_list:
                result_dict = dict({'inquiryTable':'client'}, **answer)

                
            # ===== Table 추가마다 식별 가능한 조건 추가 혹은 다른 Table을 출력해주는 등 처리가 필요 =====
            # 예를 들면 일정의 경우 날짜 및 시간 데이터가 있는 경우 schedul 테이블을 출력하는 등
            

            # ===== 검색 결과 없을 시 NULL (None) 반환 =====
            # 해당 결과를 활용해 정보를 찾지 못했다는 내용 등 처리
            result_dict = result_dict if locals()['result_dict'] else dict({'inquiryTable':None}, **answer)            
            
            # ===== Customer 테이블과 Client 테이블 간 컬럼명이 다른 경우 =====
            # 아래와 같은 경우에만 분기 생성하면 될
            if 'Mobile' in result_dict['inquiryPhysicalColumn'] and 'TelNo' in result_dict['inquiryPhysicalColumn']:
                result_dict['inquiryPhysicalColumn'] = ['Mobile'] if result_dict['inquiryTable'] == 'customer' else ['TelNo']
                
            if 'CustGrade' in result_dict['inquiryPhysicalColumn'] and 'ClientGrade' in result_dict['inquiryPhysicalColumn']:
                result_dict['inquiryPhysicalColumn'] = ['CustGrade'] if result_dict['inquiryTable'] == 'customer' else ['ClientGrade']

            # ===== 리스트 재조합 =====
            result_list[idx] = result_dict
            
    except:
        logger.exception(f'Data processing error : {result_list}')
        return [{"message":"Data processing error"}]
        
    return [{"Information":result_list, "Cost":cost}]


def return_schedul_result(user_question:str) -> list:
    '''
    일정으로 분류된 질문에 대한 JSON 반환 함수
    '''
    # ===== Prompt =====
    # RAG를 활용하면 토큰 비용을 감소시킬 수 있을 듯

    template = '''당신은 자연어를 JSON 형태의 정형 데이터로 변환해주는 전문 AI입니다.
자연어를 구분하는 기준은 ["Gubun" : 구분, "StartDT" : 시작일시, "EndDT" : 종료일시, "Addr" : 주소, "Title" : 제목] 입니다.
"Gubun"은 ["MEETING" (회의, 미팅), "EDUCATION" (교육), "OUTSIDE" (외부, 외근, 외출), "SEMINAR" (세미나), "None" (해당 없음)] 다섯 개의 값을 가집니다.
"StartDT" 및 "EndDT" 는 현재시각 {now_time} 기준으로 연산해주세요.
출력할 JSON 형식의 키 값은 {{"Gubun", "StartDT", "EndDT", "Addr", "Title", "actionItem"}} 입니다.

예를 들어 "오늘 일정 알려주세요."라는 질문에는 {{"StartDT":{now_time}, "EndDT":{now_time} "actionItem":"일정 확인"}}와 같이 답변하고,
"내일 오후 3시 CRM 견적서 제출 일정 등록"이라는 질문에는 {{"Gubun":"OUTSIDE", "StartDT":calculated_time, "EndDT":calculated_time, "actionItem":"일정 등록"}}와 같이 답변해주세요.

Question: {question}
'''

    prompt = ChatPromptTemplate.from_template(template)

    # ===== LangChain =====
    rag_chain = (
        prompt
        | llm
        | StrOutputParser()
    )
    with get_openai_callback() as cb:
        llm_return = rag_chain.invoke(
            {
                'question':user_question,
                'now_time' : return_now_time()
            }
        )
        cost = cb.total_cost
        
    
    # ===== LLM 답변 타입 처리 =====
    try:
        if '},' in llm_return:
            result_list = [ast.literal_eval(f'{i}}}'.replace('}}','}')) for i in llm_return.replace('\n','').replace(' ','').strip('`json').split('},') if i]
        else:
            llm_return = llm_return.strip('\n`json')
            result_list = [ast.literal_eval(''.join(i.strip() for i in llm_return.split('\n') if i))]
    except:
        logger.exception(f'Type transformation error : {llm_return}')
        return [{"message":"Type transformation error"}]
    
    # ===== 시각 표준화 처리 =====
    for data in result_list:
        if data.get('StartDT'):
            data['StartDT'] = data['StartDT'].replace('T', ' ')
        if data.get('EndDT'):
            data['EndDT'] = data['EndDT'].replace('T', ' ')
            
    # ===== 인풋 - LLM 결과 - 타입 변환 값 로깅 =====
    # 해당 부분 추후 LangSmith 연동하여 모니터링 하는 것이 좋을 듯
    logger.info(f'\nSCHEDUL PROCESSOR\n\nUSER :\n{user_question}\n\nLLM :\n{llm_return}\n\nPROCESSING :\n{result_list}')
    
    return [{"Schedul":result_list, "Cost":cost}]


def return_sales_result(user_question:str) -> list:
    '''
    영업으로 분류된 질문에 대한 JSON 반환 함수
    '''
    # ===== Prompt =====
    # RAG를 활용하면 토큰 비용을 감소시킬 수 있을 듯

    template = '''당신은 자연어를 JSON 형태의 정형 데이터로 변환해주는 전문 AI입니다.
자연어를 구분하는 기준은 ["SalesNm" : 영업기회명, "ProgressStep" : 진행단계, "ContractStatus" : 계약구분, "ActualStartDT" : 등록일, "ActualEndDT" : 종료일, "Memo" : 메모(비고)] 입니다.
"ProgressStep"은 ["INQUIRY" (사전문의), "CONSULT" (방문상담), "PROPOSAL" (제안 제출), "CONTRACT" (계약)] 네 개의 값을 가집니다.
"ContractStatus"은 ["SUCCESS" (성공), "FAILURE" (실패), "PENDING" (보류)] 세 개의 값을 가집니다.
"ActualStartDT" 및 "ActualEndDT" 는 현재시각 {now_time} 기준으로 연산해주세요.
출력할 JSON 형식의 키 값은 {{"SalesNm", "ProgressStep", "ContractStatus", "ActualStartDT", "ActualEndDT", "Memo", "actionItem"}} 입니다.

예를 들어 "S사 AI 센터 구축 영업기회의 진행단계를 방문상담으로 변경해주세요."라는 질문에는 {{"SalesNm":"S사 AI 센터 구축", "ProgressStep":"CONSULT", "actionItem":"영업기회 진행단계 변경"}}과 같이 답변하고,
"성공한 계약 건 알려줘"라는 질문에는 {{"ProgressStep":"SUCCESS", "actionItem":"계약 조회"}}와 같이 답변해주세요.

Question: {question}
'''

    prompt = ChatPromptTemplate.from_template(template)

    # ===== LangChain =====
    rag_chain = (
        prompt
        | llm
        | StrOutputParser()
    )
    with get_openai_callback() as cb:
        llm_return = rag_chain.invoke(
            {
                'question':user_question,
                'now_time' : return_now_time()
            }
        )
        cost = cb.total_cost
        
    
    # ===== LLM 답변 타입 처리 =====
    try:
        if '},' in llm_return:
            result_list = [ast.literal_eval(f'{i}}}'.replace('}}','}')) for i in llm_return.replace('\n','').replace(' ','').strip('`json').split('},') if i]
        else:
            llm_return = llm_return.strip('\n`json')
            result_list = [ast.literal_eval(''.join(i.strip() for i in llm_return.split('\n') if i))]
    except:
        logger.exception(f'Type transformation error : {llm_return}')
        return [{"message":"Type transformation error"}]
    
    # ===== 시각 표준화 처리 =====
    for data in result_list:
        if data.get('ActualStartDT'):
            data['ActualStartDT'] = data['ActualStartDT'].replace('T', ' ')
        if data.get('ActualEndDT'):
            data['ActualEndDT'] = data['ActualEndDT'].replace('T', ' ')
            
    # ===== 인풋 - LLM 결과 - 타입 변환 값 로깅 =====
    # 해당 부분 추후 LangSmith 연동하여 모니터링 하는 것이 좋을 듯
    logger.info(f'\nSALES PROCESSOR\n\nUSER :\n{user_question}\n\nLLM :\n{llm_return}\n\nPROCESSING :\n{result_list}')
    
    return [{"Sales":result_list, "Cost":cost}]


def ask_return(user_question:str) -> list:
    '''
    AGENT API 연결을 위한 최종 JSON 반환 함수
    해당 함수를 API와 연결하여 사용
    '''
    classifier_result = return_classifier_result(user_question)
    
    final_result = []
    
    for cls, content in classifier_result.items():
        try:
            if classifier_result.get(cls) and cls == "정보":
                final_result += return_information_result(content)
        except:
            pass
        
        try:
            if classifier_result.get(cls) and cls == "일정":
                final_result += return_schedul_result(content)
        except:
            pass
        
        try:
            if classifier_result.get(cls) and cls == "영업":
                final_result += return_sales_result(user_question)
        except:
            pass
           
    return [data for data in final_result if not data.get('message')]