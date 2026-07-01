class Config:
    # --- System & Hardware ---
    MODEL_SIZE = "base"
    DEVICE = "cuda"
    COMPUTE_TYPE = "float16"
    
    # --- File Paths ---
    TEMP_TRANSCRIPT = "real_transcript.txt"
    TEMP_HORIZONTAL = "final_ai_clip.mp4"
    TEMP_SILENT = "temp_silent.mp4"
    TEMP_SUBS = "clip_subs.srt"
    FINAL_OUTPUT = "ai_vertical_short.mp4"  # <-- This was missing!