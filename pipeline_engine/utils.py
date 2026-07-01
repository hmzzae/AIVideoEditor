import os

def format_srt_time(seconds):
    """Formats raw seconds into standard SRT timestamp format."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds - int(seconds)) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

def clean_path(path):
    """Converts Windows backslashes to forward slashes for FFmpeg."""
    return os.path.abspath(path).replace("\\", "/")