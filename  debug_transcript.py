from youtube_transcript_api import YouTubeTranscriptApi
import re

video_url = "https://www.youtube.com/watch?v=6H5gQXzN6vQ"

def get_video_id(url):
    regex = r"(?:v=|\/)([0-9A-Za-z_-]{11}).*"
    match = re.search(regex, url)
    if match:
        return match.group(1)
    return None

try:
    video_id = get_video_id(video_url)
    print(f"Video ID: {video_id}")
    
    print("Attempting list_transcripts...")
    transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
    
    print("Available transcripts:")
    for t in transcript_list:
        print(f" - {t.language} ({t.language_code}) | Generated: {t.is_generated}")
        
    print("Fetching English transcript...")
    transcript = transcript_list.find_generated_transcript(['en'])
    data = transcript.fetch()
    print(f"First 100 chars: {str(data)[:100]}")
    print("Success!")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()