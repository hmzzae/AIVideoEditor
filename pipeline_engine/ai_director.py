import google.generativeai as genai
import re
import time

def get_gemini_decision(transcript_path, api_key):
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    with open(transcript_path, "r", encoding="utf-8") as f:
        transcript_data = f.read()

    prompt = f"""
    You are an expert short-form video editor (TikTok/Reels). Read this transcript.
    Find the most engaging, complete thought that is under 60 seconds.
    Do NOT cut the sentence in half.
    Return ONLY the start and end timestamps in this exact format:
    START: HH:MM:SS
    END: HH:MM:SS

    Transcript:
    {transcript_data}
    """
    
    for attempt in range(3):
        try:
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            if attempt == 2: raise e
            time.sleep(4)

def parse_timestamps(ai_text):
    times = re.findall(r"\d{2}:\d{2}:\d{2}", ai_text)
    if len(times) >= 2:
        # Force chronological order so FFmpeg never crashes
        start_t = min(times[0], times[1])
        end_t = max(times[0], times[1])
        return start_t, end_t
    raise ValueError("Could not parse valid HH:MM:SS timestamps from AI response.")