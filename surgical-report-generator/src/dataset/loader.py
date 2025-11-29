"""Data loader utilities."""
from pathlib import Path
from typing import List


def list_videos(folder: Path) -> List[Path]:
    """Return a list of video files in `folder`."""
    return [p for p in folder.iterdir() if p.is_file()]


if __name__ == "__main__":
    print("Dataset loader stub")
