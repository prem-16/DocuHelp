"""Data loader utilities."""
from pathlib import Path
from typing import List, Dict, Optional, BinaryIO
import tempfile
import shutil
import mimetypes
from datetime import datetime


VIDEO_EXTENSIONS = {'.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.m4v'}


def list_videos(folder: Path) -> List[Path]:
    """Return a list of video files in `folder`."""
    return [p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in VIDEO_EXTENSIONS]


def parse_video_from_upload(
    file_content: BinaryIO,
    filename: str,
    metadata: Optional[Dict] = None
) -> Dict:
    """
    Parse video file from frontend upload.

    Args:
        file_content: Binary file content from frontend upload
        filename: Original filename
        metadata: Optional metadata dict (procedure type, user info, etc.)

    Returns:
        Dict containing:
            - temp_path: Path to temporary file
            - filename: Original filename
            - file_size: Size in bytes
            - mime_type: MIME type
            - extension: File extension
            - metadata: Additional metadata
            - timestamp: Upload timestamp
    """
    # Validate file type
    extension = Path(filename).suffix.lower()
    if extension not in VIDEO_EXTENSIONS:
        raise ValueError(
            f"Invalid video format: {extension}. "
            f"Supported formats: {', '.join(VIDEO_EXTENSIONS)}"
        )

    # Determine MIME type
    mime_type, _ = mimetypes.guess_type(filename)
    if not mime_type:
        mime_type = 'video/mp4'  # Default fallback

    # Create temporary file
    temp_dir = Path(tempfile.gettempdir()) / "docuhelp_videos"
    temp_dir.mkdir(exist_ok=True)

    # Generate unique filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_filename = f"{timestamp}_{Path(filename).stem}{extension}"
    temp_path = temp_dir / safe_filename

    # Save file to temporary location
    file_size = 0
    with open(temp_path, 'wb') as f:
        shutil.copyfileobj(file_content, f)
        file_size = temp_path.stat().st_size

    return {
        'temp_path': str(temp_path),
        'filename': filename,
        'safe_filename': safe_filename,
        'file_size': file_size,
        'mime_type': mime_type,
        'extension': extension,
        'metadata': metadata or {},
        'timestamp': timestamp,
        'upload_time': datetime.now().isoformat()
    }


def validate_video_file(file_path: Path) -> bool:
    """
    Validate that a video file exists and is readable.

    Args:
        file_path: Path to video file

    Returns:
        True if valid, False otherwise
    """
    if not file_path.exists():
        return False

    if not file_path.is_file():
        return False

    if file_path.suffix.lower() not in VIDEO_EXTENSIONS:
        return False

    # Check if file is not empty
    if file_path.stat().st_size == 0:
        return False

    return True


if __name__ == "__main__":
    print("Dataset loader stub")
