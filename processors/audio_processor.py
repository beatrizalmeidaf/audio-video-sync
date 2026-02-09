import os
import torch
import numpy as np
import soundfile as sf
import librosa
import warnings
from utils.api_client import generate_voice_clone
warnings.filterwarnings('ignore')

class AudioVADSlicer:
    """
    Classe responsável por dividir arquivos de áudio com base em timestamps de voz detectados pelo modelo VAD.
    
    """
    def __init__(self, device, min_sec=1, max_sec=10, threshold=0.9, rms_threshold=0.01, out_dir=None, vad_sample_rate=8000):
        from models.audio_processing import get_vad_model_and_utils
        
        self.use_cuda = device == "cuda" and torch.cuda.is_available()
        self.model_and_utils = get_vad_model_and_utils(use_cuda=self.use_cuda)
        self.vad_sample_rate = vad_sample_rate
        self.out_dir = out_dir
        self.min_sec = min_sec
        self.max_sec = max_sec
        self.threshold = threshold
        self.rms_threshold = rms_threshold

    def calculate_rms(self, audio_data):
        return torch.sqrt(torch.mean(torch.tensor(audio_data) ** 2))

    def get_new_speech_timestamps(self, audio_path, trim_just_beginning_and_end=False):
        from models.audio_processing import read_audio, resample_wav, map_timestamps_to_new_sr
        
        try:
            model, get_speech_timestamps, _, collect_chunks = self.model_and_utils
            orig_wav, orig_sample_rate = read_audio(audio_path)

            if orig_sample_rate != self.vad_sample_rate:
                wav = resample_wav(orig_wav, orig_sample_rate, self.vad_sample_rate)
            else:
                wav = orig_wav

            if self.use_cuda:
                wav = wav.cuda()

            speech_timestamps = get_speech_timestamps(
                wav, model, sampling_rate=self.vad_sample_rate,
                window_size_samples=768, threshold=self.threshold
            )

            new_speech_timestamps = map_timestamps_to_new_sr(
                self.vad_sample_rate, orig_sample_rate,
                speech_timestamps, trim_just_beginning_and_end
            )

            return orig_wav, orig_sample_rate, new_speech_timestamps
        except Exception as e:
            raise Exception(f"Error getting speech timestamps: {e}")

    def __call__(self, audio_path, out_dir=None):
        try:
            if not out_dir and self.out_dir:
                out_dir = self.out_dir

            orig_wav, orig_sample_rate, new_timestamps = self.get_new_speech_timestamps(audio_path)
            orig_wav = orig_wav.cpu().numpy()

            segments = []
            for tp in new_timestamps:
                s = tp["start"]
                e = tp["end"]
                duration = (e-s)/orig_sample_rate
                
                segment_audio = orig_wav[s:e]
                rms = self.calculate_rms(segment_audio)
                
                if duration > self.max_sec:
                    print(f"Skipping segment {s//orig_sample_rate}:{e//orig_sample_rate}s (too long)")
                    continue
                elif duration < self.min_sec and rms < self.rms_threshold:
                    print(f"Skipping silent short segment {s//orig_sample_rate}:{e//orig_sample_rate}s (duration={duration:.2f}s, RMS={rms:.6f})")
                    continue
                else:
                    print(f"Keeping segment {s//orig_sample_rate}:{e//orig_sample_rate}s (duration={duration:.2f}s, RMS={rms:.6f})")

                if out_dir:
                    prefix = os.path.splitext(os.path.basename(audio_path))[0]
                    segment_dir = os.path.join(out_dir, prefix)
                    os.makedirs(segment_dir, exist_ok=True)
                    out_path = os.path.join(segment_dir, f"{prefix}_{s}_{e}.wav")
                    sf.write(out_path, segment_audio, orig_sample_rate, subtype="PCM_16")
                    print(f"Saved segment: {out_path}")

                segments.append({
                    "audio": segment_audio,
                    "sample_rate": orig_sample_rate,
                    "start": s,
                    "end": e,
                })
            return segments
        except Exception as e:
            raise Exception(f"Error processing audio segments: {e}")

def process_segment_audio(api_url, segment, temp_dir, sample_rate, audio_converted, audio_original, full_ref_path):
    """
    Processa um segmento de áudio: envia para a API, recebe o áudio sintetizado, ajusta duração e volume, e mescla no áudio final.
    """
    import pyrubberband as pyrb
    
    start_sample = int(segment["start"])
    end_sample = int(segment["end"])
    target_duration = segment["duration"]
    
    print(f"   -> Sending to API ({api_url})...")
    
    audio_content = generate_voice_clone(
        text=segment["translation"],
        ref_audio_path=full_ref_path, 
        api_url=api_url,
        speed=1.0 
    )

    if audio_content and len(audio_content) > 1000: 
        temp_path = os.path.join(temp_dir, f"temp_api_{start_sample}.wav")
        with open(temp_path, 'wb') as f:
            f.write(audio_content)

        try:
            best_audio, _ = librosa.load(temp_path, sr=sample_rate)

            # ajuste de Velocidade (Time-Stretching)
            current_duration = len(best_audio) / sample_rate
            
            if current_duration > 0:
                final_speed_adjustment = current_duration / target_duration
                
                # tolerância maior: só ajusta se diferença for > 15%
                if abs(current_duration - target_duration) > 0.15:
                    final_speed_adjustment = np.clip(final_speed_adjustment, 0.6, 1.8) # limites seguros
                    best_audio = pyrb.time_stretch(best_audio, sample_rate, final_speed_adjustment)

            # ajuste de tamanho (corte ou padding)
            target_len = end_sample - start_sample
            if len(best_audio) > target_len:
                best_audio = best_audio[:target_len]
            elif len(best_audio) < target_len:
                best_audio = np.pad(best_audio, (0, target_len - len(best_audio)))

            # normalização de volume 
            segment_original = audio_original[start_sample:end_sample]
            rms_orig = np.sqrt(np.mean(segment_original**2))
            rms_new = np.sqrt(np.mean(best_audio**2))
            
            if rms_new > 0.001: # evita explodir áudio mudo
                best_audio = best_audio * (rms_orig / rms_new)

            # crossfade
            fade_len = int(0.01 * sample_rate)
            if len(best_audio) > 2*fade_len:
                best_audio[:fade_len] *= np.linspace(0, 1, fade_len)
                best_audio[-fade_len:] *= np.linspace(1, 0, fade_len)

            audio_converted[start_sample:start_sample+len(best_audio)] = best_audio
            print("   -> Success (Audio merged)")
            
        except Exception as e:
            print(f"   -> Error processing downloaded audio: {e}")
            audio_converted[start_sample:end_sample] = audio_original[start_sample:end_sample]
            
        if os.path.exists(temp_path): os.remove(temp_path)
    else:
        print("   -> API returned empty/invalid data. Fallback to original.")
        audio_converted[start_sample:end_sample] = audio_original[start_sample:end_sample]