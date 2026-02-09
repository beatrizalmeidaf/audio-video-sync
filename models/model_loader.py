import os
import torch
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline

def initialize_models(models_dir):
    try:
        print("\n=== Initializing Models ===")

        print("\n1. Setting up Whisper model (Local)...")
        use_gpu = torch.cuda.is_available()
        device = "cuda" if use_gpu else "cpu"
        
        print(f"- Using device: {device}")
        
        model_id = "openai/whisper-large-v3"
        torch_dtype = torch.float16 if use_gpu else torch.float32

        model = AutoModelForSpeechSeq2Seq.from_pretrained(
            model_id,
            torch_dtype=torch_dtype,
            low_cpu_mem_usage=True,
            use_safetensors=True
        )
        
        if use_gpu:
            model = model.to(device)

        processor = AutoProcessor.from_pretrained(model_id)

        pipe = pipeline(
            "automatic-speech-recognition",
            model=model,
            tokenizer=processor.tokenizer,
            feature_extractor=processor.feature_extractor,
            max_new_tokens=128,
            chunk_length_s=30,
            batch_size=1,
            return_timestamps=True,
            torch_dtype=torch_dtype,
            device=device,
        )
        print("✓ Whisper model loaded successfully")
        
        return None, pipe
        
    except Exception as e:
        print(f"Error initializing models: {e}")
        raise e