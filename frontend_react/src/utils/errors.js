export function getFriendlyErrorMessage(errorMsg) {
  if (!errorMsg || typeof errorMsg !== 'string') return 'Erro desconhecido ao processar vídeo.';
  
  const lowerMsg = errorMsg.toLowerCase();
  
  if (lowerMsg.includes('out of memory')) {
    return 'Servidor sobrecarregado (Falta de Memória). Por favor, aguarde e tente novamente.';
  }
  if (lowerMsg.includes('job_cancelled')) {
    return 'A tradução foi cancelada pelo usuário.';
  }
  if (lowerMsg.includes('ffmpeg')) {
    return 'Formato de vídeo não suportado ou arquivo corrompido.';
  }
  if (lowerMsg.includes('failed to fetch')) {
    return 'Erro de conexão: Servidor indisponível.';
  }
  if (lowerMsg.includes('nenhum')) {
    return 'Selecione um arquivo válido para enviar.';
  }
  
  // Default fallback if it's a backend generic exception
  return `Erro no servidor: ${errorMsg}`;
}
