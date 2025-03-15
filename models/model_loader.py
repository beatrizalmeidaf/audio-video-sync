import os
import torch
from TTS.api import TTS
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline

def initialize_models(models_dir):
    try:
        print("\n=== Initializing Models ===")
        print("\n1. Setting up TTS model...")
        os.environ["TTS_HOME"] = models_dir
        use_gpu = torch.cuda.is_available()
        device = "cuda" if use_gpu else "cpu"
        
        print(f"- Using device: {device}")
        print("- Loading XTTS model (this may take a few minutes)...")
        
        tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2",
                  gpu=use_gpu,
                  progress_bar=True)
        print("✓ TTS model loaded successfully")

        print("\n2. Setting up Whisper model...")
        print("- Loading model configuration...")
        model_id = "openai/whisper-large-v3"
        torch_dtype = torch.float32

        model = AutoModelForSpeechSeq2Seq.from_pretrained(
            model_id,
            torch_dtype=torch_dtype,
            low_cpu_mem_usage=True,
            use_safetensors=True,
            trust_remote_code=True
        )
        
        if not use_gpu:
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
        
        print("\n=== All models initialized successfully! ===\n")
        return tts, pipe
    except Exception as e:
        print(f"\nDetailed error initializing models: {str(e)}")
        import traceback
        print("\nFull error traceback:")
        traceback.print_exc()
        raise Exception(f"Error initializing models: {e}")
