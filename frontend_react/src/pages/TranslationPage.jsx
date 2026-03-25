import React, { useState } from 'react';
import api from '../services/api';
import { useAuth } from '../hooks/useAuth';
import VideoUploader from '../components/video/VideoUploader';
import VideoOptions from '../components/video/VideoOptions';
import VideoTrimmer from '../components/video/VideoTrimmer';
import ProgressViewer from '../components/video/ProgressViewer';
import ResultViewer from '../components/video/ResultViewer';
import Button from '../components/ui/Button';
import { MagicWand } from '@phosphor-icons/react';
import { getFriendlyErrorMessage } from '../utils/errors';
import { toast } from 'sonner';
import styles from './TranslationPage.module.css';

export default function TranslationPage() {
  const [file, setFile] = useState(null);
  const [ttsModel, setTtsModel] = useState('qwen');
  const [translationMode, setTranslationMode] = useState('full');
  const [trimRange, setTrimRange] = useState({ start: 0, end: 0 });
  
  // Pipeline state: 'idle', 'processing', 'completed', 'error'
  const [status, setStatus] = useState('idle');
  const [progress, setProgress] = useState(0);
  const [progressMsg, setProgressMsg] = useState('');
  const [resultUrl, setResultUrl] = useState(null);
  
  // Variables for cancellation
  const [activeJobId, setActiveJobId] = useState(null);
  const [uploadController, setUploadController] = useState(null);

  const handleFileSelect = (selectedFile) => {
    setFile(selectedFile);
    setStatus('idle');
    setResultUrl(null);
  };

  const handleClearFile = () => {
    setFile(null);
    setStatus('idle');
  };

  const handleTimeUpdate = (start, end) => {
    setTrimRange({ start, end });
  };

  const startTranslation = async () => {
    if (!file) return;
    setStatus('processing');
    setProgress(0);
    setProgressMsg('Iniciando envio do vídeo...');

    const pollInterval = setInterval(async () => {
      try {
        const response = await api.get(`/status/${jobId}`);
        const data = response.data;
        if (data.progress >= 0) {
          setProgress(data.progress);
          setProgressMsg(data.text);
        } else if (data.progress === -1) {
          clearInterval(pollInterval);
          throw new Error(data.error_message || data.text || 'Falha no processamento.');
        }
      } catch (err) {
        console.error('Erro no polling:', err);
      }
    }, 1500);

    try {
      // 1. Upload Video
      const formData = new FormData();
      formData.append('video', file);

      setProgressMsg('Enviando arquivo de vídeo...');
      const uploadRes = await api.post('/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress: (progressEvent) => {
          const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          if (percentCompleted < 100) {
            setProgressMsg(`Enviando: ${percentCompleted}%`);
          }
        }
      });

      const uploadData = uploadRes.data;
      const jobId = uploadData.job_id;
      setActiveJobId(jobId);
      toast.success('Upload completo. Processando...');

      // 2. Start Prediction Pipeline
      const payload = {
        video_path: uploadData.video_path,
        model: ttsModel,
        job_id: jobId,
        duration: 'full',
        start_time: '0'
      };

      if (translationMode === 'clip') {
        payload.start_time = String(trimRange.start);
        payload.duration = String(trimRange.end - trimRange.start);
      }

      const predictRes = await api.post('/predict', payload);
      const data = predictRes.data;
      const downloadUrl = data.download_url || (Array.isArray(data) && data.length > 0 ? data[0].download_url : null);
      
      if (!downloadUrl) throw new Error('URL de vídeo não encontrada na resposta.');

      const finalVideoUrl = downloadUrl.startsWith('/') ? `http://localhost:7000${downloadUrl}` : downloadUrl;

      // Finish successfully
      clearInterval(pollInterval);
      setProgress(100);
      setProgressMsg('Tradução finalizada com sucesso!');
      setResultUrl(finalVideoUrl);
      setStatus('completed');

    } catch (error) {
      console.error(error);
      if (pollInterval) clearInterval(pollInterval);
      
      const isCancel = error.message === 'canceled';
      
      let finalErrorMsg;
      if (isCancel) {
         finalErrorMsg = 'Upload cancelado pelo usuário.';
         toast.info(finalErrorMsg);
      } else {
         finalErrorMsg = getFriendlyErrorMessage(error.response?.data?.detail || error.message);
         toast.error(finalErrorMsg);
      }
      setProgressMsg(finalErrorMsg);
      setStatus('error');
    } finally {
      setActiveJobId(null);
    }
  };

  const handleCancelProcess = async () => {
    // Call backend backend cancel endpoint
    if (activeJobId) {
      try {
        await api.post(`/cancel/${activeJobId}`);
      } catch (e) {
        console.error('Erro ao cancelar:', e);
      }
    }
    // For axios, we would need an AbortController for the upload part specifically if we wanted to abort it.
    // Simplifying for now since the backend cancel handles the pipeline logic.
  };

  return (
    <div className={`container ${styles.pageContainer}`}>
      <div className={styles.header}>
        <h1 className={styles.title}>
          Traduza seus vídeos com <span className="gradient-text">Magia da IA</span>
        </h1>
        <p className={styles.subtitle}>
          Faça o upload do seu conteúdo e nós cuidamos da transcrição, tradução e dublagem automaticamente.
        </p>
      </div>

      <div className={styles.grid}>
        <div className={styles.mainColumn}>
          {status !== 'processing' && status !== 'completed' && (
            <VideoUploader 
              onFileSelect={handleFileSelect} 
              selectedFile={file} 
              onClear={handleClearFile} 
            />
          )}

          {file && status === 'idle' && (
            <div className="animate-fade-in" style={{ marginTop: '1.5rem' }}>
              <VideoTrimmer 
                videoFile={file} 
                onTimeUpdate={handleTimeUpdate} 
                isFullMode={translationMode === 'full'}
              />
            </div>
          )}

          {(status === 'processing' || status === 'error') && (
            <div className="animate-fade-in">
              <ProgressViewer 
                progress={status === 'error' ? 100 : progress} 
                status={progressMsg} 
                hasError={status === 'error'} 
                onCancel={status === 'processing' ? handleCancelProcess : null}
              />
              {status === 'error' && (
                <div style={{ marginTop: '1rem', display: 'flex', gap: '1rem', justifyContent: 'center' }}>
                  <button className="btn btn-primary" onClick={handleClearFile}>Tentar Novamente</button>
                </div>
              )}
            </div>
          )}

          {status === 'completed' && (
            <div className="animate-fade-in">
              <ResultViewer 
                videoUrl={resultUrl} 
                onDownload={() => {
                  const a = document.createElement('a');
                  a.href = resultUrl;
                  a.download = `translated_${file?.name || 'video.mp4'}`;
                  a.target = '_blank';
                  a.click();
                }} 
              />
            </div>
          )}
        </div>

        <div className={styles.sideColumn}>
          <VideoOptions 
            ttsModel={ttsModel} 
            setTtsModel={setTtsModel} 
            translationMode={translationMode} 
            setTranslationMode={setTranslationMode} 
          />

          <Button 
            variant={status === 'error' ? 'primary' : 'primary'} 
            size="large" 
            icon={<MagicWand size={24} weight="duotone" />}
            onClick={startTranslation}
            disabled={!file || status === 'processing' || status === 'completed'}
            className={styles.translateBtn}
          >
            {status === 'processing' ? 'Traduzindo...' : status === 'error' ? 'Tentar Novamente' : 'Iniciar Tradução'}
          </Button>

          {status === 'completed' && (
            <Button 
              variant="secondary" 
              size="large" 
              onClick={handleClearFile}
              className={styles.newTranslationBtn}
            >
              Traduzir Novo Vídeo
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}
