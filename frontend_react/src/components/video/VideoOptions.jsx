import React from 'react';
import Card from '../ui/Card';
import { Cpu, Scissors, VideoCamera } from '@phosphor-icons/react';
import styles from './VideoOptions.module.css';

export default function VideoOptions({ 
  ttsModel, 
  setTtsModel, 
  translationMode, 
  setTranslationMode 
}) {
  return (
    <Card variant="glass" className={styles.optionsCard}>
      <h3 className={styles.title}>Configurações de Tradução</h3>
      
      <div className={styles.section}>
        <label className={styles.label}>
          <Cpu size={18} /> Modelo de Voz (TTS)
        </label>
        <div className={styles.selectWrapper}>
          <select 
            value={ttsModel} 
            onChange={(e) => setTtsModel(e.target.value)}
            className={styles.select}
          >
            <option value="qwen">Qwen</option>
            <option value="mira">Mira</option>
          </select>
        </div>
      </div>

      <div className={styles.section}>
        <label className={styles.label}>Modo de Tradução</label>
        <div className={styles.radioGroup}>
          <label className={`${styles.radioCard} ${translationMode === 'full' ? styles.active : ''}`}>
            <input 
              type="radio" 
              name="mode" 
              value="full"
              checked={translationMode === 'full'}
              onChange={() => setTranslationMode('full')}
              className={styles.hiddenRadio}
            />
            <VideoCamera size={24} weight={translationMode === 'full' ? 'duotone' : 'regular'} />
            <div className={styles.radioText}>
              <span className={styles.radioTitle}>Vídeo Completo</span>
              <span className={styles.radioDesc}>Traduz do início ao fim</span>
            </div>
          </label>

          <label className={`${styles.radioCard} ${translationMode === 'clip' ? styles.active : ''}`}>
            <input 
              type="radio" 
              name="mode" 
              value="clip"
              checked={translationMode === 'clip'}
              onChange={() => setTranslationMode('clip')}
              className={styles.hiddenRadio}
            />
            <Scissors size={24} weight={translationMode === 'clip' ? 'duotone' : 'regular'} />
            <div className={styles.radioText}>
              <span className={styles.radioTitle}>Cortar Trecho</span>
              <span className={styles.radioDesc}>Selecione uma parte específica</span>
            </div>
          </label>
        </div>
      </div>
    </Card>
  );
}
