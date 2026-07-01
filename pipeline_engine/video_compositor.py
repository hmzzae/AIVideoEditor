import os
import ffmpeg
from pipeline_engine.utils import clean_path

def burn_subtitles_and_audio(silent_video, original_audio_source, srt_path, final_output):
    print("\nVisual rendering complete. Burning in styled subtitles and merging audio...")
    try:
        clean_srt_path = clean_path(srt_path)
        
        video_stream = ffmpeg.input(silent_video)
        audio_stream = ffmpeg.input(original_audio_source).audio
        
        tiktok_style = "FontName=Arial,FontSize=18,PrimaryColour=&H0000FFFF,OutlineColour=&H40000000,BorderStyle=1,Outline=2,Bold=1,MarginV=40"
        
        video_with_subs = video_stream.filter('subtitles', filename=clean_srt_path, force_style=tiktok_style)
        
        (
            ffmpeg
            .output(video_with_subs, audio_stream, final_output, vcodec='libx264', acodec='aac')
            .run(overwrite_output=True, quiet=False)
        )
        print(f"Success! Subtitled vertical video compiled: {final_output}")
        
        if os.path.exists(silent_video): 
            os.remove(silent_video)
            
    except ffmpeg.Error as e:
        print("An error occurred during audio compilation.")
        if e.stderr: 
            print(e.stderr.decode('utf-8'))