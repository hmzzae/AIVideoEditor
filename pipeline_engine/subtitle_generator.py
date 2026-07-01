import os
from faster_whisper import WhisperModel
from config import Config
from pipeline_engine.utils import format_srt_time

def generate_subtitles(video_path, srt_filename):
    print("\n--- Generating Word-Synced Short-Form Captions on NVIDIA GPU (CUDA) ---")
    model = WhisperModel(Config.MODEL_SIZE, device=Config.DEVICE, compute_type=Config.COMPUTE_TYPE)
    segments, info = model.transcribe(video_path, word_timestamps=True)
    
    srt_path = os.path.abspath(srt_filename)
    with open(srt_path, "w", encoding="utf-8") as f:
        idx = 1
        for segment in segments:
            current_chunk = []
            chunk_start = None
            
            for word in segment.words:
                if chunk_start is None:
                    chunk_start = word.start
                    
                current_chunk.append(word.word.strip())
                
                if len(current_chunk) >= 3 or word.word.strip()[-1] in ".!?":
                    start_str = format_srt_time(chunk_start)
                    end_str = format_srt_time(word.end)
                    text_str = " ".join(current_chunk).upper() 
                    
                    f.write(f"{idx}\n{start_str} --> {end_str}\n{text_str}\n\n")
                    idx += 1
                    current_chunk = []
                    chunk_start = None
                    
            if current_chunk:
                start_str = format_srt_time(chunk_start)
                end_str = format_srt_time(segment.end)
                text_str = " ".join(current_chunk).upper()
                f.write(f"{idx}\n{start_str} --> {end_str}\n{text_str}\n\n")
                idx += 1
                
    print(f"Subtitles saved to: {srt_path}")
    return srt_path