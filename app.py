import os
import uuid
import logging
import boto3
import shutil
import tempfile
import multiprocessing
import litserve as ls
from fastapi import Request, UploadFile, HTTPException
from pydantic import BaseModel, Field, ConfigDict, field_validator

from video_pipeline import VideoTranslatorPipeline
from models.model_loader import load_whisper, load_gemma

# logging 
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=getattr(logging, log_level, logging.INFO), force=True)
logger = logging.getLogger("VideoTranslator_API")


class VideoOutput(BaseModel):
    download_url: str = Field(..., description="URL para baixar o vídeo traduzido")

# API LitServe 
class VideoTranslatorAPI(ls.LitAPI):
    def setup(self, device: str) -> None:
        logger.info("Iniciando setup da API de Tradução de Vídeo")
        
        logger.info("Carregando Whisper (transcrição)...")
        self.whisper_pipe = load_whisper()
        logger.info("Whisper carregado com sucesso.")
        
        logger.info("Carregando Gemma (tradução)...")
        self.gemma_pipe = load_gemma()
        logger.info("Gemma carregado com sucesso.")
        
        self.pipeline = VideoTranslatorPipeline(
            device=device,
            whisper_pipe=self.whisper_pipe,
            gemma_pipe=self.gemma_pipe,
        )
        
        self.bucket = os.getenv("S3_BUCKET_OUTPUTS")
        if self.bucket:
            self.s3 = boto3.client("s3")
            logger.info(f"S3 configurado. Bucket: {self.bucket}")
        else:
            logger.warning("S3_BUCKET_OUTPUTS não configurado. Salvando apenas localmente.")

    def decode_request(self, request: dict) -> dict:
        try:
            video_path = request.get("video_path")
            model = request.get("model", "qwen")
            duration = str(request.get("duration", "full"))
            job_id = request.get("job_id", "default")

            if not video_path:
                raise ValueError("Nenhum 'video_path' fornecido no JSON.")
            
            if model not in ["qwen", "mira"]:
                raise ValueError("O modelo deve ser 'qwen' ou 'mira'.")

            payload_dict = {
                "video_path": str(video_path), 
                "model": model, 
                "duration": duration, 
                "temp_dir": os.path.dirname(video_path),
                "job_id": job_id
            }
            logger.info(f"Decoded payload: {payload_dict}")
            return payload_dict
        except Exception as e:
            logger.exception(f"Erro no decode_request: {e}")
            raise HTTPException(status_code=400, detail=str(e))

    def encode_response(self, output: dict) -> VideoOutput:
        return VideoOutput(**output)

    def _upload_video(self, video_path: str) -> str:
        if not self.bucket:
            filename = os.path.basename(video_path)
            return f"/outputs/{filename}"

        uid = uuid.uuid4().hex
        key = f"outputs/translated_{uid}.mp4"
        
        logger.info(f"Fazendo upload para S3: {key}")
        with open(video_path, "rb") as f:
            self.s3.upload_fileobj(f, self.bucket, key, ExtraArgs={"ContentType": "video/mp4"})

        url = self.s3.generate_presigned_url(
            ClientMethod="get_object",
            Params={"Bucket": self.bucket, "Key": key},
            ExpiresIn=3600 
        )
        os.remove(video_path) # apaga do servidor após o upload
        return url

    def predict(self, inputs: dict) -> dict:
        try:
            video_path = inputs["video_path"]
            model = inputs["model"]
            duration = inputs["duration"]
            temp_dir = inputs["temp_dir"]
            job_id = inputs.get("job_id", "default")

            logger.info(f"Iniciando tradução. Arquivo: {video_path} | Modelo: {model} | Duração: {duration}")
            
            def update_status(progress: float, text: str):
                os.makedirs("/tmp/jobs", exist_ok=True)
                try:
                    import json
                    with open(f"/tmp/jobs/{job_id}.json", "w") as f:
                        json.dump({"progress": progress, "text": text}, f)
                except Exception as ex:
                    logger.error(f"Erro ao salvar status: {ex}")
                    
            update_status(0.0, "Iniciando processamento...")
            
            final_video_path = self.pipeline.process(video_path, model, duration, update_status)
            
            update_status(95.0, "Fazendo upload do vídeo final...")
            download_url = self._upload_video(final_video_path)
            
            update_status(100.0, "Concluído!")
            return {"download_url": download_url}
        except Exception as e:
            logger.exception(f"Erro no processamento: {e}")
            if "job_id" in inputs:
                job_id = inputs["job_id"]
                os.makedirs("/tmp/jobs", exist_ok=True)
                import json
                with open(f"/tmp/jobs/{job_id}.json", "w") as f:
                    json.dump({"progress": -1.0, "text": f"Erro: {str(e)}"}, f)
            raise HTTPException(status_code=500, detail=str(e))
        finally:
            temp_dir = inputs.get("temp_dir")
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)

if __name__ == "__main__":
    from fastapi.middleware.cors import CORSMiddleware
    
    api = VideoTranslatorAPI()
    server = ls.LitServer(
        lit_api=api,
        max_batch_size=1, # processamento de vídeo é pesado, fazemos um por vez
        timeout=1800.0,   # 30 minutos de limite 
        accelerator="cuda",
        workers_per_device=1,
    )

    # Rota personalizada para salvar upload antes de passar ao LitServe

    @server.app.post("/upload")
    async def upload_video(video: UploadFile):
        temp_dir = tempfile.mkdtemp(prefix="upload_temp_")
        video_path = os.path.join(temp_dir, video.filename or "video.mp4")
        with open(video_path, "wb") as f:
            shutil.copyfileobj(video.file, f)
            
        job_id = uuid.uuid4().hex
        
        os.makedirs("/tmp/jobs", exist_ok=True)
        import json
        with open(f"/tmp/jobs/{job_id}.json", "w") as f:
            json.dump({"progress": 0.0, "text": "Upload concluído. Aguardando processamento..."}, f)
        
        return {"video_path": video_path, "job_id": job_id}
        
    @server.app.get("/status/{job_id}")
    async def get_status(job_id: str):
        import json
        try:
            with open(f"/tmp/jobs/{job_id}.json", "r") as f:
                return json.load(f)
        except FileNotFoundError:
            return {"progress": 0.0, "text": "Aguardando..."}

    # servindo os vídeos locais quando AWS não está configurado
    from fastapi.staticfiles import StaticFiles
    import os
    os.makedirs("/tmp", exist_ok=True)
    server.app.mount("/outputs", StaticFiles(directory="/tmp"), name="outputs")

    # configurando o CORS
    server.app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"], # em produção substituir por ["http://localhost:8080", ...]
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    server.run(port=7000)