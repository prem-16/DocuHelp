"""Quick demo of YouTube video downloader."""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

import logging
from docuhelp.dataset.youtube_downloader import YouTubeDownloader

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s:%(message)s'
)

def main():
    """Download a sample video."""
    print("=" * 80)
    print("YouTube Video Downloader - Quick Demo")
    print("=" * 80)
    print()

    # Create downloader
    downloader = YouTubeDownloader(download_dir=Path("downloads/demo"))

    # Sample video URL - replace with your own!
    video_url = input("Enter YouTube URL (or press Enter for demo video): ").strip()
    if not video_url:
        video_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

    print()
    print(f"Downloading: {video_url}")
    print()

    try:
        # Download with best quality
        result = downloader.download_video(
            url=video_url,
            quality='720p',
            download_subtitles=True,
            subtitle_languages=['en'],
            extract_metadata=True
        )

        print()
        print("=" * 80)
        print("SUCCESS!")
        print("=" * 80)
        print(f"Title:       {result['title']}")
        print(f"Video ID:    {result['video_id']}")
        print(f"Duration:    {result['download_info']['duration']}s")
        print(f"Views:       {result['download_info']['view_count']:,}")
        print()
        print("Files saved:")
        print(f"  Video:     {result['video_path']}")
        print(f"  Metadata:  {result['metadata_path']}")
        if result['subtitle_paths']:
            print(f"  Subtitles: {len(result['subtitle_paths'])} files")
        if result['thumbnail_path']:
            print(f"  Thumbnail: {result['thumbnail_path']}")
        print()
        print(f"All files in: {result['video_dir']}")
        print("=" * 80)

        return True

    except ImportError as e:
        print()
        print("ERROR: Missing dependency")
        print(f"{e}")
        print()
        print("Install with: pip install yt-dlp pytubefix youtube-transcript-api")
        return False

    except Exception as e:
        print()
        print("ERROR: Download failed")
        print(f"{e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
