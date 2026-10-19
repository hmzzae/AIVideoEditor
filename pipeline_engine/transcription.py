from faster_whisper import WhisperModel
from config import Config

def run_transcription(video_path, output_txt):
    model = WhisperModel(Config.MODEL_SIZE, device=Config.DEVICE, compute_type=Config.COMPUTE_TYPE)
    segments, _ = model.transcribe(video_path, beam_size=5)
    
    with open(output_txt, "w", encoding="utf-8") as f:
        for segment in segments:
            f.write(f"[{segment.start:.2f}s -> {segment.end:.2f}s] {segment.text}\n")