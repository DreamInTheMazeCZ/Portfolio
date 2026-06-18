import base64, json

def encode_image(image_path: str):
    '''
    이미지 파일 base64 인코딩
    '''
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

def usage(in_token, out_token):
    '''
    GPT5-Mini 사용요금 계산 (원화)
    '''
    return round((0.00000025 * in_token + 0.000002 * out_token) * 1450, 3)

def parse(text: str):
    '''
    JSON 파싱 메서드
    '''
    text = text.strip()
    
    if text.startswith("```"):
        text = text.strip("`")
        text = text.replace("json", "", 1).strip()
    return json.loads(text)