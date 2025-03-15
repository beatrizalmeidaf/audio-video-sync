import os
import torch
import torchaudio
from huggingface_hub import hf_hub_download, snapshot_download
from zonos.model import Zonos
from zonos.conditioning import make_cond_dict
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline

def initialize_models(models_dir):
    try:
        # Configurar diretório de cache
        cache_dir = os.path.join(models_dir, 'cache')
        os.environ['TRANSFORMERS_CACHE'] = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
        
        print("\n=== Inicializando Modelos ===")
        device = "cpu"  # Forçar CPU para consistência
        print(f"- Utilizando: {device}")
        
        # 1. Baixar modelo Zonos explicitamente primeiro
        print("\n1. Configurando modelo TTS (Zonos)...")
        print("- Baixando arquivos do modelo (pode demorar alguns minutos)...")
        
        # Criar um diretório local para o modelo
        zonos_dir = os.path.join(models_dir, "zonos_model")
        os.makedirs(zonos_dir, exist_ok=True)
        
        # Baixar o modelo com a função snapshot_download
        try:
            model_path = snapshot_download(
                repo_id="Zyphra/Zonos-v0.1-transformer",
                local_dir=zonos_dir,
                local_dir_use_symlinks=False,
                resume_download=True,
                max_workers=4
            )
            print(f"- Download completo em: {model_path}")

            # Vamos tentar uma abordagem diferente - verificar se os arquivos necessários estão presentes
            print("- Carregando modelo do diretório local...")
            # Verificar se os arquivos config.json e model.safetensors existem no diretório
            config_path = os.path.join(model_path, "config.json")
            model_file_path = os.path.join(model_path, "model.safetensors")
            
            if not os.path.exists(config_path) or not os.path.exists(model_file_path):
                # Se os arquivos não existirem, tente baixá-los diretamente
                print("- Arquivos do modelo não encontrados localmente. Baixando...")
                config_path = hf_hub_download(repo_id="Zyphra/Zonos-v0.1-transformer", filename="config.json")
                model_file_path = hf_hub_download(repo_id="Zyphra/Zonos-v0.1-transformer", filename="model.safetensors")
            
            # Carregar o modelo diretamente usando config_path e model_file_path
            model = Zonos.from_local(config_path, model_file_path, device=device)
            print("✓ Modelo Zonos TTS carregado com sucesso")
        except Exception as e:
            print(f"- Erro durante o download do Zonos: {str(e)}")
            raise
        
        def generate_speech(text, speaker_audio_path, language="pt-br"):
            print(f"- Gerando fala a partir do texto: {text[:30]}...")
            wav, sampling_rate = torchaudio.load(speaker_audio_path)
            speaker = model.make_speaker_embedding(wav, sampling_rate)
            cond_dict = make_cond_dict(text=text, speaker=speaker, language=language)
            conditioning = model.prepare_conditioning(cond_dict)
            
            print("  * Gerando códigos de áudio...")
            codes = model.generate(conditioning)
            
            print("  * Decodificando áudio...")
            wavs = model.autoencoder.decode(codes).cpu()
            print("  * Áudio gerado com sucesso!")
            return wavs[0], model.autoencoder.sampling_rate
        
        # 2. Configurar modelo Whisper
        print("\n2. Configurando modelo Whisper (versão menor)...")
        model_id = "openai/whisper-small"
        torch_dtype = torch.float32
        
        print("- Baixando modelo Whisper...")
        whisper_model = AutoModelForSpeechSeq2Seq.from_pretrained(
            model_id,
            torch_dtype=torch_dtype,
            low_cpu_mem_usage=True,
            use_safetensors=True,
            cache_dir=cache_dir
        )
        
        whisper_model = whisper_model.to(device)
        print("- Modelo Whisper carregado na memória")
        
        print("- Configurando processador...")
        processor = AutoProcessor.from_pretrained(model_id, cache_dir=cache_dir)
        
        print("- Criando pipeline de ASR...")
        pipe = pipeline(
            "automatic-speech-recognition",
            model=whisper_model,
            tokenizer=processor.tokenizer,
            feature_extractor=processor.feature_extractor,
            max_new_tokens=128,
            chunk_length_s=15,
            batch_size=1,
            return_timestamps=True,
            torch_dtype=torch_dtype,
            device=device,
        )
        print("✓ Modelo Whisper carregado com sucesso")
        
        print("\n=== Todos os modelos inicializados com sucesso! ===\n")
        return generate_speech, pipe
    
    except Exception as e:
        print(f"\nErro detalhado na inicialização dos modelos: {str(e)}")
        import traceback
        print("\nTraceback completo do erro:")
        traceback.print_exc()
        raise Exception(f"Erro na inicialização dos modelos: {e}")