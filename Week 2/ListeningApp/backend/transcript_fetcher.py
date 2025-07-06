import re
import os
from youtube_transcript_api import YouTubeTranscriptApi

def fetch_transcript(youtube_url: str) -> dict:
    """
    Fetches the transcript for a given YouTube URL, calculates basic stats,
    saves the raw transcript to a file, and returns the results.
    """
    video_id_match = re.search(r"(?<=v=)[a-zA-Z0-9_-]+", youtube_url)
    if not video_id_match:
        return {"success": False, "error": "Invalid YouTube URL provided."}

    video_id = video_id_match.group(0)
    output_dir = "yt_lang_app/data/transcripts"
    os.makedirs(output_dir, exist_ok=True)
    transcript_path = os.path.join(output_dir, f"{video_id}.txt")

    try:
        # Fetch the transcript
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=['en', 'en-US'])
        full_transcript_text = " ".join([item['text'] for item in transcript_list])

        # Save the raw transcript to a file
        with open(transcript_path, "w", encoding="utf-8") as f:
            f.write(full_transcript_text)

        # Calculate statistics
        word_count = len(full_transcript_text.split())
        # Simple heuristic for token count (approximate)
        token_count = int(word_count * 1.3) # Or word_count / 0.75
        # Estimate reading time assuming 200 words per minute
        estimated_reading_time_minutes = round(word_count / 200, 2)

        # Create a transcript preview
        transcript_preview = full_transcript_text[:1000] + "..." if len(full_transcript_text) > 1000 else full_transcript_text

        return {
            "success": True,
            "video_id": video_id,
            "full_transcript_path": transcript_path,
            "word_count": word_count,
            "token_count": token_count,
            "estimated_reading_time_minutes": estimated_reading_time_minutes,
            "transcript_preview": transcript_preview
        }

    except Exception as e:
        return {"success": False, "error": f"Failed to fetch or process transcript for video ID {video_id}: {e}"}

# Example usage (for independent testing)
if __name__ == '__main__':
    test_url = "https://www.youtube.com/watch?v=isMpyCkKuDU" # Replace with a real URL
    result = fetch_transcript(test_url)
    print(result)
