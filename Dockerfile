FROM python:3.9-bookworm

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    rubberband-cli \
    libsndfile1 \
    git \
    build-essential \
    gcc \
    g++ \
    libffi-dev \
    libsndfile1-dev \
    libblas-dev \
    liblapack-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .


RUN pip install --upgrade pip \
    && pip install -r requirements.txt


COPY . .

CMD ["python", "main.py"]
