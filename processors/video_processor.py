import os
import gc
import torch
import torchaudio
import numpy as np
import soundfile as sf
import warnings
warnings.filterwarnings("ignore") 

from .audio_processor import AudioVADSlicer, process_segment_audio
from models.model_loader import load_whisper, load_gemma

def process_video(video_path, temp_dir, api_url, output_dir, model_name="model", update_status=None, whisper_pipe=None, gemma_pipe=None):
    def safe_update(prog, txt):
        if update_status:
            update_status(prog, txt)

    try:
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")

        print("Extracting audio from video...")
        audio_path = os.path.join(temp_dir, "audio_original.wav")
        ffmpeg_cmd = f'ffmpeg -y -i "{video_path}" -map 0:a -acodec pcm_s16le -ar 16000 -ac 1 "{audio_path}"'
        if os.system(ffmpeg_cmd) != 0:
            raise Exception("Failed to extract audio from video")

        print("Initializing VAD slicer...")
        slicer = AudioVADSlicer(device='cpu', min_sec=1.5, max_sec=20, threshold=0.75, rms_threshold=0.008)

        print("Processing audio segments...")
        segments = slicer(audio_path)
        audio_segments = []

        waveform, sample_rate = torchaudio.load(audio_path)
        audio_original = waveform[0].numpy()
        audio_converted = np.zeros_like(audio_original)

        for segment in segments:
            s, e = segment["start"], segment["end"]
            segment_audio = torch.from_numpy(segment["audio"]).float().unsqueeze(0)
            if segment["sample_rate"] != 24000:
                segment_audio = torchaudio.functional.resample(segment_audio, segment["sample_rate"], 24000)

            segment_path = os.path.join(temp_dir, f"segment_{s}_{e}.wav")
            torchaudio.save(segment_path, segment_audio, 24000)

            audio_segments.append({
                "audio": segment_audio, "audio_path": segment_path, 
                "transcription": None, "translation": None, 
                "start": s, "end": e, "duration": (e - s) / sample_rate
            })

        # TRANSCRIÇÃO 
        print("\n=== TRANSCRIPTION (WHISPER) ===")
        _own_whisper = whisper_pipe is None
        if _own_whisper:
            safe_update(10.0, "Carregando modelo de transcrição...")
            whisper_pipe = load_whisper()
        else:
            safe_update(10.0, "Transcrevendo áudio...")
        
        for i, segment in enumerate(audio_segments, 1):
            try:
                prog = 10.0 + (30.0 * (i / len(audio_segments))) # 10 a 40%
                safe_update(prog, f"Transcrevendo segmento {i}/{len(audio_segments)}")
                
                print(f"Segment {i}/{len(audio_segments)} [Transcribing]")
                transcription = whisper_pipe(segment["audio_path"], generate_kwargs={"task": "transcribe", "language": "portuguese"})["text"]
                segment["transcription"] = transcription
                print(f"   -> PT: {transcription[:70]}...")
            except Exception as e:
                print(f"Error in transcription {i}: {e}")
                
        if _own_whisper:
            print("\n[Memory Manager] Unloading Whisper to free RAM...")
            del whisper_pipe
            gc.collect()

        # TRADUÇÃO 
        print("\n=== TRANSLATION (GEMMA) ===")
        _own_gemma = gemma_pipe is None
        if _own_gemma:
            safe_update(40.0, "Carregando modelo de tradução...")
            gemma_pipe = load_gemma()
        else:
            safe_update(40.0, "Traduzindo segmentos...")
        
        for i, segment in enumerate(audio_segments, 1):
            try:
                prog = 40.0 + (30.0 * (i / len(audio_segments))) # 40 a 70%
                safe_update(prog, f"Traduzindo segmento {i}/{len(audio_segments)}")
                
                if not segment.get("transcription"):
                    continue
                print(f"Segment {i}/{len(audio_segments)} [Translating]")
                
                messages = [{"role": "user", "content": [{"type": "text", "source_lang_code": "pt", "target_lang_code": "en", "text": segment["transcription"]}]}]
                
                gemma_output = gemma_pipe(text=messages, max_new_tokens=200)
                translation = gemma_output[0]["generated_text"][-1]["content"]
                segment["translation"] = translation
                print(f"   -> EN: {translation[:70]}...")
            except Exception as e:
                print(f"Error in translation {i}: {e}")

        if _own_gemma:
            print("\n[Memory Manager] Unloading Gemma to free RAM...")
            del gemma_pipe
            gc.collect()

        # CLONAGEM DE VOZ E VÍDEO 
        print("\n=== VOICE CLONING & ASSEMBLE ===")
        for i, segment in enumerate(audio_segments, 1):
            prog = 70.0 + (23.0 * (i / len(audio_segments))) # 70 a 93%
            safe_update(prog, f"Clonando voz: segmento {i}/{len(audio_segments)}")
            
            print(f"Synthesizing segment {i}/{len(audio_segments)}")
            if not segment["translation"]: continue
            
            process_segment_audio(
                api_url, 
                segment, 
                temp_dir, 
                sample_rate, 
                audio_converted, 
                audio_original, 
                full_ref_path=segment["audio_path"]
            )

        safe_update(94.0, "Juntando áudio e vídeo...")
        print("\nSaving final audio...")
        output_audio_path = os.path.join(temp_dir, "audio_converted_adjusted.wav")
        sf.write(output_audio_path, audio_converted, sample_rate)

        print("Creating final video...")
        original_name = os.path.splitext(os.path.basename(video_path))[0]
        video_filename = f"translated_{model_name.upper()}_{original_name}.mp4"
        output_video_path = os.path.join(output_dir, video_filename)

        if video_path.endswith('.m4a'):
             ffmpeg_cmd = f'ffmpeg -y -f lavfi -i color=c=black:s=1280x720:r=30 -i "{output_audio_path}" -shortest -c:v libx264 -c:a aac -strict experimental "{output_video_path}"'
        else:
            ffmpeg_cmd = (
                f'ffmpeg -y -i "{video_path}" -i "{output_audio_path}" '
                f'-filter_complex "[0:v]setpts=PTS-STARTPTS[v];[1:a]asetpts=PTS-STARTPTS[a]" '
                f'-map "[v]" -map "[a]" '
                f'-c:v libx264 -c:a aac -pix_fmt yuv420p -shortest '
                f'-movflags +faststart "{output_video_path}"'
            )

        if os.system(ffmpeg_cmd) != 0: raise Exception("Failed to combine audio with video")

        return output_video_path

    except Exception as e:
        raise Exception(f"Error in process_video: {str(e)}")