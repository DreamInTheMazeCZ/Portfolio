CCELERATE_USE_FSDP=1 FSDP_CPU_RAM_EFFICIENT_LOADING=1 torchrun --nproc_per_node=1 run_fsdp_qlora.py --config llama_3_70b_fsdp_qlora.yaml
명령어를 통해 실행

run_fsdp_qlora.py에 QLoRA 및 FSDP 학습기 설정
nproc_per_node 수를 조절하여 오류 방지