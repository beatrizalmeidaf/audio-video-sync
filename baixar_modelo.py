import os
from huggingface_hub import login, snapshot_download

HF_TOKEN = "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"

print("1. Fazendo login no Hugging Face...")
login(token=HF_TOKEN)

print("\n2. Iniciando download seguro do TranslateGemma...")

snapshot_download(
    repo_id="google/translategemma-4b-it",
    cache_dir="./hf_cache",
    max_workers=4 # usa mais conexões para baixar mais rápido
)

print("\n✓ Download concluído com sucesso!")