import React from 'react';
import Card from '../components/ui/Card';
import { UploadSimple, Scissors, Translate, DownloadSimple } from '@phosphor-icons/react';

export default function HowToUsePage() {
  const steps = [
    {
      title: '1. Faça o Upload',
      description: 'Envie seu vídeo diretamente do seu computador. Suportamos formatos MP4, MOV e M4V.',
      icon: <UploadSimple size={32} weight="duotone" color="var(--primary)" />
    },
    {
      title: '2. Corte o Vídeo (Opcional)',
      description: 'Deseja traduzir apenas uma parte? Use nossa ferramenta visual para selecionar exatamente o trecho que importa.',
      icon: <Scissors size={32} weight="duotone" color="var(--primary)" />
    },
    {
      title: '3. Traduza com IA',
      description: 'Escolha o melhor modelo (Qwen ou Mira) e nossa Inteligência Artificial fará a transcrição, tradução e dublagem.',
      icon: <Translate size={32} weight="duotone" color="var(--primary)" />
    },
    {
      title: '4. Baixe o Resultado',
      description: 'Em poucos minutos, o seu vídeo estará pronto! Basta fazer o download do resultado final com a nova dublagem.',
      icon: <DownloadSimple size={32} weight="duotone" color="var(--primary)" />
    }
  ];

  return (
    <div className="container animate-fade-in" style={{ padding: '3rem 0', maxWidth: '800px' }}>
      <div style={{ textAlign: 'center', marginBottom: '3rem' }}>
        <h1 style={{ fontSize: '2.5rem', marginBottom: '1rem' }}>Como Funciona o <span className="gradient-text">Ermis</span></h1>
        <p style={{ color: 'var(--text-secondary)', fontSize: '1.1rem' }}>Siga o passo a passo simples para traduzir e dublar seus vídeos de forma profissional.</p>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
        {steps.map((step, idx) => (
          <Card key={idx} variant="glass" style={{ display: 'flex', alignItems: 'flex-start', gap: '1.5rem', padding: '2rem' }}>
            <div style={{ 
              background: 'var(--primary-light)', 
              padding: '1rem', 
              borderRadius: 'var(--radius-lg)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              border: '1px solid rgba(99, 102, 241, 0.2)'
            }}>
              {step.icon}
            </div>
            <div>
              <h3 style={{ fontSize: '1.25rem', marginBottom: '0.5rem', color: 'var(--text-primary)' }}>{step.title}</h3>
              <p style={{ color: 'var(--text-secondary)', lineHeight: '1.6' }}>{step.description}</p>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}
