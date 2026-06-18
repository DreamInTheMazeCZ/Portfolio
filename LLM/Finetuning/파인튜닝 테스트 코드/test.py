import torch

if torch.cuda.get_device_capability()[0] >= 8:
    
    attn_implementation = "flash_attention_2"
    torch_dtype = torch.bfloat16
else:
    attn_implementation = "eager"
    torch_dtype = torch.float16

print(attn_implementation)
