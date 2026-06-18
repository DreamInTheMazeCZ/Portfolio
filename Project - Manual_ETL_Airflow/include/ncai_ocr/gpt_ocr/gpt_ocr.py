from config.config import *
from gpt_ocr.prompt import ocr_prompt
from gpt_ocr.ocr_func import encode_image, parse, usage

from openai import AsyncOpenAI

import time, asyncio, os

client = AsyncOpenAI()

async def gpt_ocr(image_file_dir_name:str):
    '''
    이미지 OCR 결과를 반환하는 GPT 호출 함수
    '''    
    # 최대 요청 개수
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)
    
    # 이미지 인코딩
    image_base64 = encode_image(image_file_dir_name)
    
    # 비동기 처리
    async with semaphore:
        start_time = time.time()
        response = await client.chat.completions.create(
            model=GPT_MODEL_NAME,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": ocr_prompt()},
                        {
                            "type": "image_url",
                            "image_url": {
                                # 이미지 처리
                                "url":f"data:image/png;base64, {image_base64}",
                                "detail":"auto"
                            }
                        },
                    ],
                }
            ]
        )
        end_time = round(time.time() - start_time, 3)
        result = response.choices[0].message.content
        
        # 토큰
        in_tokens = response.usage.prompt_tokens
        out_tokens = response.usage.completion_tokens
        
        # 구조화된 OCR 결과 반환
        try:
            result = parse(result)
        except:
            # 에러 처리를 위한 파일 생성
            if not os.path.exists(f'gpt_error_txt/{image_file_dir_name.split("/")[-3]}'):
                os.makedirs(f'gpt_error_txt/{image_file_dir_name.split("/")[-3]}')
                
            with open(f'gpt_error_txt/{image_file_dir_name.split("/")[-3]}/{image_file_dir_name[:-4].split("/")[-1]}.txt', 'w', encoding='utf-8') as f:
                f.write(result)
            raise
            
        result_dict = {
            **result,
            "page_num":int(image_file_dir_name.split('/')[-1].split('_')[1]),
            "prompt_tokens":in_tokens,
            "completion_tokens":out_tokens,
            "total_tokens":response.usage.total_tokens,
            "usage":usage(in_tokens, out_tokens),
            "processing_time":end_time
        }
    
    return result_dict