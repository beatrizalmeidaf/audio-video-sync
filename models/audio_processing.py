import torch
import torchaudio
import numpy as np
import soundfile as sf
import librosa
import pyrubberband as pyrb

def read_audio(path):
    """
    Lê um arquivo de áudio do caminho fornecido e converte para mono, se necessário.

    Args:
        path (str): Caminho do arquivo de áudio.

    Returns:
        tuple: Um tupla contendo o waveform como tensor e a taxa de amostragem (sample rate).

    Raises:
        Exception: Se o arquivo de áudio não puder ser lido.
    """
    try:
        wav, sr = torchaudio.load(path)
        if wav.size(0) > 1:
            wav = wav.mean(dim=0, keepdim=True)
        return wav.squeeze(0), sr
    except Exception as e:
        raise Exception(f"Error reading audio file: {e}")


def resample_wav(wav, sr, new_sr):
    """
    Ressampleia o áudio para uma nova taxa de amostragem.

    Args:
        wav (Tensor): O waveform do áudio original.
        sr (int): Taxa de amostragem original.
        new_sr (int): Nova taxa de amostragem desejada.

    Returns:
        Tensor: O waveform ressampleado.

    Raises:
        Exception: Se ocorrer um erro durante o ressampling.
    """
    try:
        wav = wav.unsqueeze(0)
        transform = torchaudio.transforms.Resample(orig_freq=sr, new_freq=new_sr)
        wav = transform(wav)
        return wav.squeeze(0)
    except Exception as e:
        raise Exception(f"Error resampling audio: {e}")


def map_timestamps_to_new_sr(vad_sr, new_sr, timestamps, just_begging_end=False):
    """
    Mapeia os timestamps para uma nova taxa de amostragem.

    Args:
        vad_sr (int): Taxa de amostragem original dos timestamps.
        new_sr (int): Nova taxa de amostragem.
        timestamps (list): Lista de dicionários com os timestamps originais.
        just_begging_end (bool): Se True, retorna apenas o início e o fim.

    Returns:
        list: Lista de timestamps ajustados para a nova taxa de amostragem.

    Raises:
        Exception: Se ocorrer um erro durante o mapeamento.
    """
    try:
        factor = new_sr / vad_sr
        new_timestamps = []
        if just_begging_end and timestamps:
            new_dict = {"start": int(timestamps[0]["start"] * factor), "end": int(timestamps[-1]["end"] * factor)}
            new_timestamps.append(new_dict)
        else:
            for ts in timestamps:
                new_dict = {"start": int(ts["start"] * factor), "end": int(ts["end"] * factor)}
                new_timestamps.append(new_dict)
        return new_timestamps
    except Exception as e:
        raise Exception(f"Error mapping timestamps: {e}")


def get_vad_model_and_utils(use_cuda=False):
    """
    Carrega o modelo de detecção de voz (VAD) e suas funções utilitárias.

    Args:
        use_cuda (bool): Se True, utiliza GPU, caso disponível.

    Returns:
        tuple: Modelo VAD e funções utilitárias (get_speech_timestamps, save_audio, collect_chunks).

    Raises:
        Exception: Se ocorrer um erro ao carregar o modelo.
    """
    try:
        model, utils = torch.hub.load(repo_or_dir="snakers4/silero-vad", model="silero_vad", onnx=False)
        if use_cuda and torch.cuda.is_available():
            model = model.cuda()
        get_speech_timestamps, save_audio, _, _, collect_chunks = utils
        return model, get_speech_timestamps, save_audio, collect_chunks
    except Exception as e:
        raise Exception(f"Error loading VAD model: {e}")


def adjust_speed(audio, sr, target_duration, min_rate=0.8, max_rate=1.5):
    """
    Ajusta a velocidade do áudio para atingir uma duração alvo.

    Args:
        audio (ndarray): Áudio como array numpy.
        sr (int): Taxa de amostragem do áudio.
        target_duration (float): Duração alvo desejada.
        min_rate (float): Taxa mínima de ajuste.
        max_rate (float): Taxa máxima de ajuste.

    Returns:
        ndarray: Áudio ajustado.

    """
    current_duration = len(audio) / sr
    rate = current_duration / target_duration
    rate = np.clip(rate * 1.01, min_rate, max_rate)
    adjusted_audio = pyrb.time_stretch(audio, sr, rate)
    return adjusted_audio


def calculate_tts_speed(current_duration, target_duration):
    """
    Calcula a taxa de ajuste necessária para alinhar a duração do áudio atual com a duração alvo.

    Args:
        current_duration (float): Duração atual do áudio.
        target_duration (float): Duração alvo desejada.

    Returns:
        float: Fator de ajuste dentro de limites aceitáveis (0.8 a 1.2).
    """
    error_margin = (current_duration - target_duration) / target_duration
    adjustment_factor = 1 - error_margin
    return np.clip(adjustment_factor, 0.8, 1.2)