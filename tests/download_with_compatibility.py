"""Download YouTube video with maximum compatibility (no FFmpeg required)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

import logging
import yt_dlp

logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(message)s')

def download_compatible_format(url: str, output_dir: Path = Path("downloads/compatible")):
    """
    Download video in a format that doesn't require FFmpeg.
    Uses pre-merged MP4 format if available.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    # Configure yt-dlp for maximum compatibility
    ydl_opts = {
        'format': 'best[ext=mp4]/best',  # Prefer pre-merged MP4
        'outtmpl': str(output_dir / '%(title)s.%(ext)s'),
        'writesubtitles': True,
        'writeautomaticsub': True,
        'writethumbnail': True,
        'writedescription': True,
        'writeinfojson': True,
        'progress_hooks': [progress_hook],
    }

    # Add cookie support if file exists
    cookies_file = Path("youtube_cookies.txt")
    if cookies_file.exists():
        ydl_opts['cookiefile'] = str(cookies_file)
        print(f"Using cookies from: {cookies_file}")

    print("=" * 80)
    print("YouTube Video Downloader (Compatibility Mode)")
    print("=" * 80)
    print(f"URL: {url}")
    print("Format: Best pre-merged MP4 (no FFmpeg required)")
    print()

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print("Downloading...")
            info = ydl.extract_info(url, download=True)

            video_file = output_dir / f"{info['title']}.{info['ext']}"

            print()
            print("=" * 80)
            print("SUCCESS!")
            print("=" * 80)
            print(f"Title: {info['title']}")
            print(f"Format: {info['ext']}")
            print(f"Resolution: {info.get('resolution', 'N/A')}")
            print(f"File: {video_file}")
            print()
            print("This file should play in any MP4 player!")
            print("=" * 80)

            return str(video_file)

    except Exception as e:
        print()
        print("=" * 80)
        print("ERROR")
        print("=" * 80)
        print(f"{e}")
        print()
        print("If this is an age-restricted video:")
        print("1. Export cookies using browser extension")
        print("2. Save as 'youtube_cookies.txt' in this folder")
        print("3. Run again")
        print("=" * 80)
        return None


def progress_hook(d):
    """Show download progress."""
    if d['status'] == 'downloading':
        total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
        downloaded = d.get('downloaded_bytes', 0)
        if total > 0:
            percent = (downloaded / total) * 100
            print(f"\rProgress: {percent:.1f}%", end='', flush=True)
    elif d['status'] == 'finished':
        print("\rDownload complete!       ")


def main():
    """Main function."""
    # Check for FFmpeg
    import subprocess
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
        print("NOTE: FFmpeg is installed! You can use the full downloader.")
        print("      This script uses compatibility mode (lower quality).")
        print()
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("NOTE: FFmpeg not found - using compatibility mode")
        print("      Install FFmpeg for better quality: choco install ffmpeg")
        print()

    # Get video URL
    url = input("Enter YouTube URL: ").strip()
    if not url:
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Default test video
        print(f"Using default test video: {url}")

    print()
    download_compatible_format(url)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nCancelled by user.")
    except Exception as e:
        print(f"\nError: {e}")
