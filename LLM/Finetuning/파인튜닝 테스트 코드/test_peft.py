import torch
from peft import AutoPeftModelForCausalLM
from transformers import AutoTokenizer
 
peft_model_id = "./test-model"
 
# Load Model with PEFT adapter
model = AutoPeftModelForCausalLM.from_pretrained(
  peft_model_id,
  torch_dtype=torch.float16,
  quantization_config= {"load_in_4bit": True},
  device_map="auto"
)
tokenizer = AutoTokenizer.from_pretrained(peft_model_id)

import datetime

def today():
    return datetime.datetime.strftime(datetime.datetime.now(),'%Y-%m-%d %H:%M:%S %A')

input_text = input('LLM 질문 :')

prompt = '''당신은 텍스트에서 엔터티를 추출하도록 설계된 도우미다.
사용자는 텍스트 문자열을 붙여넣고 텍스트에서 추출한 엔터티를 JSON 개체로 응답한다.

오늘의 날짜 및 시각은 ''' + today() + '''이다.
출력 형식의 예는 다음과 같다.

USER : "홍길동의 주소는 뭐야?"
ASSISTANT : {"inquirytype":"call", "name":"홍길동", "reqData":"주소"}

USER : "내일 오전 10시~11시까지 중회의실 예약해줘"
ASSISTANT : {"inquirytype":"reserveMeeting", "meetingRoom":"중회의실", "startDate":"", "endDate":""}

- 다른 내용 없이 JSON 내용만 반환한다.
- 여러 inquery일 경우 inquery 별 JSON으로 최대한 자세하게 반환한다.
- 예가 없는 경우 "이해할 수 없습니다."라고 반환한다.'''

messages = [{"role": "system", "content": prompt}] + [{"role": "user", "content": input_text}]

input_ids = tokenizer.apply_chat_template(
    messages,
    add_generation_prompt=True,
    return_tensors="pt"
).to("cuda")

terminators = [
    tokenizer.eos_token_id,
    tokenizer.convert_tokens_to_ids("<|eot_id|>")
]

outputs = model.generate(
    input_ids,
    max_new_tokens=512,
    eos_token_id=terminators,
    do_sample=True,
    temperature=0.2,
    top_k=50,
    top_p=0.8,
    pad_token_id=tokenizer.eos_token_id,
    repetition_penalty=1.2,
).to("cuda")

response = outputs[0][input_ids.shape[-1]:]

print(tokenizer.decode(response, skip_special_tokens=True))

