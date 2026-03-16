import os
import gc
import shutil
import tempfile
import subprocess
from processors.video_processor import process_video

class VideoTranslatorPipeline:
    def __init__(self, device="cuda", whisper_pipe=None, gemma_pipe=None):
        self.device = device
        self.whisper_pipe = whisper_pipe
        self.gemma_pipe = gemma_pipe
        self.api_urls = {
            "mira": "http://44.192.41.163:7000/voice_clone",
            "qwen": "http://13.220.246.239:9000/voice_clone"
        }

    def process(self, video_path: str, model_name: str, duration: str = "full", update_status=None) -> str:
        api_url = self.api_urls.get(model_name)
        if not api_url:
            raise ValueError(f"Modelo {model_name} inválido. Use 'qwen' ou 'mira'.")

        # pastas temporárias isoladas para cada requisição da API
        temp_dir = tempfile.mkdtemp(prefix="video_temp_")
        output_dir = tempfile.mkdtemp(prefix="video_out_")
        
        try:
            print(f"Processando vídeo local: {video_path}")
            
            # cortar vídeo preservando a qualidade 
            work_video_path = video_path
            if str(duration).lower() != "full":
                try:
                    duration_secs = int(duration)
                    clipped_path = os.path.join(temp_dir, "clipped.mp4")
                    
                    if update_status:
                        update_status(2.0, f"Cortando vídeo para {duration_secs} segundos...")
                    print(f"Cortando vídeo para {duration_secs} segundos...")
                    
                    subprocess.run([
                        "ffmpeg",
                        "-y",
                        "-i", video_path,
                        "-t", str(duration_secs),
                        "-c", "copy",
                        clipped_path
                    ], check=True, capture_output=True)
                    work_video_path = clipped_path
                except ValueError:
                    print(f"Aviso: duration '{duration}' não é numérico, processando inteiro.")
                except subprocess.CalledProcessError as e:
                    print(f"Aviso: Erro ao cortar vídeo com ffmpeg, usando arquivo original.\nDetalhes: {e.stderr.decode('utf-8')}")
                except Exception as e:
                    print(f"Aviso: Erro inesperado ao cortar vídeo: {e}")

            if update_status:
                update_status(5.0, "Extraindo áudio...")

            output_video_path = process_video(
                video_path=work_video_path,
                temp_dir=temp_dir,
                api_url=api_url,
                output_dir=output_dir,
                model_name=model_name,
                update_status=update_status,
                whisper_pipe=self.whisper_pipe,
                gemma_pipe=self.gemma_pipe,
            )
            
            # salva o vídeo final em /tmp para não ser apagado na limpeza
            final_name = os.path.basename(output_video_path)
            final_safe_path = os.path.join("/tmp", final_name)
            shutil.copy(output_video_path, final_safe_path)
            
            return final_safe_path
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
            shutil.rmtree(output_dir, ignore_errors=True)
            gc.collect()