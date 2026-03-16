document.addEventListener('DOMContentLoaded', () => {
    const videoFileInput = document.getElementById('video-file');
    const ttsModelSelect = document.getElementById('tts-model');
    const translateBtn = document.getElementById('translate-btn');
    const btnText = translateBtn.querySelector('.btn-text');
    const loader = translateBtn.querySelector('.loader');
    
    const resultContainer = document.getElementById('result-container');
    const outputVideo = document.getElementById('output-video');
    const downloadBtn = document.getElementById('download-btn');
    
    const errorToast = document.getElementById('error-toast');
    const errorMsg = document.getElementById('error-msg');

    let toastTimeout;

    function showError(message) {
        errorMsg.textContent = message;
        errorToast.classList.remove('hidden');
        
        clearTimeout(toastTimeout);
        toastTimeout = setTimeout(() => {
            errorToast.classList.add('hidden');
        }, 5000);
    }

    function setButtonLoading(isLoading) {
        if (isLoading) {
            translateBtn.disabled = true;
            btnText.style.display = 'none';
            loader.style.display = 'inline-block';
        } else {
            translateBtn.disabled = false;
            btnText.style.display = 'inline';
            loader.style.display = 'none';
        }
    }

    const progressContainer = document.getElementById('progress-container');
    const progressText = document.getElementById('progress-text');
    const progressPercentage = document.getElementById('progress-percentage');
    const progressFill = document.getElementById('progress-fill');

    let pollInterval = null;

    function resetProgress() {
        progressContainer.classList.add('hidden');
        progressText.textContent = 'Iniciando processamento...';
        progressPercentage.textContent = '0%';
        progressFill.style.width = '0%';
        
        progressFill.style.backgroundColor = ''; 
        
        if (pollInterval) {
            clearInterval(pollInterval);
            pollInterval = null;
        }
    }

    function startPolling(apiHost, jobId) {
        progressContainer.classList.remove('hidden');
        
        pollInterval = setInterval(async () => {
            try {
                const res = await fetch(`${apiHost}/status/${jobId}`);
                if (res.ok) {
                    const data = await res.json();
                    
                    if (data.progress >= 0) {
                        const progStr = data.progress.toFixed(0);
                        progressText.textContent = data.text;
                        progressPercentage.textContent = `${progStr}%`;
                        progressFill.style.width = `${data.progress}%`;
                    } else if (data.progress === -1) {
                        // Erro reportado pelo backend
                        clearInterval(pollInterval);
                        progressText.textContent = "Falha no processamento!";
                        progressFill.style.width = "100%"; // Preenche a barra toda para indicar parada
                        progressFill.style.backgroundColor = "var(--error-color)";
                        
                        showError(data.text);
                    }

                    if (data.progress >= 100) {
                        clearInterval(pollInterval);
                    }
                }
            } catch (error) {
                console.log("Erro ao checar status:", error);
            }
        }, 1500);
    }

    translateBtn.addEventListener('click', async () => {
        const file = videoFileInput.files[0];
        const ttsModel = ttsModelSelect.value;
        const apiHost = `http://${window.location.hostname}:7000`;
        const endpoint = `${apiHost}/predict`;

        if (!file) {
            showError("Por favor, selecione um arquivo de vídeo.");
            return;
        }

        setButtonLoading(true);
        resultContainer.classList.add('hidden');
        resetProgress();

        // Pausa se algum vídeo anterior estivesse tocando
        outputVideo.pause(); 
        outputVideo.removeAttribute('src');

        try {
            const formData = new FormData();
            formData.append("video", file);

            // 1. Faz upload do vídeo
            progressText.textContent = 'Enviando arquivo...';
            progressContainer.classList.remove('hidden');
            
            const uploadResponse = await fetch(`${apiHost}/upload`, {
                method: 'POST',
                body: formData
            });

            if (!uploadResponse.ok) {
                const errorData = await uploadResponse.json().catch(() => null);
                throw new Error(errorData?.detail || `Erro no upload: ${uploadResponse.status}`);
            }

            const uploadData = await uploadResponse.json();
            const jobId = uploadData.job_id;

            // Iniciar o polling
            startPolling(apiHost, jobId);

            // 2. Chama a tradução enviando o caminho do vídeo local
            const predictPayload = {
                video_path: uploadData.video_path,
                model: ttsModel,
                duration: "full",
                job_id: jobId
            };

            const response = await fetch(endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                body: JSON.stringify(predictPayload)
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => null);
                throw new Error(errorData?.detail || `Erro do servidor: ${response.status}`);
            }

            const data = await response.json();

            const downloadUrl = data.download_url || (Array.isArray(data) && data.length > 0 ? data[0].download_url : null);

            if (!downloadUrl) {
                throw new Error('URL de vídeo não encontrada na resposta da API.');
            }

            const finalVideoUrl = downloadUrl.startsWith('/') ? `${apiHost}${downloadUrl}` : downloadUrl;

            // Exibe o vídeo e o botão de download
            outputVideo.src = finalVideoUrl;
            outputVideo.load();
            
            downloadBtn.href = finalVideoUrl;
            downloadBtn.style.display = 'block';

            resultContainer.classList.remove('hidden');
            
            // Auto play se desejar
            outputVideo.play().catch(e => console.log('Autoplay prevent or ignored', e));

            progressFill.style.width = '100%';
            progressText.textContent = 'Pronto!';
            setTimeout(() => {
                progressContainer.classList.add('hidden');
            }, 3000);

        } catch (error) {
            console.error(error);
            showError(error.message === 'Failed to fetch' 
                ? 'Erro de conexão. O servidor AWS está rodando ou permite CORS?' 
                : error.message);
            
            if (pollInterval) clearInterval(pollInterval);
            progressText.textContent = "Erro!";
            progressFill.style.backgroundColor = "var(--error-color)";
        } finally {
            setButtonLoading(false);
        }
    });
});

