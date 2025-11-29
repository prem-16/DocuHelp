"""Test script for age-restricted YouTube videos."""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

import logging
from docuhelp.dataset.youtube_parser import YouTubeParser

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s:%(name)s:%(message)s'
)

logger = logging.getLogger(__name__)

def test_age_restricted_video():
    """Test YouTube parser with an age-restricted video."""

    parser = YouTubeParser()

    # Age-restricted video URL
    test_url = "https://youtu.be/uYRbY1uVHTc?si=hbcVoxtj4khLFWHD"

    print("=" * 60)
    print("Testing Age-Restricted YouTube Video")
    print("=" * 60)
    print(f"URL: {test_url}")
    print()

    try:
        # Extract video ID
        video_id = parser.extract_video_id(test_url)
        print(f"Video ID: {video_id}")
        print()

        # Try to get metadata (will automatically use OAuth if age-restricted)
        print("Fetching metadata...")
        metadata = parser.get_video_metadata(test_url)

        print()
        print("✓ SUCCESS!")
        print("-" * 60)
        print(f"Title: {metadata['title']}")
        print(f"Author: {metadata['author']}")
        print(f"Duration: {metadata['duration_formatted']} ({metadata['length']}s)")
        print(f"Views: {metadata['views']:,}")
        print(f"Publish Date: {metadata['publish_date']}")
        print()

    except Exception as e:
        print()
        print("✗ ERROR!")
        print("-" * 60)
        print(f"Error: {e}")
        logger.exception("Full error details:")
        return False

    return True

if __name__ == "__main__":
    success = test_age_restricted_video()
    sys.exit(0 if success else 1)
