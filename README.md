# AI Video Translator & Voice Cloner Pipeline

Esse projeto é um pipeline automatizado para tradução de vídeos (Português → Inglês) preservando a voz original do locutor (Voice Cloning).

O sistema integra o poder do **OpenAI Whisper** (local) para transcrição e tradução com APIs externas da Ermis de **Clonagem de Voz** (Mira/Qwen), utilizando algoritmos de processamento de sinal (Time Stretching) para sincronizar o áudio gerado com o vídeo original.

## Funcionalidades

* **CLI Robusta:** Interface de linha de comando para fácil automação.
* **Entrada Flexível:** Aceita arquivos de vídeo locais (`.mp4`, `.avi`, etc.) ou URLs do YouTube.
* **Docker Ready:** Ambiente containerizado que já inclui todas as dependências complexas (FFmpeg, Rubberband).
* **Transcrição & Tradução:** Utiliza `Whisper Large v3` localmente para máxima precisão.
* **Segmentação Inteligente:** Usa `Silero VAD` para detectar fala e ignorar silêncios.
* **Clonagem de Voz (API):** Suporte nativo para modelos **Mira** (Porta 7000) e **Qwen** (Porta 9000).
* **Sincronia Temporal:** Ajusta a velocidade do áudio gerado para bater com a duração da fala original (Lip-sync approximation).
* **Cache Persistente:** Otimizado para não baixar modelos repetidamente ao usar Docker.


## Como Usar (Docker)

### 1. Construir a Imagem

```bash
docker build -t video-translator .

```

### 2. Executar

Deve passar a URL/Arquivo e o Modelo (`mira` ou `qwen`) via linha de comando.

**No Linux / WSL:**

```bash
# exemplo com URL do YouTube e modelo Qwen
docker run -it --rm -v $(pwd):/app video-translator --model qwen --url "https://youtu.be/SEU_VIDEO_AQUI"

# exemplo com arquivo local e modelo Mira (o arquivo input.mp4 deve estar na pasta atual)
docker run -it --rm -v $(pwd):/app video-translator --model mira --url "input.mp4"

```

**No Windows (Command Prompt / CMD):**

```cmd
docker run -it --rm -v %cd%:/app video-translator --model qwen --url "https://youtu.be/SEU_VIDEO_AQUI"

```

> **Nota:** Os vídeos traduzidos serão salvos automaticamente na pasta `videos/` com o nome do modelo utilizado (ex: `translated_QWEN_video.mp4`).


## Instalação Manual (Sem Docker)

Se preferir rodar localmente fora do Docker, precisará configurar o ambiente manualmente.

### Pré-requisitos de Sistema

1. **Python 3.9**
2. **FFmpeg:** Essencial para extração e montagem.
3. **Rubberband CLI:** Obrigatório para o ajuste de tempo (Time Stretching).
* *Windows:* Baixe o executável e adicione ao PATH do sistema.
* *Linux:* `sudo apt-get install rubberband-cli`


### Passo a Passo

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


3. **Instale as dependências:**
```bash
pip install -r requirements.txt

```


4. **Execute via CLI:**
```bash
python main.py --model qwen --url "https://youtu.be/..."

```

## Argumentos da CLI

O script `main.py` aceita os seguintes argumentos:

| Argumento | Obrigatório | Opções | Descrição |
| --- | --- | --- | --- |
| `--url` | Sim | URL ou Caminho | Link do YouTube ou caminho para arquivo local `.mp4`. |
| `--model` | Sim | `mira`, `qwen` | Escolhe qual API de clonagem usar. |

**Detalhes dos Modelos:**

* **`--model mira`**: Conecta na porta `7000`. Envia áudio como referência.
* **`--model qwen`**: Conecta na porta `9000`. Envia arquivo + parâmetro de velocidade.
