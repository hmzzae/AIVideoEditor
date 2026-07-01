import os
import sys
import platform
from config import Config
from pipeline_engine.transcription import run_transcription
from pipeline_engine.ai_director import get_gemini_decision, parse_timestamps
from pipeline_engine.video_cutter import cut_video
from pipeline_engine.face_tracker import render_cinematic_crop
from pipeline_engine.subtitle_generator import generate_subtitles
from pipeline_engine.video_compositor import burn_subtitles_and_audio

def sync_hardware_paths(log_callback):
    """Maps local binaries and NVIDIA DLLs on Windows."""
    if platform.system() == "Windows":
        
        # 1. Map local FFmpeg binaries (CRUCIAL for video cutter!)
        local_dir = os.path.dirname(os.path.abspath(__file__))
        os.environ["PATH"] += os.pathsep + local_dir
        
        # 2. Map NVIDIA DLLs
        try:
            site_packages = os.path.join(sys.prefix, "Lib", "site-packages")
            cublas_bin = os.path.join(site_packages, "nvidia", "cublas", "bin")
            cudnn_bin = os.path.join(site_packages, "nvidia", "cudnn", "bin")
            
            if os.path.exists(cublas_bin):
                os.environ["PATH"] += os.pathsep + cublas_bin + os.pathsep + cudnn_bin
                log_callback("[System] Hardware paths synced. FFmpeg and NVIDIA libraries forcefully mapped.")
            else:
                log_callback("[ERROR] NVIDIA folders not found in site-packages!")
        except Exception as e:
            log_callback(f"[Warning] Could not map NVIDIA DLLs: {e}")

def run_full_pipeline(video_path, api_key, log_callback, status_callback, on_complete):
    """
    The main assembly line. 
    Callbacks are used to send live updates back to the UI without freezing it.
    """
    try:
        # --- 0. Hardware Sync ---
        # We must run the Windows DLL fix before anything else!
        sync_hardware_paths(log_callback)
        
        # --- 1. Transcription ---
        status_callback("Transcribing audio tracks locally...")
        log_callback("[Engine] Spinning up local Whisper translation vectors...")
        run_transcription(video_path, Config.TEMP_TRANSCRIPT)
        
        # --- 2. AI Direction ---
        status_callback("Consulting Gemini 3 Flash...")
        log_callback("[Engine] Requesting AI hook selection...")
        ai_decision = get_gemini_decision(Config.TEMP_TRANSCRIPT, api_key)
        start_t, end_t = parse_timestamps(ai_decision)
        
       # --- 3. Horizontal Cut ---
        status_callback("Isolating selected horizontal sequence...")
        cut_video(video_path, Config.TEMP_HORIZONTAL, start_t, end_t)
        
        # ADD THIS SAFETY CHECK:
        if not os.path.exists(Config.TEMP_HORIZONTAL):
            raise FileNotFoundError("Video cutter failed. 'final_ai_clip.mp4' was never created.")
            
        # --- 4. Cinematic Cropping (MediaPipe) ---
        status_callback("Calculating dynamic speaker mesh boundaries...")
        log_callback("[MediaPipe] Processing facial anchor grids frame-by-frame...")
        render_cinematic_crop(Config.TEMP_HORIZONTAL, Config.TEMP_SILENT)
        
        # --- 5. Subtitles & Audio Burn ---
        status_callback("Burning cinematic subtitles...")
        log_callback("[FFmpeg] Compiling final vertical stack...")
        srt_path = generate_subtitles(Config.TEMP_HORIZONTAL, Config.TEMP_SUBS)
        
        final_output = os.path.join(os.path.dirname(video_path), Config.FINAL_OUTPUT)
        burn_subtitles_and_audio(Config.TEMP_SILENT, Config.TEMP_HORIZONTAL, srt_path, final_output)
        
        # --- 6. Cleanup ---
        if os.path.exists(Config.TEMP_HORIZONTAL): os.remove(Config.TEMP_HORIZONTAL)
        if os.path.exists(Config.TEMP_TRANSCRIPT): os.remove(Config.TEMP_TRANSCRIPT)
        if os.path.exists(Config.TEMP_SUBS): os.remove(Config.TEMP_SUBS)
            
        log_callback(f"\n[Complete] Target short created at: {final_output}")
        status_callback("Processing completely finished!")
        
        # Tell the UI we are done and hand back the file path
        on_complete(final_output)
        
    except Exception as e:
        log_callback(f"\n[CRITICAL ERROR] Execution failed: {str(e)}")
        status_callback("Execution broken due to errors.")
        on_complete(None)