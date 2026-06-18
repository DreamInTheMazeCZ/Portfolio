from peft import AutoPeftModelForCausalLM
 
# Load PEFT model on CPU
model = AutoPeftModelForCausalLM.from_pretrained(
    './test-model',
    torch_dtype=torch.float16,
    low_cpu_mem_usage=True,
)
# Merge LoRA and base model and save
merged_model = model.merge_and_unload()
merged_model.save_pretrained('./test-model',safe_serialization=True, max_shard_size="2GB")
