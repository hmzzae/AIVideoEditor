from faster_whisper import WhisperModel
from config import Config

def run_transcription(video_path, output_txt_path):
    print("--- [1/4] Starting Local AI Transcription ---")
    
    print(f"Loading Whisper '{Config.MODEL_SIZE}' model onto NVIDIA GPU (CUDA)...")
    model = WhisperModel(Config.MODEL_SIZE, device=Config.DEVICE, compute_type=Config.COMPUTE_TYPE)
    
    print(f"Transcribing {video_path}...")
    segments, info = model.transcribe(video_path, beam_size=5)
    
    # Save segments directly to a file so we can read it later
    with open(output_txt_path, "w", encoding="utf-8") as file:
        for segment in segments:
            line = f"[{segment.start:.2f}s -> {segment.end:.2f}s] {segment.text}\n"
            file.write(line)
            
    print(f"Transcription complete! Saved to {output_txt_path}\n")