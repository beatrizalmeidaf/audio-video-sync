import os
import torch
import torchaudio
import numpy as np
import soundfile as sf
from .audio_processor import AudioVADSlicer, process_segment_audio

def process_video(video_path, temp_dir, tts, pipe, output_dir):
    """
    Processa um vídeo extraindo o áudio, segmentando-o usando detecção de atividade vocal (VAD),
    transcrevendo e traduzindo os segmentos de áudio, sintetizando o áudio traduzido
    e gerando um vídeo final traduzido.

    Args:
        video_path (str): Caminho para o arquivo de vídeo de entrada.
        temp_dir (str): Diretório para armazenar arquivos temporários.
        tts: Instância do modelo de texto para fala.
        pipe: Pipeline para transcrição e tradução.
        output_dir (str): Diretório para salvar o vídeo final de saída.

    Returns:
        str: Caminho para o vídeo traduzido gerado.

    Raises:
        Exception: Se ocorrer algum erro durante o processamento do vídeo.
    """
    try:
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")

        print("Extracting audio from video...")
        audio_path = os.path.join(temp_dir, "audio_original.wav")
        ffmpeg_cmd = f'ffmpeg -y -i "{video_path}" -map 0:a -to 00:00:30 -acodec pcm_s16le -ar 16000 -ac 1 "{audio_path}"'
        if os.system(ffmpeg_cmd) != 0:
            raise Exception("Failed to extract audio from video")

        print("Initializing VAD slicer...")
        slicer = AudioVADSlicer(
            device='cpu',
            min_sec=1.5,
            max_sec=20,
            threshold=0.75,
            rms_threshold=0.008
        )

        print("Processing audio segments...")
        segments = slicer(audio_path)
        audio_segments = []

        waveform, sample_rate = torchaudio.load(audio_path)
        audio_original = waveform[0].numpy()
        audio_converted = np.zeros_like(audio_original)

        for segment in segments:
            s = segment["start"]
            e = segment["end"]
            segment_audio = torch.from_numpy(segment["audio"]).float().unsqueeze(0)
            if segment["sample_rate"] != 24000:
                segment_audio = torchaudio.functional.resample(
                    segment_audio, segment["sample_rate"], 24000)

            segment_path = os.path.join(temp_dir, f"segment_{s}_{e}.wav")
            torchaudio.save(segment_path, segment_audio, 24000)

            duration = (e - s) / sample_rate

            audio_segments.append({
                "audio": segment_audio,
                "audio_path": segment_path,
                "transcription": None,
                "translation": None,
                "start": s,
                "end": e,
                "duration": duration
            })

        print(f"\nProcessing {len(audio_segments)} segments...")
        for i, segment in enumerate(audio_segments, 1):
            try:
                print(f"\nSegment {i}/{len(audio_segments)}")

                transcription = pipe(segment["audio_path"],
                                  generate_kwargs={"task": "transcribe",
                                                 "language": "portuguese"})["text"]

                translation = pipe(segment["audio_path"],
                                generate_kwargs={"task": "translate",
                                               "language": "english"})["text"]

                segment["transcription"] = transcription
                segment["translation"] = translation

                torch.cuda.empty_cache() if torch.cuda.is_available() else None

            except Exception as e:
                print(f"Error processing segment {i}: {e}")
                continue

        print("\nGenerating translated audio...")
        for i, segment in enumerate(audio_segments, 1):
            try:
                print(f"\nSynthesizing segment {i}/{len(audio_segments)}")
                if not segment["translation"]:
                    print(f"Skipping segment {i} - no translation available")
                    continue

                process_segment_audio(tts, segment, temp_dir, sample_rate, audio_converted, audio_original)

                torch.cuda.empty_cache() if torch.cuda.is_available() else None

            except Exception as e:
                print(f"Error processing segment {i}: {e}")
                continue

        print("\nSaving final audio...")
        output_audio_path = os.path.join(temp_dir, "audio_converted_adjusted.wav")
        sf.write(output_audio_path, audio_converted, sample_rate)

        print("Creating final video...")
        video_filename = f"translated_{os.path.basename(video_path)}"
        output_video_path = os.path.join(output_dir, video_filename)

        if video_path.endswith('.m4a'):
            ffmpeg_cmd = (
                f'ffmpeg -y -f lavfi -i color=c=black:s=1280x720:r=30 -i "{output_audio_path}" '
                f'-shortest -c:v libx264 -c:a aac -strict experimental "{output_video_path}"'
            )
        else:
            ffmpeg_cmd = (
                f'ffmpeg -y -i "{video_path}" -i "{output_audio_path}" '
                f'-c:v copy -c:a aac -map 0:v:0 -map 1:a:0 "{output_video_path}"'
            )

        if os.system(ffmpeg_cmd) != 0:
            raise Exception("Failed to combine audio with video")

        return output_video_path

    except Exception as e:
        raise Exception(f"Error in process_video: {str(e)}")