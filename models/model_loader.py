import os
import torch
import kagglehub
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor as SpeechProcessor, pipeline

def initialize_models(models_dir):
    try:
        print("\n=== Initializing Models ===")

        # --- 1. WHISPER (Para Transcrição) ---
        print("\n1. Setting up Whisper model (Transcription)...")
        use_gpu = torch.cuda.is_available()
        device = "cuda" if use_gpu else "cpu"
        
        print(f"- Using device: {device}")
        
        whisper_id = "openai/whisper-large-v3"
        torch_dtype = torch.bfloat16 if use_gpu else torch.float32

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
            max_new_tokens=128,
            chunk_length_s=30,
            batch_size=1,
            return_timestamps=True,
            torch_dtype=torch_dtype,
            device=device,
        )
        print("✓ Whisper loaded successfully")

        # TRANSLATEGEMMA (Tradução) 
        print("\n2. Setting up TranslateGemma model (Translation)...")
        print("- Downloading model from Kaggle (4B parameters)...")
        
        gemma_path = kagglehub.model_download("google/translategemma/transformers/translategemma-4b-it")
        
        gemma_pipe = pipeline(
            "image-text-to-text", # conforme documentação
            model=gemma_path,
            device=device,
            torch_dtype=torch_dtype
        )
        print("✓ TranslateGemma loaded successfully")
        
        return whisper_pipe, gemma_pipe
        
    except Exception as e:
        print(f"Error initializing models: {e}")
        raise e