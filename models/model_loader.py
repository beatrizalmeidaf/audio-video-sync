import os
import torch
import gc
from dotenv import load_dotenv
from huggingface_hub import login, snapshot_download
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor as SpeechProcessor, pipeline

load_dotenv()

def authenticate_hf():
    print("\n0. Authenticating with Hugging Face...")
    hf_token = os.environ.get("HF_TOKEN", "").strip()
    if hf_token:
        login(token=hf_token)
        print("✓ Hugging Face authenticated securely.")
    else:
        print("Warning: HF_TOKEN not found!")
    return torch.cuda.is_available()

def load_whisper():
    use_gpu = authenticate_hf()
    device = "cuda" if use_gpu else "cpu"
    torch_dtype = torch.bfloat16

    print(f"\n1. Setting up Whisper model (Transcription) on {device}...")
    whisper_id = "openai/whisper-large-v3"

    whisper_model = AutoModelForSpeechSeq2Seq.from_pretrained(
        whisper_id, torch_dtype=torch_dtype, low_cpu_mem_usage=True, use_safetensors=True
    )
    if use_gpu: whisper_model = whisper_model.to(device)

    whisper_processor = SpeechProcessor.from_pretrained(whisper_id)

    whisper_pipe = pipeline(
        "automatic-speech-recognition",
        model=whisper_model,
        tokenizer=whisper_processor.tokenizer,
        feature_extractor=whisper_processor.feature_extractor,
        chunk_length_s=30,
        batch_size=1,
        return_timestamps=True,
        torch_dtype=torch_dtype,
        device=device,
    )
    return whisper_pipe

def load_gemma():
    use_gpu = torch.cuda.is_available() 
    device = "cuda" if use_gpu else "cpu"
    torch_dtype = torch.bfloat16

    print(f"\n2. Setting up TranslateGemma model (Translation) on {device}...")
    gemma_local_path = snapshot_download(
        repo_id="google/translategemma-4b-it"
    )

    gemma_pipe = pipeline(
        "image-text-to-text", 
        model=gemma_local_path,
        device=device,
        torch_dtype=torch_dtype
    )
    return gemma_pipe