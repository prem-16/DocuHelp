"""Test script for YouTube parser functionality."""
import json
import logging
from docuhelp.dataset.youtube_parser import YouTubeParser

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_youtube_parser():
    """Test YouTube parser with a sample video."""

    parser = YouTubeParser()

    # Example YouTube URL (replace with your surgical procedure video)
    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=42s"

    print("=" * 80)
    print("YOUTUBE VIDEO PARSER TEST")
    print("=" * 80)
    print()

    # Test 1: Extract Video ID
    print("1. EXTRACTING VIDEO ID")
    print("-" * 80)
    video_id = parser.extract_video_id(test_url)
    print(f"   URL: {test_url}")
    print(f"   Video ID: {video_id}")
    print()

    # Test 2: Extract URL timestamp
    print("2. EXTRACTING URL TIMESTAMP")
    print("-" * 80)
    url_timestamp = parser.extract_url_timestamp(test_url)
    if url_timestamp:
        print(f"   Start time from URL: {url_timestamp}s ({parser.format_timestamp(url_timestamp)})")
    else:
        print("   No timestamp in URL")
    print()

    # Test 3: Parse timestamps
    print("3. TESTING TIMESTAMP PARSING")
    print("-" * 80)
    test_timestamps = ["1:23", "1:23:45", "42", "0:05"]
    for ts in test_timestamps:
        seconds = parser.parse_timestamp(ts)
        print(f"   '{ts}' -> {seconds}s")
    print()

    # Test 4: Parse description timestamps
    print("4. PARSING DESCRIPTION TIMESTAMPS")
    print("-" * 80)
    sample_description = """
    This is a surgical procedure video.

    Timestamps:
    0:00 Introduction
    1:30 Patient preparation
    5:45 - Incision and access
    [10:20] Main procedure
    15:00 - Closure
    20:30 Post-operative notes
    """
    timestamps = parser.parse_description_timestamps(sample_description)
    print(f"   Found {len(timestamps)} timestamps:")
    for ts in timestamps:
        print(f"   - {ts['time_formatted']} ({ts['time']}s): {ts['label']}")
    print()

    # Test 5: Full video parsing (requires internet connection)
    print("5. FULL VIDEO PARSING")
    print("-" * 80)
    print("   Attempting to parse full video data...")
    print("   (This requires internet connection and may take a moment)")
    print()

    try:
        result = parser.parse_youtube_video(
            test_url,
            extract_subtitles=True,
            subtitle_languages=['en']
        )

        print(f"   ✓ Successfully parsed video!")
        print(f"   - Title: {result['metadata']['title']}")
        print(f"   - Author: {result['metadata']['author']}")
        print(f"   - Duration: {result['metadata']['duration_formatted']} ({result['metadata']['length']}s)")
        print(f"   - Views: {result['metadata']['views']:,}")
        print(f"   - Publish Date: {result['metadata']['publish_date']}")
        print(f"   - Description timestamps: {len(result['description_timestamps'])}")
        print(f"   - Has subtitles: {result['has_subtitles']}")
        print(f"   - Subtitle languages: {', '.join(result['subtitle_languages'])}")

        if result['subtitles']:
            for lang, subs in result['subtitles'].items():
                print(f"   - {lang} subtitles: {len(subs)} segments")
                if subs:
                    print(f"     First segment: '{subs[0]['text']}' at {subs[0]['start']}s")

        print()
        print("6. SAVING PARSED DATA")
        print("-" * 80)
        output_file = "youtube_parsed_sample.json"
        parser.save_parsed_data(result, output_file)
        print(f"   ✓ Saved to {output_file}")

    except ImportError as e:
        print(f"   ✗ Missing dependencies: {e}")
        print(f"   Install with: pip install pytube youtube-transcript-api")
    except Exception as e:
        print(f"   ✗ Error: {e}")
        logger.exception("Error during full parsing")

    print()
    print("=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    test_youtube_parser()
