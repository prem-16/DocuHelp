import sys
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from docuhelp.dataset.video_input_parser import VideoInputParser

logging.basicConfig(level=logging.INFO)

url = "https://youtu.be/uYRbY1uVHTc?si=hbcVoxtj4khLFWHD"

print("Testing YouTube URL parsing...")
print(f"URL: {url}")
print("-" * 60)

try:
    parser = VideoInputParser()
    result = parser.parse_input(url, extract_youtube_subtitles=False)

    print("SUCCESS!")
    print(f"Title: {result['title']}")
    print(f"Duration: {result['duration']}s")
    print(f"Author: {result['video_data']['metadata']['author']}")
    print(f"Video ID: {result['video_id']}")

except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
