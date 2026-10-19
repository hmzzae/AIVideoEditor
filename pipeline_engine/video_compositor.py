import ffmpeg
from pipeline_engine.utils import clean_path

def burn_subtitles_and_audio(silent_video, original_video, srt_file, output_file):
    clean_silent = clean_path(silent_video)
    clean_audio_src = clean_path(original_video)
    clean_srt = clean_path(srt_file)
    clean_out = clean_path(output_file)
    
    try:
        video_input = ffmpeg.input(clean_silent)
        audio_input = ffmpeg.input(clean_audio_src).audio
        
        # TikTok style: Yellow, bold Arial, black outline, bottom margin
        style = "FontName=Arial,FontSize=18,PrimaryColour=&H00FFFF,OutlineColour=&H00000000,BorderStyle=1,Outline=2,Shadow=0,MarginV=40"
        
        video_with_subs = video_input.filter('subtitles', clean_srt, force_style=style)
        
        (
            ffmpeg
            .output(video_with_subs, audio_input, clean_out, vcodec='libx264', acodec='aac')
            .run(overwrite_output=True, quiet=False)
        )
    except ffmpeg.Error as e:
        if e.stderr:
            print(e.stderr.decode('utf-8'))
        raise RuntimeError("FFmpeg failed to burn subtitles and merge audio.")