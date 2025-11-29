"""Test parsing age-restricted YouTube videos with OAuth authentication."""
import sys
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from docuhelp.dataset.video_input_parser import VideoInputParser

logging.basicConfig(level=logging.INFO)

url = "https://youtu.be/uYRbY1uVHTc?si=hbcVoxtj4khLFWHD"

print("=" * 80)
print("TESTING AGE-RESTRICTED VIDEO WITH OAUTH")
print("=" * 80)
print(f"\nURL: {url}\n")

parser = VideoInputParser()

print("NOTE: This video is age-restricted and requires authentication.")
print("When you run this with use_oauth=True, a browser window will open")
print("asking you to sign in to your Google account.")
print()
print("Options:")
print("  1. Without OAuth (will fail for age-restricted videos)")
print("  2. With OAuth (requires browser login)")
print()

# Test 1: Without OAuth (will fail)
print("-" * 80)
print("TEST 1: Without OAuth (Expected to fail)")
print("-" * 80)
try:
    result = parser.parse_input(url, extract_youtube_subtitles=False, use_oauth=False)
    print("SUCCESS - This shouldn't happen for age-restricted videos!")
except Exception as e:
    print(f"FAILED (Expected): {type(e).__name__}: {e}")

print()

# Test 2: With OAuth (should work after login)
print("-" * 80)
print("TEST 2: With OAuth (Will open browser for login)")
print("-" * 80)
print("\nTo use OAuth authentication, uncomment the code below:")
print()
print("try:")
print("    result = parser.parse_input(")
print("        url,")
print("        extract_youtube_subtitles=False,")
print("        use_oauth=True,")
print("        allow_oauth_cache=True")
print("    )")
print("    print('SUCCESS!')")
print("    print(f'Title: {result[\"title\"]}')")
print("    print(f'Duration: {result[\"duration\"]}s')")
print("    print(f'Author: {result[\"video_data\"][\"metadata\"][\"author\"]}')")
print("except Exception as e:")
print("    print(f'FAILED: {e}')")
print()
print("=" * 80)
print("To enable OAuth, uncomment the code above and re-run this script.")
print("=" * 80)
