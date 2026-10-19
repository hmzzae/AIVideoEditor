from faster_whisper import WhisperModel
from config import Config
from pipeline_engine.utils import format_srt_time

def generate_subtitles(video_path, output_srt):
    model = WhisperModel(Config.MODEL_SIZE, device=Config.DEVICE, compute_type=Config.COMPUTE_TYPE)
    segments, _ = model.transcribe(video_path, word_timestamps=True)
    
    srt_index = 1
    with open(output_srt, "w", encoding="utf-8") as f:
        for segment in segments:
            current_phrase = []
            phrase_start = None
            
            for word in segment.words:
                if phrase_start is None:
                    phrase_start = word.start
                    
                current_phrase.append(word.word.strip().upper())
                
                if len(current_phrase) >= 3 or word.word.strip()[-1] in ".!?":
                    phrase_text = " ".join(current_phrase)
                    f.write(f"{srt_index}\n")
                    f.write(f"{format_srt_time(phrase_start)} --> {format_srt_time(word.end)}\n")
                    f.write(f"{phrase_text}\n\n")
                    srt_index += 1
                    current_phrase = []
                    phrase_start = None
                    
    return output_srt