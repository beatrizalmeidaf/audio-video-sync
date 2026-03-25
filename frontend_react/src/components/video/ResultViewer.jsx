import React from 'react';
import Card from '../ui/Card';
import Button from '../ui/Button';
import { DownloadSimple, PlayCircle, CheckCircle } from '@phosphor-icons/react';
import styles from './ResultViewer.module.css';

export default function ResultViewer({ videoUrl, onDownload }) {
  if (!videoUrl) return null;

  return (
    <Card variant="glass" className={`${styles.resultCard} animate-fade-in`}>
      <div className={styles.header}>
        <CheckCircle size={32} weight="fill" className={styles.successIcon} />
        <div>
          <h2 className={styles.title}>Tradução Concluída!</h2>
          <p className={styles.subtitle}>Seu vídeo está pronto. Assista à prévia ou faça o download.</p>
        </div>
      </div>

      <div className={styles.videoWrapper}>
        <video 
          src={videoUrl} 
          controls 
          playsInline
          className={styles.video}
          poster=""
        />
        {!videoUrl && (
          <div className={styles.placeholder}>
            <PlayCircle size={48} weight="duotone" className={styles.placeholderIcon} />
          </div>
        )}
      </div>

      <div className={styles.actions}>
        <Button 
          variant="primary" 
          size="large" 
          icon={<DownloadSimple size={24} />}
          onClick={onDownload}
          className={styles.downloadBtn}
        >
          Baixar Vídeo Traduzido
        </Button>
      </div>
    </Card>
  );
}
