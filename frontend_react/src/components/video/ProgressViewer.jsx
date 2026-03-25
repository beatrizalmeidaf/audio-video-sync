import React from 'react';
import Card from '../ui/Card';
import { CircleNotch, CheckCircle, WarningCircle, XCircle } from '@phosphor-icons/react';
import styles from './ProgressViewer.module.css';

export default function ProgressViewer({ progress, status, hasError = false, onCancel }) {
  const isComplete = progress >= 100 && !hasError;

  return (
    <Card variant="glass" className={`${styles.progressCard} ${hasError ? styles.errorCard : ''}`}>
      <div className={styles.header}>
        {hasError ? (
          <WarningCircle size={28} className={styles.errorIcon} />
        ) : isComplete ? (
          <CheckCircle size={28} weight="fill" className={styles.successIcon} />
        ) : (
          <CircleNotch size={28} className={styles.spinIcon} />
        )}
        <div className={styles.statusInfo}>
          <h3 className={`${styles.title} ${hasError ? styles.errorTitle : ''}`}>
            {hasError ? 'Falha na Tradução' : isComplete ? 'Processamento Concluído' : 'Processando Vídeo'}
          </h3>
          <p className={`${styles.statusText} ${hasError ? styles.errorTitle : ''}`}>{status || 'Aguarde um momento...'}</p>
        </div>
        {!hasError && <span className={styles.percentage}>{Math.round(progress)}%</span>}
        {onCancel && !isComplete && !hasError && (
          <button onClick={onCancel} className={styles.cancelBtn} title="Cancelar processamento">
            <XCircle size={28} weight="duotone" />
          </button>
        )}
      </div>

      <div className={styles.progressBarBg}>
        <div 
          className={`${styles.progressBarFill} ${isComplete ? styles.complete : ''} ${hasError ? styles.errorFill : ''}`} 
          style={{ width: `${hasError ? 100 : progress}%` }} 
        />
      </div>
    </Card>
  );
}
