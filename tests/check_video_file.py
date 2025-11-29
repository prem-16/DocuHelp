"""Check downloaded video file format and provide solutions."""
import sys
from pathlib import Path
import json

def check_video_files():
    """Find and check all downloaded video files."""
    print("=" * 80)
    print("Video File Checker")
    print("=" * 80)
    print()

    downloads_dir = Path("downloads")
    if not downloads_dir.exists():
        print("No downloads folder found.")
        return

    # Find all video-like files
    video_extensions = ['.mp4', '.webm', '.mkv', '.m4a', '.mp3', '.part']
    video_files = []

    for ext in video_extensions:
        video_files.extend(downloads_dir.rglob(f'*{ext}'))

    if not video_files:
        print("No video files found in downloads folder.")
        return

    print(f"Found {len(video_files)} video file(s):\n")

    for i, video_file in enumerate(video_files, 1):
        print(f"{i}. {video_file.name}")
        print(f"   Path: {video_file}")
        print(f"   Size: {video_file.stat().st_size / 1024 / 1024:.2f} MB")
        print(f"   Extension: {video_file.suffix}")

        # Check if there's a .part file (incomplete download)
        if video_file.suffix == '.part':
            print("   Status: INCOMPLETE DOWNLOAD")
            print("   Solution: Re-download the video")

        # Check for accompanying .info.json file
        info_file = video_file.with_suffix('.info.json')
        if info_file.exists():
            try:
                with open(info_file, 'r', encoding='utf-8') as f:
                    info = json.load(f)
                print(f"   Format: {info.get('ext', 'unknown')}")
                print(f"   Resolution: {info.get('resolution', 'N/A')}")
                print(f"   Duration: {info.get('duration', 'N/A')}s")
            except:
                pass

        # Check if file is playable
        if video_file.suffix in ['.mp4', '.webm', '.mkv'] and video_file.suffix != '.part':
            print("   Status: Should be playable")
            print(f"   Try opening: {video_file}")
        elif video_file.suffix in ['.m4a', '.mp3']:
            print("   Status: Audio only file")

        print()

    print("=" * 80)
    print("Troubleshooting:")
    print("=" * 80)
    print()
    print("If videos won't play:")
    print("1. Install FFmpeg: choco install ffmpeg")
    print("2. Re-download the video after installing FFmpeg")
    print("3. Or use: python download_with_compatibility.py")
    print()
    print("If you have .webm files:")
    print("  - Install VLC Media Player (plays all formats)")
    print("  - Or convert to MP4 after installing FFmpeg")
    print()


if __name__ == "__main__":
    check_video_files()
