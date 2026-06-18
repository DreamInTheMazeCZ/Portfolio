from sentence_transformers import SentenceTransformer

embedding_model = SentenceTransformer("dragonkue/bge-m3-ko")

import re


def clean_text(text: str) -> str:
    '''
    텍스트 정규화 함수
    '''
    # 줄바꿈/탭 공백 변환
    text = text.replace("\n", " ").replace("\t", " ")
    # 특수문자 제거
    text = re.sub(r"[.·•●▪▶▷※◆◇→←↑↓“”\u3400-\u4DBF\u4E00-\u9FFF\uF900-\uFAFF]", " ", text)
    # 불필요한 구분선/특수문자 (----, ==== 등) 제거
    text = re.sub(r"[-=]{2,}", " ", text)
    # 스트립 처리
    text = text.strip()
    # 불필요한 구분선/특수문자 (----, ==== 등) 제거
    text = re.sub(r"[^가-힣ㄱ-ㅎa-zA-Z0-9 \|#\-]", "", text)
    # 중복 공백 제거
    text = re.sub(r"\s+", " ", text)
    return text


def get_embeddings(text:str) -> list:
    '''
    임베딩 벡터 생성 함수
    '''
    return embedding_model.encode(text)