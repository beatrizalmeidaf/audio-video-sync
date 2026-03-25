import os
import uuid
import logging
import boto3
import shutil
import tempfile
import multiprocessing
import litserve as ls
from datetime import timedelta
from fastapi import Request, UploadFile, HTTPException, Header
from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Optional

from video_pipeline import VideoTranslatorPipeline
from models.model_loader import load_whisper, load_gemma
from db import init_db, create_job, update_job_status, get_job, get_all_jobs, delete_job, create_user, get_user_by_email, get_user_by_id
from utils.auth import verify_password, get_password_hash, create_access_token, decode_token

# Initialize SQLite database
init_db()

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
            start_time = str(request.get("start_time", "0"))
            job_id = request.get("job_id", "default")

            if not video_path:
                raise ValueError("Nenhum 'video_path' fornecido no JSON.")
            
            if model not in ["qwen", "mira"]:
                raise ValueError("O modelo deve ser 'qwen' ou 'mira'.")

            payload_dict = {
                "video_path": str(video_path), 
                "model": model, 
                "duration": duration, 
                "start_time": start_time,
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
            start_time = inputs["start_time"]
            temp_dir = inputs["temp_dir"]
            job_id = inputs.get("job_id", "default")

            logger.info(f"Iniciando tradução. Arquivo: {video_path} | Modelo: {model} | Duração: {duration} | Início: {start_time}")
            
            cancel_flag_path = f"/tmp/jobs/{job_id}_cancel.flag"

            def update_status(progress: float, text: str):
                if os.path.exists(cancel_flag_path):
                    raise Exception("JOB_CANCELLED")
                
                try:
                    status_value = "processing"
                    update_job_status(job_id, progress, text, status=status_value)
                except Exception as ex:
                    logger.error(f"Erro ao salvar status no BD: {ex}")
                    
            update_status(0.0, "Iniciando processamento...")
            
            final_video_path = self.pipeline.process(video_path, model, duration, update_status, start_time, job_id=job_id)
            
            update_status(95.0, "Fazendo upload do vídeo final...")
            download_url = self._upload_video(final_video_path)
            
            update_job_status(job_id, 100.0, "Concluído!", status="completed", download_url=download_url)
            return {"download_url": download_url}
        except Exception as e:
            logger.exception(f"Erro no processamento: {e}")
            if "job_id" in inputs:
                job_id = inputs["job_id"]
                if str(e) == "JOB_CANCELLED":
                    update_job_status(job_id, -1.0, "Cancelado pelo usuário.", status="cancelled")
                else:
                    update_job_status(job_id, -1.0, f"Erro: {str(e)}", status="error", error_message=str(e))
            raise HTTPException(status_code=500, detail=str(e))
        finally:
            temp_dir = inputs.get("temp_dir")
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)

# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------

class RegisterRequest(BaseModel):
    name: Optional[str] = None
    email: str
    password: str

class LoginRequest(BaseModel):
    email: str
    password: str

def get_current_user(authorization: Optional[str] = Header(None)):
    """FastAPI dependency — extracts and validates the JWT Bearer token."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token não fornecido.")
    token = authorization.split(" ", 1)[1]
    payload = decode_token(token)
    if payload is None:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado.")
    user = get_user_by_id(payload.get("sub"))
    if not user:
        raise HTTPException(status_code=401, detail="Usuário não encontrado.")
    return user

if __name__ == "__main__":
    from fastapi.middleware.cors import CORSMiddleware
    
    # API LitServe 
    api = VideoTranslatorAPI()
    server = ls.LitServer(
        lit_api=api,
        max_batch_size=1, # processamento de vídeo é pesado, fazemos um por vez
        timeout=1800.0,   # 30 minutos de limite 
        accelerator="cuda",
        workers_per_device=1,
    )

    # Middleware para proteger TODAS as rotas, incluindo /predict do LitServe
    from fastapi.responses import JSONResponse
    from fastapi import Request
    
    @server.app.middleware("http")
    async def auth_middleware(request: Request, call_next):
        # Rotas públicas que não precisam de token
        public_routes = [
            "/auth/login", 
            "/auth/register", 
            "/", 
            "/login", 
            "/register", 
            "/how-to-use"
        ]
        
        # Se for uma rota pública ou for um arquivo estático (css, js, imagens) ou for o próprio servidor estático do front
        if request.url.path in public_routes or request.url.path.startswith(("/assets/", "/static/")):
            return await call_next(request)
            
        # Para as demais, verificamos o token
        authorization = request.headers.get("Authorization")
        if not authorization or not authorization.startswith("Bearer "):
            # Se for uma tentativa de acessar o front (que não seja assets), permite (o react lida com proteção de rotas)
            # Mas se for API (predict, upload, history, me), exige token
            if request.url.path.startswith(("/auth/", "/predict", "/upload", "/history", "/status", "/cancel")):
                return JSONResponse(status_code=401, content={"detail": "Token não fornecido."})
            return await call_next(request)
            
        token = authorization.split(" ", 1)[1]
        payload = decode_token(token)
        if payload is None:
             return JSONResponse(status_code=401, content={"detail": "Token inválido ou expirado."})
             
        # Opcional: injetar o user id no state para uso posterior
        request.state.user_id = payload.get("sub")
        
        return await call_next(request)

    # --- Auth Endpoints ---

    @server.app.post("/auth/register", status_code=201)
    async def register(body: RegisterRequest):
        if len(body.password) < 6:
            raise HTTPException(status_code=400, detail="A senha deve ter pelo menos 6 caracteres.")
        hashed = get_password_hash(body.password)
        user_id = create_user(body.name, body.email, hashed)
        if user_id is None:
            raise HTTPException(status_code=409, detail="Este email já está cadastrado.")
        return {"message": "Conta criada com sucesso!", "user_id": user_id}

    @server.app.post("/auth/login")
    async def login(body: LoginRequest):
        user = get_user_by_email(body.email)
        if not user or not verify_password(body.password, user["password_hash"]):
            raise HTTPException(status_code=401, detail="Email ou senha inválidos.")
        token = create_access_token({"sub": user["id"]})
        return {
            "access_token": token,
            "token_type": "bearer",
            "user": {"id": user["id"], "name": user["name"], "email": user["email"]}
        }

    @server.app.get("/auth/me")
    async def me(authorization: Optional[str] = Header(None)):
        return get_current_user(authorization)

    # --- Protected routes ---

    @server.app.post("/upload")
    async def upload_video(video: UploadFile, authorization: Optional[str] = Header(None)):
        current_user = get_current_user(authorization)
        temp_dir = tempfile.mkdtemp(prefix="upload_temp_")
        video_path = os.path.join(temp_dir, video.filename or "video.mp4")
        with open(video_path, "wb") as f:
            shutil.copyfileobj(video.file, f)
            
        job_id = uuid.uuid4().hex
        
        create_job(job_id, current_user["id"], video.filename)
        update_job_status(job_id, 0.0, "Upload concluído. Aguardando processamento...", status="processing")
        
        return {"video_path": video_path, "job_id": job_id}
        
    @server.app.get("/status/{job_id}")
    async def get_status(job_id: str, authorization: Optional[str] = Header(None)):
        current_user = get_current_user(authorization)
        job = get_job(job_id, current_user["id"])
        if not job:
            raise HTTPException(status_code=404, detail="Job não encontrado.")
        return job

    @server.app.post("/cancel/{job_id}")
    async def cancel_job(job_id: str, authorization: Optional[str] = Header(None)):
        current_user = get_current_user(authorization)
        job = get_job(job_id, current_user["id"])
        if not job:
            raise HTTPException(status_code=404, detail="Job não encontrado.")
        os.makedirs("/tmp/jobs", exist_ok=True)
        flag_path = f"/tmp/jobs/{job_id}_cancel.flag"
        with open(flag_path, "w") as f:
            f.write("cancelled")
        update_job_status(job_id, -1.0, "Tradução cancelada pelo usuário.", status="cancelled")
        return {"status": "cancelled", "job_id": job_id}

    @server.app.get("/history")
    async def list_history(authorization: Optional[str] = Header(None)):
        current_user = get_current_user(authorization)
        return get_all_jobs(current_user["id"])
        
    @server.app.delete("/history/{job_id}")
    async def delete_history_job(job_id: str, authorization: Optional[str] = Header(None)):
        current_user = get_current_user(authorization)
        delete_job(job_id, current_user["id"])
        return {"status": "deleted"}

    @server.app.patch("/history/{job_id}")
    async def rename_history_job(job_id: str, body: dict, authorization: Optional[str] = Header(None)):
        current_user = get_current_user(authorization)
        new_filename = body.get("filename")
        if not new_filename:
            raise HTTPException(status_code=400, detail="Filename não fornecido.")
        
        # O db.py já filtra por job_id e user_id
        from db import update_job_filename
        update_job_filename(job_id, current_user["id"], new_filename)
        return {"status": "updated", "filename": new_filename}

    # servindo os vídeos locais quando AWS não está configurado
    from fastapi.staticfiles import StaticFiles
    import os
    os.makedirs("/tmp", exist_ok=True)
    server.app.mount("/outputs", StaticFiles(directory="/tmp"), name="outputs")

    # Servir o build do React como fallback
    frontend_path = os.path.join(os.path.dirname(__file__), "frontend_react", "dist")
    if os.path.exists(frontend_path):
        server.app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")
    else:
        logger.warning(f"Frontend dist não encontrado em {frontend_path}. Compile o react para acessar na porta 7000.")

    # configurando o CORS
    server.app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"], # em produção substituir por ["http://localhost:8080", ...]
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    server.run(port=7000)