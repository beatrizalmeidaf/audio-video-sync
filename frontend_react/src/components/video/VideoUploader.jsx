import React, { useRef, useState } from 'react';
import styles from './VideoUploader.module.css';
import { UploadSimple, FileVideo, X, FileMinus } from '@phosphor-icons/react';

export default function VideoUploader({ onFileSelect, selectedFile, onClear }) {
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef(null);

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const file = e.dataTransfer.files[0];
      if (file.type.startsWith('video/')) {
        onFileSelect(file);
      }
    }
  };

  const handleChange = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      const file = e.target.files[0];
      onFileSelect(file);
    }
  };

  if (selectedFile) {
    return (
      <div className={`${styles.uploader} ${styles.hasFile}`}>
        <div className={styles.fileInfo}>
          <FileVideo size={32} weight="duotone" className={styles.fileIcon} />
          <div className={styles.fileDetails}>
            <span className={styles.fileName}>{selectedFile.name}</span>
            <span className={styles.fileSize}>{(selectedFile.size / (1024 * 1024)).toFixed(2)} MB</span>
          </div>
          <button onClick={onClear} className={styles.clearBtn} title="Remover vídeo">
            <X size={20} />
          </button>
        </div>
      </div>
    );
  }

  return (
    <div 
      className={`${styles.uploader} ${isDragging ? styles.dragging : ''}`}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      onClick={() => fileInputRef.current?.click()}
    >
      <input 
        type="file" 
        ref={fileInputRef} 
        onChange={handleChange} 
        accept="video/mp4,video/x-m4v,video/*" 
        style={{ display: 'none' }} 
      />
      <div className={styles.uploadContent}>
        <div className={styles.iconCircle}>
          <UploadSimple size={32} color="var(--primary)" />
        </div>
        <p className={styles.mainText}>
          Arraste um vídeo ou <strong>clique para buscar</strong>
        </p>
        <p className={styles.subText}>
          Suporta MP4, MOV, M4V (Máx: 500MB)
        </p>
      </div>
    </div>
  );
}
