import os
import torch
import numpy as np
import soundfile as sf
import librosa
import warnings
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

def process_segment_audio(tts, segment, temp_dir, sample_rate, audio_converted, audio_original):
    from models.audio_processing import calculate_tts_speed
    import pyrubberband as pyrb
    
    start_sample = int(segment["start"])
    end_sample = int(segment["end"])
    target_duration = segment["duration"]

    ref_audio_path = os.path.join(temp_dir, f"ref_audio_{start_sample}.wav")
    segment_audio_np = segment["audio"].numpy().squeeze()
    sf.write(ref_audio_path, segment_audio_np, 24000)

    max_attempts = 3
    best_audio = None
    best_duration_diff = float('inf')
    best_speed = 1.0

    for attempt in range(max_attempts):
        if attempt == 0:
            speed = 1.0
        else:
            speed = calculate_tts_speed(len(best_audio) / sample_rate, target_duration)

        temp_path = os.path.join(temp_dir, f"temp_translated_{start_sample}_{attempt}.wav")
        tts.tts_to_file(
            text=segment["translation"],
            file_path=temp_path,
            speaker_wav=ref_audio_path,
            language="en",
            speed=speed
        )

        temp_audio, _ = librosa.load(temp_path, sr=sample_rate)
        current_duration = len(temp_audio) / sample_rate
        duration_diff = abs(current_duration - target_duration)

        if duration_diff < best_duration_diff:
            best_audio = temp_audio
            best_duration_diff = duration_diff
            best_speed = speed

        os.remove(temp_path)

        if duration_diff < 0.05:
            break

    print(f"Final speed: {best_speed:.2f}, Duration diff: {best_duration_diff:.3f}s")

    if best_audio is not None:
        final_speed = len(best_audio) / sample_rate / target_duration
        if abs(len(best_audio) / sample_rate - target_duration) > 0.05:
            best_audio = pyrb.time_stretch(best_audio, sample_rate, final_speed)

        if len(best_audio) > (end_sample - start_sample):
            best_audio = best_audio[:(end_sample - start_sample)]
        elif len(best_audio) < (end_sample - start_sample):
            padding = np.zeros((end_sample - start_sample) - len(best_audio))
            best_audio = np.concatenate([best_audio, padding])

        rms_original = np.sqrt(np.mean(segment_audio_np**2))
        rms_translated = np.sqrt(np.mean(best_audio**2)) if len(best_audio) > 0 else 1
        if rms_translated > 0:
            volume_factor = rms_original / rms_translated
            best_audio = best_audio * volume_factor

        fade_samples = int(0.02 * sample_rate)
        fade_in = np.linspace(0, 1, fade_samples)
        fade_out = np.linspace(1, 0, fade_samples)
        best_audio[:fade_samples] *= fade_in
        best_audio[-fade_samples:] *= fade_out

        audio_converted[start_sample:start_sample + len(best_audio)] = best_audio
    else:
        audio_converted[start_sample:end_sample] = audio_original[start_sample:end_sample]

    if os.path.exists(ref_audio_path):
        os.remove(ref_audio_path)