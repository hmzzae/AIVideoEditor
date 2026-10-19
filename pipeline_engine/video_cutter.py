import ffmpeg
from pipeline_engine.utils import clean_path

def cut_video(input_file, output_file, start_time, end_time):
    clean_in = clean_path(input_file)
    clean_out = clean_path(output_file)
    
    try:
        (
            ffmpeg
            .input(clean_in, ss=start_time, to=end_time)
            .output(clean_out, vcodec='libx264', preset='ultrafast', acodec='aac')
            .run(overwrite_output=True, quiet=False)
        )
    except ffmpeg.Error as e:
        if e.stderr:
            print(e.stderr.decode('utf-8'))
        raise RuntimeError("FFmpeg failed to cut the video.")