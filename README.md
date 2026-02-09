# AI Video Translator & Voice Cloner Pipeline

Esse projeto é um pipeline automatizado para tradução de vídeos (Português → Inglês) preservando a voz original do locutor (Voice Cloning).

O sistema integra o poder do OpenAI Whisper (local) para transcrição e tradução com APIs externas de Clonagem de Voz (Mira/Qwen), utilizando algoritmos de processamento de sinal (Time Stretching) para sincronizar o áudio gerado com o vídeo original.

## Funcionalidades

* **Entrada Flexível:** Aceita arquivos de vídeo locais (`.mp4`, `.avi`, etc.) ou URLs do YouTube.
* **Transcrição & Tradução:** Utiliza `Whisper Large v3` localmente para máxima precisão.
* **Segmentação Inteligente:** Usa `Silero VAD` para detectar fala e ignorar silêncios, garantindo cortes precisos.
* **Clonagem de Voz (API):** Integração com APIs externas de TTS (Text-to-Speech) generative (portas 7000/9000).
* **Sincronia Temporal:** Ajusta a velocidade do áudio gerado (`pyrubberband`) para bater com a duração da fala original (Lip-sync approximation).
* **Montagem Automática:** Recompila o vídeo final com o novo áudio usando FFmpeg.

## Pré-requisitos

Precisa ter as seguintes dependências de sistema instaladas:

1. **Python 3.9**
2. **FFmpeg:** Essencial para extração e montagem de áudio/vídeo.
* Ubuntu: `sudo apt install ffmpeg`
* Windows: Baixe e adicione ao PATH.
3. **Rubberband CLI:** Necessário para o pacote `pyrubberband`.
* Ubuntu: `sudo apt install rubberband-cli`
* Windows: Necessário baixar o executável do Rubberband.

## Instalação

1. **Clone o repositório:**
```bash
git clone https://github.com/beatrizalmeidaf/audio-video-sync
cd audio-video-sync
```


2. **Crie um ambiente virtual:**
```bash
conda create -n sync python=3.9 -y
conda activate sync
```


3. **Instale as dependências Python:**
```bash
pip install -r requirements.txt

```

## Configuração da API

O projeto suporta dois tipos de endpoints para a clonagem de voz.:

```python
API_URL = "http://44.192.41.163:7000/voice_clone" 
# OU
API_URL = "http://44.192.41.163:9000/voice_clone"

```

O sistema detecta automaticamente a porta e ajusta o payload:

* **Porta 9000 (Qwen):** Envia campo `file` e aceita parâmetro `speed`.
* **Porta 7000 (Mira):** Envia campo `audio` e não utiliza `speed` na requisição.

## Como Usar

Execute o arquivo principal:

```bash
python main.py

```

O terminal irá solicitar:

1. **Caminho do vídeo ou URL:**
* Ex: `videos/palestra.mp4`
* Ex: `https://www.youtube.com/watch?v=...`


**O processo seguirá as etapas:**

1. Download (se for YouTube) e extração do áudio.
2. Carregamento dos modelos (Whisper e VAD).
3. Segmentação e Transcrição.
4. Envio para API de Clonagem.
5. Pós-processamento (Ajuste de velocidade e volume).
6. Geração do vídeo final na pasta `videos/`.
