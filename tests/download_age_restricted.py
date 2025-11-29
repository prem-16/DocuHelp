"""Download age-restricted YouTube videos using cookies."""
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
    print("=" * 80)
    print("Age-Restricted YouTube Video Downloader")
    print("=" * 80)
    print()

    # Check if cookies file exists
    cookies_file = Path("youtube_cookies.txt")
    if not cookies_file.exists():
        print("ERROR: youtube_cookies.txt not found!")
        print()
        print("Please follow these steps to export your YouTube cookies:")
        print()
        print("1. Install browser extension:")
        print("   Chrome: https://chromewebstore.google.com/detail/")
        print("          get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc")
        print()
        print("   Firefox: https://addons.mozilla.org/en-US/firefox/addon/cookies-txt/")
        print()
        print("2. Login to YouTube in your browser")
        print("3. Go to youtube.com")
        print("4. Click the extension icon and export cookies")
        print("5. Save as 'youtube_cookies.txt' in this folder:")
        print(f"   {Path.cwd()}")
        print()
        print("=" * 80)
        return False

    # Create downloader
    downloader = YouTubeDownloader(download_dir=Path("downloads/age_restricted"))

    # Get video URL
    print("Cookies file found: youtube_cookies.txt")
    print()
    video_url = input("Enter age-restricted video URL: ").strip()

    if not video_url:
        print("No URL provided. Exiting.")
        return False

    print()
    print(f"Downloading: {video_url}")
    print("Using cookies from: youtube_cookies.txt")
    print()

    # Ask for quality
    print("Select quality:")
    print("  1. Best quality")
    print("  2. 1080p")
    print("  3. 720p (recommended)")
    print("  4. 480p")
    print("  5. Audio only (MP3)")
    quality_choice = input("Choice (default: 3): ").strip() or "3"

    quality_map = {
        "1": ("best", False),
        "2": ("1080p", False),
        "3": ("720p", False),
        "4": ("480p", False),
        "5": ("best", True)
    }

    quality, audio_only = quality_map.get(quality_choice, ("720p", False))

    print()
    print(f"Downloading {'audio' if audio_only else 'video'} at {quality}...")
    print()

    try:
        result = downloader.download_video(
            url=video_url,
            cookies_file=str(cookies_file),
            quality=quality,
            audio_only=audio_only,
            download_subtitles=True,
            extract_metadata=False  # Skip pytubefix for age-restricted videos
        )

        print()
        print("=" * 80)
        print("SUCCESS!")
        print("=" * 80)
        print(f"Title:     {result['title']}")
        print(f"Video ID:  {result['video_id']}")
        if audio_only:
            print(f"Audio:     {result['video_path']}")
        else:
            print(f"Video:     {result['video_path']}")
        if result['subtitle_paths']:
            print(f"Subtitles: {len(result['subtitle_paths'])} files")
        print(f"Directory: {result['video_dir']}")
        print("=" * 80)

        return True

    except Exception as e:
        print()
        print("=" * 80)
        print("ERROR!")
        print("=" * 80)
        print(f"{e}")
        print()
        print("Troubleshooting:")
        print("1. Make sure you're logged into YouTube in your browser")
        print("2. Re-export fresh cookies (they may have expired)")
        print("3. Make sure FFmpeg is installed:")
        print("   - Windows: choco install ffmpeg")
        print("   - Or: https://ffmpeg.org/download.html")
        print("4. Check that your account can access this video")
        print("=" * 80)
        return False

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nDownload cancelled by user.")
        sys.exit(1)
