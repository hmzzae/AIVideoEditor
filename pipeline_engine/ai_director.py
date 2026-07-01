import time
import re
from google import genai

def get_gemini_decision(transcript_path, api_key):
    print("--- [2/4] Consulting Gemini AI for Editing Strategy ---")
    
    client = genai.Client(api_key=api_key)
    
    with open(transcript_path, "r", encoding="utf-8") as file:
        transcript_data = file.read()
        
    prompt = f"""
    You are an expert short-form video editor (TikTok, Reels, Shorts). 
    Below is a transcript of a video with timestamps. 
    
    Your goal is to identify the single most engaging "hook" or complete thought.
    
    Strict Rules:
    1. The segment MUST be a complete thought or conversation. Do not cut off mid-sentence.
    2. It can be less than 60 seconds, but it MUST NOT exceed 60 seconds.
    3. Do not include extra filler talk just to reach the 60-second limit. Cut it exactly where the interesting thought ends naturally.
    
    Return ONLY the start and end timestamp in this exact format: START: 00:00:10, END: 00:00:45
    
    Transcript:
    {transcript_data}
    """
    
    # AUTO-RETRY LOGIC FOR 503 SERVER ERRORS
    max_retries = 3
    for attempt in range(max_retries):
        try:
            # We switched to the highly stable production Flash model
            response = client.models.generate_content(
                model='gemini-2.5-flash', 
                contents=prompt
            )
            
            decision = response.text.strip()
            print(f"Gemini Decision received:\n{decision}\n")
            return decision
            
        except Exception as e:
            error_msg = str(e)
            if "503" in error_msg or "Unavailable" in error_msg:
                print(f"[Network] Google servers busy (Attempt {attempt + 1}/{max_retries}). Waiting 4 seconds to retry...")
                time.sleep(4) # Wait 4 seconds before trying again
            else:
                raise e
                
    raise RuntimeError("Google Gemini API is completely overloaded right now. Please try again in a few minutes.")

def parse_timestamps(gemini_text):
    print("--- [3/4] Parsing Timestamps for Video Cutter ---")
    # Uses Regular Expressions (Regex) to extract timestamps formatted like 00:00:00
    pattern = r"(\d{2}:\d{2}:\d{2})"
    matches = re.findall(pattern, gemini_text)
    
    if len(matches) >= 2:
        start_time = matches[0]
        end_time = matches[1]
        print(f"Parsed Times -> Start: {start_time}, End: {end_time}\n")
        return start_time, end_time
    else:
        raise ValueError("Could not parse timestamps from Gemini's response. Check format.")