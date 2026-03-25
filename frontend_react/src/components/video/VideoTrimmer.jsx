import React, { useRef, useState, useEffect } from 'react';
import Card from '../ui/Card';
import styles from './VideoTrimmer.module.css';

export default function VideoTrimmer({ videoFile, onTimeUpdate, isFullMode }) {
  const videoRef = useRef(null);
  const [duration, setDuration] = useState(0);
  const [startTime, setStartTime] = useState(0);
  const [endTime, setEndTime] = useState(10);
  const [isPlaying, setIsPlaying] = useState(false);

  useEffect(() => {
    if (videoFile) {
      const url = URL.createObjectURL(videoFile);
      if (videoRef.current) {
        videoRef.current.src = url;
      }
      return () => URL.revokeObjectURL(url);
    }
  }, [videoFile]);

  const handleLoadedMetadata = () => {
    if (videoRef.current) {
      const vidDuration = videoRef.current.duration;
      setDuration(vidDuration);
      setEndTime(vidDuration);
      onTimeUpdate(0, vidDuration);
    }
  };

  const handleTimeUpdate = () => {
    if (videoRef.current) {
      const current = videoRef.current.currentTime;
      if (current >= endTime) {
        videoRef.current.pause();
        setIsPlaying(false);
      }
    }
  };

  const formatTime = (seconds) => {
    const min = Math.floor(seconds / 60);
    const sec = Math.floor(seconds % 60);
    return `${min}:${sec.toString().padStart(2, '0')}`;
  };

  const handleStartChange = (e) => {
    const val = Number(e.target.value);
    if (val < endTime) {
      setStartTime(val);
      if (videoRef.current) videoRef.current.currentTime = val;
      onTimeUpdate(val, endTime);
    }
  };

  const handleEndChange = (e) => {
    const val = Number(e.target.value);
    if (val > startTime) {
      setEndTime(val);
      onTimeUpdate(startTime, val);
    }
  };

  if (!videoFile) return null;

  return (
    <Card variant="glass" className={styles.trimmerCard}>
      <div className={`${styles.videoWrapper} ${isFullMode ? styles.fullMode : ''}`}>
        <video 
          ref={videoRef}
          onLoadedMetadata={handleLoadedMetadata}
          onTimeUpdate={handleTimeUpdate}
          controls
          className={styles.video}
          playsInline
        />
      </div>

      {!isFullMode && (
        <div className={styles.controls}>
          <div className={styles.sliderContainer}>
            <div 
              className={styles.sliderTrack} 
              style={{ 
                left: `${(startTime / duration) * 100}%`,
                right: `${100 - (endTime / duration) * 100}%`
              }} 
            />
            <input 
              type="range" 
              min="0" 
              max={duration || 100} 
              value={startTime} 
              onChange={handleStartChange} 
              className={`${styles.slider} ${styles.leftSlider}`}
            />
            <input 
              type="range" 
              min="0" 
              max={duration || 100} 
              value={endTime} 
              onChange={handleEndChange} 
              className={`${styles.slider} ${styles.rightSlider}`}
            />
          </div>

          <div className={styles.timeInfo}>
            <div className={styles.timeBlock}>
              <span className={styles.timeLabel}>Início</span>
              <span className={styles.timeValue}>{formatTime(startTime)}</span>
            </div>
            <div className={styles.timeBlock}>
              <span className={styles.timeLabel}>Fim</span>
              <span className={styles.timeValue}>{formatTime(endTime)}</span>
            </div>
            <div className={styles.timeBlock}>
              <span className={styles.timeLabel}>Duração</span>
              <span className={styles.timeValue}>{formatTime(endTime - startTime)}</span>
            </div>
          </div>
        </div>
      )}
    </Card>
  );
}
