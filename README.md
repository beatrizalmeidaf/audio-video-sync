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

## Interface Web & API (Docker Compose)

A maneira mais fácil de rodar o projeto com interface gráfica e API é utilizando o **Docker Compose**.

### Como Rodar

1. **Subir os serviços**:
   ```bash
   docker compose up -d
   ```

2. **Acessar a Interface**:
   Abra o seu navegador em [http://localhost:8081](http://localhost:8081).

3. **API Local**:
   A API estará disponível em [http://localhost:7000](http://localhost:7000).

4. **Verificar Logs**:
   ```bash
   docker compose logs -f api
   ```

5. **Reiniciar Serviços**:
   ```bash
   docker compose down && docker compose up -d
   ```


**Detalhes dos Modelos:**

* **`--model mira`**: Conecta na porta `7000`. Envia áudio como referência.
* **`--model qwen`**: Conecta na porta `9000`. Envia arquivo + parâmetro de velocidade.
