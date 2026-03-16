document.addEventListener('DOMContentLoaded', () => {
    // Elementos da UI
    const dropzone = document.getElementById('dropzone');
    const videoFileInput = document.getElementById('video-file');
    const translateBtn = document.getElementById('translate-btn');
    const ttsModelSelect = document.getElementById('tts-model');
    
    // Elementos de Preview Local
    const previewContainer = document.getElementById('video-preview-container');
    const localPreviewVideo = document.getElementById('local-preview-video');
    const fileNameDisplay = document.getElementById('file-name-display');
    const removeFileBtn = document.getElementById('remove-file-btn');
    const uploadSection = document.querySelector('.upload-section');
    
    // Elementos de Status e Resultado
    const btnText = translateBtn.querySelector('.btn-text');
    const btnIcon = translateBtn.querySelector('.btn-icon');
    const loader = translateBtn.querySelector('.loader');
    const progressContainer = document.getElementById('progress-container');
    const progressText = document.getElementById('progress-text');
    const progressPercentage = document.getElementById('progress-percentage');
    const progressFill = document.getElementById('progress-fill');
    
    const resultContainer = document.getElementById('result-container');
    const outputVideo = document.getElementById('output-video');
    const downloadBtn = document.getElementById('download-btn');
    
    const errorToast = document.getElementById('error-toast');
    const errorMsg = document.getElementById('error-msg');

    let toastTimeout;
    let pollInterval = null;
    let selectedFile = null;

    // --- Lógica de UI e Validação ---

    function showError(message) {
        errorMsg.textContent = message;
        errorToast.classList.remove('hidden');
        clearTimeout(toastTimeout);
        toastTimeout = setTimeout(() => {
            errorToast.classList.add('hidden');
        }, 6000);
    }

    function handleFileSelection(file) {
        if (!file) return;
        
        // Verifica se é vídeo
        if (!file.type.startsWith('video/')) {
            showError("Formato inválido. Por favor, envie um arquivo de vídeo.");
            return;
        }

        selectedFile = file;
        fileNameDisplay.innerHTML = `<i class="ph ph-video"></i> ${file.name}`;
        
        // Gera preview local
        const fileURL = URL.createObjectURL(file);
        localPreviewVideo.src = fileURL;
        
        // Troca os painéis
        uploadSection.classList.add('hidden');
        previewContainer.classList.remove('hidden');
        translateBtn.disabled = false;
        
        // Esconde resultados anteriores se houver
        resultContainer.classList.add('hidden');
    }

    function clearFileSelection() {
        selectedFile = null;
        videoFileInput.value = '';
        localPreviewVideo.src = '';
        
        uploadSection.classList.remove('hidden');
        previewContainer.classList.add('hidden');
        translateBtn.disabled = true;
    }

    // --- Eventos de Drag & Drop ---
    
    // ---dropzone.addEventListener('click', () => videoFileInput.click());---
    
    dropzone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropzone.classList.add('dragover');
    });

    dropzone.addEventListener('dragleave', () => {
        dropzone.classList.remove('dragover');
    });

    dropzone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropzone.classList.remove('dragover');
        
        if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
            videoFileInput.files = e.dataTransfer.files; // Sincroniza o input real
            handleFileSelection(e.dataTransfer.files[0]);
        }
    });

    videoFileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFileSelection(e.target.files[0]);
        }
    });

    removeFileBtn.addEventListener('click', clearFileSelection);

    // --- Lógica de Progresso e Polling ---

    function setButtonLoading(isLoading) {
        if (isLoading) {
            translateBtn.disabled = true;
            btnText.style.display = 'none';
            if(btnIcon) btnIcon.style.display = 'none';
            loader.classList.remove('hidden');
        } else {
            translateBtn.disabled = false;
            btnText.style.display = 'inline';
            if(btnIcon) btnIcon.style.display = 'inline';
            loader.classList.add('hidden');
        }
    }

    function resetProgress() {
        progressContainer.classList.add('hidden');
        progressText.innerHTML = '<i class="ph ph-spinner-gap spin-icon"></i> Iniciando processamento...';
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
                        progressText.innerHTML = `<i class="ph ph-spinner-gap spin-icon"></i> ${data.text}`;
                        progressPercentage.textContent = `${progStr}%`;
                        progressFill.style.width = `${data.progress}%`;
                    } else if (data.progress === -1) {
                        // Erro reportado pelo backend
                        clearInterval(pollInterval);
                        progressText.innerHTML = `<i class="ph ph-warning-circle"></i> Falha no processamento!`;
                        progressFill.style.width = "100%";
                        progressFill.style.backgroundColor = "var(--error-color)";
                        showError(data.text);
                        setButtonLoading(false);
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

    // --- Submissão Principal ---

    translateBtn.addEventListener('click', async () => {
        if (!selectedFile) return;

        const ttsModel = ttsModelSelect.value;
        const apiHost = `http://${window.location.hostname}:7000`;
        const endpoint = `${apiHost}/predict`;

        setButtonLoading(true);
        resultContainer.classList.add('hidden');
        resetProgress();
        outputVideo.pause(); 
        outputVideo.removeAttribute('src');

        try {
            const formData = new FormData();
            formData.append("video", selectedFile);

            // 1. Faz upload do vídeo
            progressText.innerHTML = '<i class="ph ph-upload-simple spin-icon"></i> Enviando arquivo...';
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

            // 2. Chama a API de Tradução
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

            if (!downloadUrl) throw new Error('URL de vídeo não encontrada na resposta.');

            const finalVideoUrl = downloadUrl.startsWith('/') ? `${apiHost}${downloadUrl}` : downloadUrl;

            // Sucesso! Atualiza UI
            outputVideo.src = finalVideoUrl;
            outputVideo.load();
            downloadBtn.href = finalVideoUrl;
            
            resultContainer.classList.remove('hidden');
            progressFill.style.width = '100%';
            progressText.innerHTML = '<i class="ph ph-check-circle text-success"></i> Tradução finalizada!';
            
            setTimeout(() => {
                progressContainer.classList.add('hidden');
            }, 3000);

        } catch (error) {
            console.error(error);
            showError(error.message === 'Failed to fetch' 
                ? 'Erro de conexão. O servidor backend está rodando?' 
                : error.message);
            
            if (pollInterval) clearInterval(pollInterval);
            progressText.innerHTML = `<i class="ph ph-warning-circle"></i> Erro!`;
            progressFill.style.backgroundColor = "var(--error-color)";
        } finally {
            // Se não for erro de backend (-1), libera o botão
            if (progressFill.style.backgroundColor !== "var(--error-color)") {
                 setButtonLoading(false);
            }
        }
    });
});