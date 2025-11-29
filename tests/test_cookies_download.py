"""Test downloading age-restricted video with cookies."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from docuhelp.dataset.youtube_downloader import YouTubeDownloader

def main():
    # Check for cookies file
    cookies_file = Path("youtube_cookies.txt")

    if not cookies_file.exists():
        print("=" * 80)
        print("ERROR: youtube_cookies.txt not found!")
        print("=" * 80)
        print()
        print("To download age-restricted videos, you need to export your cookies:")
        print()
        print("1. Install this Chrome extension:")
        print("   https://chromewebstore.google.com/detail/")
        print("   get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc")
        print()
        print("2. Login to YouTube in Chrome")
        print("3. Go to youtube.com")
        print("4. Click the extension icon and click 'Export'")
        print("5. Rename the file to 'youtube_cookies.txt'")
        print("6. Save it here: " + str(Path.cwd()))
        print()
        print("=" * 80)
        return

    print("=" * 80)
    print("Testing Age-Restricted Video Download")
    print("=" * 80)
    print(f"Cookies file: {cookies_file} (found)")
    print()

    downloader = YouTubeDownloader(download_dir=Path("downloads/age_restricted_test"))

    # Your age-restricted video
    video_url = "https://youtu.be/uYRbY1uVHTc?si=hbcVoxtj4khLFWHD"

    print(f"URL: {video_url}")
    print("Quality: 720p")
    print("Downloading...")
    print()

    try:
        result = downloader.download_video(
            url=video_url,
            cookies_file=str(cookies_file),
            quality='720p',
            download_subtitles=True,
            extract_metadata=False  # Skip pytubefix for age-restricted
        )

        print()
        print("=" * 80)
        print("SUCCESS!")
        print("=" * 80)
        print(f"Title:     {result['title']}")
        print(f"Video ID:  {result['video_id']}")
        print(f"Video:     {result['video_path']}")
        print(f"Duration:  {result['download_info']['duration']}s")
        if result['subtitle_paths']:
            print(f"Subtitles: {len(result['subtitle_paths'])} files")
        print(f"Directory: {result['video_dir']}")
        print("=" * 80)
        print()
        print("All files saved successfully!")

    except Exception as e:
        print()
        print("=" * 80)
        print("ERROR")
        print("=" * 80)
        print(f"{e}")
        print()
        print("Common issues:")
        print("1. Cookies expired - re-export fresh cookies")
        print("2. Not logged into YouTube - login and re-export")
        print("3. FFmpeg not installed - install with: choco install ffmpeg")
        print("=" * 80)

if __name__ == "__main__":
    main()
