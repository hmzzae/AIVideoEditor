import ffmpeg

def cut_video(input_file, output_file, start_time, end_time):
    print(f"--- [4/4] Executing Video Cut ---")
    print(f"Slicing {input_file} from {start_time} to {end_time}...")
    
    try:
        (
            ffmpeg
            .input(input_file, ss=start_time, to=end_time)
            .output(output_file, vcodec='libx264', preset='ultrafast', acodec='aac')
            # CHANGED: quiet=False so we can see the exact FFmpeg error in the terminal
            .run(overwrite_output=True, quiet=False) 
        )
        print(f"Success! Final clip saved as: {output_file}\n")
    except ffmpeg.Error as e:
        print("\n[FFMPEG CRASH] An error occurred with FFmpeg cutting.")
        if e.stderr:
            print(e.stderr.decode('utf-8'))
        raise RuntimeError("FFmpeg failed to cut the video.")