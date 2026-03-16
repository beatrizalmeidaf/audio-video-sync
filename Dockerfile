FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

ENV HF_HOME=/app/hf_cache

RUN apt-get update && apt-get install -y \
    ffmpeg \
    rubberband-cli \
    libsndfile1 \
    git \
    build-essential \
    nodejs \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir "numpy<2.0" 
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# ENTRYPOINT ["python", "main.py"]
# expõe a porta 7000 
EXPOSE 7000
ENTRYPOINT ["python", "app.py"]