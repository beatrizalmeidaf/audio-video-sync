import React, { useState, useEffect } from 'react';
import { toast } from 'sonner';
import { PlayCircle, DownloadSimple, Trash, WarningCircle, CheckCircle, Clock, VideoCameraSlash, Spinner, PencilSimple, Check, X } from '@phosphor-icons/react';
import Card from '../components/ui/Card';
import Button from '../components/ui/Button';
import api from '../services/api';
import styles from './HistoryPage.module.css';

export default function HistoryPage() {
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [playingJobId, setPlayingJobId] = useState(null);
  const [editingJobId, setEditingJobId] = useState(null);
  const [tempFilename, setTempFilename] = useState('');

  const fetchJobs = async () => {
    try {
      const response = await api.get('/history');
      setJobs(response.data);
    } catch (err) {
      console.error('Falha ao buscar histórico:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchJobs();
  }, []);

  // Polling if any job is processing
  useEffect(() => {
    const hasActiveJobs = jobs.some(j => j.status === 'processing' || j.status === 'uploading');
    if (!hasActiveJobs) return;

    const interval = setInterval(() => {
      fetchJobs();
    }, 2500);

    return () => clearInterval(interval);
  }, [jobs]);

  const handleDelete = async (jobId) => {
    if (!window.confirm('Tem certeza que deseja apagar este projeto do histórico?')) return;
    try {
      const res = await api.delete(`/history/${jobId}`);
      if (res.status === 200) {
        toast.success('Projeto removido.');
        setJobs(jobs.filter(j => j.job_id !== jobId));
      } else {
        toast.error('Erro ao remover projeto.');
      }
    } catch (err) {
      toast.error('Erro de conexão.');
    }
  };

  const handleRename = async (jobId) => {
    if (!tempFilename.trim()) {
      setEditingJobId(null);
      return;
    }
    
    try {
      const response = await api.patch(`/history/${jobId}`, { filename: tempFilename });
      if (response.status === 200) {
        toast.success('Nome atualizado com sucesso!');
        setJobs(jobs.map(j => j.job_id === jobId ? { ...j, filename: tempFilename } : j));
      } else {
        toast.error('Erro ao atualizar nome.');
      }
    } catch (err) {
      toast.error('Erro de conexão.');
    } finally {
      setEditingJobId(null);
    }
  };

  const startEditing = (job) => {
    setEditingJobId(job.job_id);
    setTempFilename(job.filename);
  };

  const getStatusLabel = (status) => {
    switch (status) {
      case 'completed': return { label: 'Concluído', icon: <CheckCircle weight="fill" /> };
      case 'processing': return { label: 'Processando', icon: <Spinner className="animate-spin" /> };
      case 'uploading': return { label: 'Enviando', icon: <Spinner className="animate-spin" /> };
      case 'error': return { label: 'Erro', icon: <WarningCircle weight="fill" /> };
      case 'cancelled': return { label: 'Cancelado', icon: <VideoCameraSlash weight="fill" /> };
      default: return { label: 'Desconhecido', icon: <Clock /> };
    }
  };

  if (loading) return (
    <div className="container" style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh', gap: '1rem', flexDirection: 'column' }}>
      <div className="animate-spin" style={{ width: '40px', height: '40px', border: '3px solid var(--border-light)', borderTop: '3px solid var(--primary)', borderRadius: '50%' }}></div>
      <p style={{ color: 'var(--text-secondary)' }}>Carregando histórico...</p>
    </div>
  );

  return (
    <div className={`container ${styles.pageContainer}`}>
      <div className={styles.header}>
        <h1 className={styles.title}>Histórico de Projetos</h1>
        <p className={styles.subtitle}>Acompanhe vídeos em tradução ou recupere traduções passadas.</p>
      </div>

      {jobs.length === 0 ? (
        <div className={styles.emptyState} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '1.5rem', padding: '4rem 0' }}>
          <VideoCameraSlash size={64} style={{ color: 'var(--text-tertiary)' }} />
          <div style={{ textAlign: 'center' }}>
            <h3 style={{ fontSize: '1.5rem', marginBottom: '0.5rem' }}>Nenhum vídeo no histórico</h3>
            <p style={{ color: 'var(--text-secondary)' }}>Você ainda não iniciou nenhuma tradução.</p>
          </div>
          <Button variant="primary" onClick={() => window.location.href = '/'}>Traduzir agora</Button>
        </div>
      ) : (
        <div className={styles.historyList}>
          {jobs.map((job) => {
            const { label, icon } = getStatusLabel(job.status);
            const dateStr = new Date(job.created_at).toLocaleString('pt-BR');
            const isActive = job.status === 'processing' || job.status === 'uploading';
            const isEditing = editingJobId === job.job_id;

            return (
              <Card key={job.job_id} variant="glass" className={styles.jobCard}>
                <div className={styles.cardHeader}>
                  <div className={styles.jobInfo} style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem', flex: 1 }}>
                    {isEditing ? (
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <input 
                          type="text" 
                          value={tempFilename}
                          onChange={(e) => setTempFilename(e.target.value)}
                          onKeyDown={(e) => e.key === 'Enter' && handleRename(job.job_id)}
                          autoFocus
                          style={{ 
                            background: 'var(--bg-main)', 
                            border: '1px solid var(--primary)', 
                            color: 'var(--text-primary)', 
                            padding: '0.25rem 0.5rem', 
                            borderRadius: '4px',
                            fontSize: '1rem',
                            outline: 'none',
                            width: '100%',
                            maxWidth: '300px'
                          }}
                        />
                        <button onClick={() => handleRename(job.job_id)} style={{ color: 'var(--success)' }}><Check size={20} /></button>
                        <button onClick={() => setEditingJobId(null)} style={{ color: 'var(--danger)' }}><X size={20} /></button>
                      </div>
                    ) : (
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <span className={styles.filename} style={{ fontSize: '1.1rem', fontWeight: '600' }}>{job.filename}</span>
                        <button 
                          onClick={() => startEditing(job)} 
                          style={{ color: 'var(--text-tertiary)', background: 'transparent', border: 'none', cursor: 'pointer', display: 'flex' }}
                          title="Renomear"
                        >
                          <PencilSimple size={14} />
                        </button>
                      </div>
                    )}
                    <span className={styles.date}>{dateStr}</span>
                  </div>
                  <div className={`${styles.statusBadge} ${styles[`status_${job.status}`]}`}>
                    {icon} {label}
                  </div>
                </div>

                {/* Progress / Status Reason */}
                {isActive && (
                  <div className={styles.progressArea}>
                    <div className={styles.progressHeader}>
                      <span>{job.text || 'Aguarde...'}</span>
                      <span>{Math.round(job.progress)}%</span>
                    </div>
                    <div className={styles.progressBarBg}>
                      <div className={styles.progressBarFill} style={{ width: `${Math.max(0, job.progress)}%` }} />
                    </div>
                  </div>
                )}
                {job.status === 'error' && (
                  <p className={styles.errorText}>{job.error_message || job.text}</p>
                )}

                {/* Actions */}
                <div className={styles.actions}>
                  {job.status === 'completed' && job.download_url && (
                    <>
                      <Button 
                        variant="primary" 
                        size="small" 
                        icon={<PlayCircle weight="fill" />} 
                        onClick={() => setPlayingJobId(playingJobId === job.job_id ? null : job.job_id)}
                      >
                        {playingJobId === job.job_id ? 'Fechar Vídeo' : 'Reproduzir'}
                      </Button>
                      <Button 
                        variant="secondary" 
                        size="small" 
                        icon={<DownloadSimple />}
                        onClick={() => window.open(job.download_url.startsWith('/') ? `http://localhost:7000${job.download_url}` : job.download_url, '_blank')}
                      >
                        Baixar
                      </Button>
                    </>
                  )}
                  <Button 
                    variant="glass" 
                    size="small" 
                    icon={<Trash />} 
                    onClick={() => handleDelete(job.job_id)}
                    style={{ marginLeft: 'auto', color: 'var(--text-tertiary)' }}
                  >
                    Excluir
                  </Button>
                </div>

                {/* Inline Player */}
                {playingJobId === job.job_id && job.download_url && (
                  <div className={`animate-fade-in ${styles.inlinePlayer}`}>
                    <video controls autoPlay src={job.download_url.startsWith('/') ? `http://localhost:7000${job.download_url}` : job.download_url} style={{ width: '100%', borderRadius: 'var(--radius-md)', marginTop: '1rem', border: '1px solid var(--border-strong)' }} />
                  </div>
                )}
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}
