import torch

class Config:
    # --- Dynamic System & Hardware Detection ---
    MODEL_SIZE = "base"
    
    if torch.cuda.is_available():
        DEVICE = "cuda"
        COMPUTE_TYPE = "float16"
    else:
        DEVICE = "cpu"
        COMPUTE_TYPE = "int8"
    
    # --- File Paths ---
    TEMP_TRANSCRIPT = "real_transcript.txt"
    TEMP_HORIZONTAL = "final_ai_clip.mp4"
    TEMP_SILENT = "temp_silent.mp4"
    TEMP_SUBS = "clip_subs.srt"