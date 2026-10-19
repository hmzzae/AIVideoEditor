import os
import sys
import platform
from datetime import datetime
from config import Config
from pipeline_engine.transcription import run_transcription
from pipeline_engine.ai_director import get_gemini_decision, parse_timestamps
from pipeline_engine.video_cutter import cut_video
from pipeline_engine.face_tracker import render_cinematic_crop
from pipeline_engine.subtitle_generator import generate_subtitles
from pipeline_engine.video_compositor import burn_subtitles_and_audio

def sync_hardware_paths(log_callback):
    """Maps local binaries dynamically based on Operating System."""
    current_os = platform.system()
    
    if current_os == "Windows":
        local_dir = os.path.dirname(os.path.abspath(__file__))
        os.environ["PATH"] += os.pathsep + local_dir
        
        try:
            site_packages = os.path.join(sys.prefix, "Lib", "site-packages")
            cublas_bin = os.path.join(site_packages, "nvidia", "cublas", "bin")
            cudnn_bin = os.path.join(site_packages, "nvidia", "cudnn", "bin")
            
            if os.path.exists(cublas_bin):
                os.environ["PATH"] += os.pathsep + cublas_bin + os.pathsep + cudnn_bin
                log_callback("[System] Windows hardware paths synced.")
        except Exception as e:
            log_callback(f"[Warning] Could not map NVIDIA DLLs: {e}")
            
    elif current_os == "Linux":
        log_callback("[System] Ubuntu Linux detected. Relying on native system PATH.")

def run_full_pipeline(video_path, api_key, log_callback, status_callback, on_complete):
    """The main assembly line."""
    try:
        sync_hardware_paths(log_callback)
        
        # 1. Transcription
        status_callback("Transcribing audio tracks...")
        log_callback("[Engine] Spinning up Whisper translation vectors...")
        run_transcription(video_path, Config.TEMP_TRANSCRIPT)
        
        # 2. AI Direction
        status_callback("Consulting Gemini Flash...")
        log_callback("[Engine] Requesting AI hook selection...")
        ai_decision = get_gemini_decision(Config.TEMP_TRANSCRIPT, api_key)
        start_t, end_t = parse_timestamps(ai_decision)
        
        # 3. Horizontal Cut
        status_callback("Isolating selected sequence...")
        cut_video(video_path, Config.TEMP_HORIZONTAL, start_t, end_t)
        
        if not os.path.exists(Config.TEMP_HORIZONTAL):
            raise FileNotFoundError("Video cutter failed to create clip.")
            
        # 4. Cinematic Cropping
        status_callback("Calculating dynamic speaker mesh boundaries...")
        log_callback("[MediaPipe] Processing facial anchor grids...")
        render_cinematic_crop(Config.TEMP_HORIZONTAL, Config.TEMP_SILENT)
        
        # 5. Subtitles & Compositing
        status_callback("Burning cinematic subtitles...")
        log_callback("[FFmpeg] Compiling final vertical stack...")
        srt_path = generate_subtitles(Config.TEMP_HORIZONTAL, Config.TEMP_SUBS)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_filename = f"ai_short_{timestamp}.mp4"
        final_output = os.path.join(os.path.dirname(video_path), unique_filename)
        
        burn_subtitles_and_audio(Config.TEMP_SILENT, Config.TEMP_HORIZONTAL, srt_path, final_output)
        
        # 6. Cleanup
        for temp_file in [Config.TEMP_HORIZONTAL, Config.TEMP_TRANSCRIPT, Config.TEMP_SUBS, Config.TEMP_SILENT]:
            if os.path.exists(temp_file):
                os.remove(temp_file)
            
        log_callback(f"\n[Complete] Target short created at: {final_output}")
        status_callback("Processing completely finished!")
        on_complete(final_output)
        
    except Exception as e:
        log_callback(f"\n[CRITICAL ERROR] Execution failed: {str(e)}")
        status_callback("Execution broken due to errors.")
        on_complete(None)