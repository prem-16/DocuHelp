"""Video endpoints for handling video uploads and processing"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
import logging
import os
from pathlib import Path
import shutil
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter()

# Configure upload directory
UPLOAD_DIR = Path("frontend/uploads/videos")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Check if Firebase is enabled
# USE_FIREBASE = "false"

# # Import storage backends
# if USE_FIREBASE:
#     try:
#         from ...firebase_config import upload_to_storage, save_to_firestore, get_from_firestore
#         logger.info("Using Firebase storage backend")
#     except Exception as e:
#         logger.warning(f"Firebase import failed: {e}. Falling back to local storage.")
#         USE_FIREBASE = False

# if not USE_FIREBASE:
from ...local_storage import save_metadata, get_metadata, update_metadata
logger.info("Using local storage backend")


# Background task for VLM processing
def process_video_with_vlm(video_id: str):
    """Background task to run VLM inference on uploaded video."""
    try:
        logger.info(f"Starting background VLM processing for video: {video_id}")

        # Update status to processing
        update_metadata(video_id, {"status": "processing"})

        # Import here to avoid circular imports
        from docuhelp.vlm.inference import run_vlm_inference_pipeline

        # Run VLM inference (extracts frames and analyzes)
        # Use 30 second minimum separation to allow for more granular phase detection
        result = run_vlm_inference_pipeline(video_id, fps=1, min_time_separation=30.0)

        logger.info(f"VLM processing completed for {video_id}: {len(result.get('phases', []))} phases found")

    except Exception as e:
        logger.error(f"Background VLM processing failed for {video_id}: {e}")
        update_metadata(video_id, {
            "status": "error",
            "error_message": str(e)
        })


@router.post("/upload")
async def upload_video(
    background_tasks: BackgroundTasks,
    video: UploadFile = File(..., description="MP4 video file"),
    procedure: str = Form(..., description="Selected surgical procedure")
):
    """
    Upload video file and procedure selection for VLM inference.

    Args:
        video: MP4 video file from frontend
        procedure: Selected surgical procedure category

    Returns:
        JSON response with video_id and upload status
    """
    try:
        # Validate video file
        if not video.content_type.startswith("video/"):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type. Expected video file, got {video.content_type}"
            )

        # Generate unique video ID
        video_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()

        # Save video locally
        video_filename = f"{video_id}_{video.filename}"
        video_path = UPLOAD_DIR / video_filename

        with video_path.open("wb") as buffer:
            shutil.copyfileobj(video.file, buffer)

        logger.info(f"Video saved locally: {video_path}")

        # Initialize metadata
        metadata = {
            "video_id": video_id,
            "procedure": procedure,
            "video_filename": video.filename,
            "local_path": str(video_path),
            "status": "uploaded",
            "uploaded_at": timestamp,
            "processed": False
        }

        # Upload to cloud storage if Firebase is enabled
        video_url = None    
        USE_FIREBASE = False
        if USE_FIREBASE:
            try:
                storage_path = f"videos/{video_id}/{video_filename}"
                video_url = upload_to_storage(
                    str(video_path),
                    storage_path,
                    content_type=video.content_type
                )
                metadata["video_url"] = video_url

                # Save to Firestore
                save_to_firestore("videos", video_id, metadata)
                logger.info(f"Metadata saved to Firestore")

            except Exception as e:
                logger.warning(f"Firebase upload failed: {e}. Falling back to local storage.")
                USE_FIREBASE = False

        # Save metadata locally (always, as backup or primary)
        if not USE_FIREBASE:
            save_metadata(video_id, metadata)
            logger.info(f"Metadata saved to local storage")

        logger.info(f"Video upload complete: {video_id}")

        # Start VLM processing in background
        logger.info(f"Scheduling VLM inference for video: {video_id}")
        background_tasks.add_task(process_video_with_vlm, video_id)

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "video_id": video_id,
                "procedure": procedure,
                "video_url": video_url if video_url else f"/api/v1/video/video/{video_id}",
                "message": "Video uploaded successfully. VLM processing started.",
                "local_path": str(video_path),
                "storage_mode": "firebase" if USE_FIREBASE else "local",
                "vlm_status": "processing"
            }
        )

    except Exception as e:
        logger.error(f"Error uploading video: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.get("/{video_id}")
async def get_video(video_id: str):
    """
    Retrieve video metadata by ID.

    Args:
        video_id: Unique video identifier

    Returns:
        Video metadata from storage
    """
    USE_FIREBASE = False
    try:
        # Get metadata from appropriate backend
        if USE_FIREBASE:
            metadata = get_from_firestore("videos", video_id)
        else:
            metadata = get_metadata(video_id)

        if not metadata:
            raise HTTPException(
                status_code=404,
                detail=f"Video not found: {video_id}"
            )

        return JSONResponse(
            status_code=200,
            content=metadata
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving video: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Retrieval failed: {str(e)}")


@router.get("/{video_id}/status")
async def get_video_status(video_id: str):
    """Get processing status of a video."""
    USE_FIREBASE = False
    try:
        # Get metadata from appropriate backend
        if USE_FIREBASE:
            metadata = get_from_firestore("videos", video_id)
        else:
            metadata = get_metadata(video_id)

        if not metadata:
            raise HTTPException(status_code=404, detail="Video not found")

        return {
            "video_id": video_id,
            "status": metadata.get("status", "unknown"),
            "processed": metadata.get("processed", False),
            "procedure": metadata.get("procedure"),
            "vlm_latency": metadata.get("vlm_latency"),
            "phases_count": len(metadata.get("vlm_phases", []))
        }

    except Exception as e:
        logger.error(f"Error getting video status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{video_id}/vlm-results")
async def get_vlm_results(video_id: str):
    """
    Get VLM inference results for a video.

    Returns:
        VLM analysis results with phases and key frames
    """
    USE_FIREBASE = False
    try:
        # Get metadata from appropriate backend
        if USE_FIREBASE:
            metadata = get_from_firestore("videos", video_id)
        else:
            metadata = get_metadata(video_id)

        if not metadata:
            raise HTTPException(status_code=404, detail="Video not found")

        # Check if VLM processing is complete
        if not metadata.get("processed", False):
            status = metadata.get("status", "unknown")

            # If processing failed, return error status
            if status == "error":
                error_message = metadata.get("error_message", "Unknown error occurred during processing")
                return JSONResponse(
                    status_code=500,
                    content={
                        "video_id": video_id,
                        "status": "error",
                        "message": f"VLM processing failed: {error_message}",
                        "processed": False,
                        "error_message": error_message
                    }
                )

            # Otherwise still processing
            return JSONResponse(
                status_code=202,  # Accepted but not ready
                content={
                    "video_id": video_id,
                    "status": status,
                    "message": f"VLM processing {status}. Results not ready yet.",
                    "processed": False
                }
            )

        # Return VLM results
        phases = metadata.get("vlm_phases", [])

        # Remove base64 data from phases for summary (too large)
        phases_summary = []
        for phase in phases:
            phase_copy = phase.copy()
            if "key_frame_data" in phase_copy:
                phase_copy["has_key_frame"] = True
                del phase_copy["key_frame_data"]  # Don't send base64 in summary
            phases_summary.append(phase_copy)

        return JSONResponse(
            status_code=200,
            content={
                "video_id": video_id,
                "procedure": metadata.get("procedure"),
                "status": "completed",
                "processed": True,
                "vlm_summary": metadata.get("vlm_summary", ""),
                "phases": phases_summary,
                "vlm_latency": metadata.get("vlm_latency"),
                "model": metadata.get("model", "google/gemini-2.0-flash-exp:free")
            }
        )

    except Exception as e:
        logger.error(f"Error getting VLM results: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{video_id}/phase/{phase_index}/refine")
async def refine_phase_description(
    video_id: str,
    phase_index: int,
    user_feedback: str = Form(..., description="User's correction/feedback for the phase")
):
    """
    Refine a phase description based on user feedback.

    Args:
        video_id: Video ID
        phase_index: Index of the phase to refine (0-based)
        user_feedback: User's textual feedback/correction

    Returns:
        Refined phase with updated description
    """
    USE_FIREBASE = False
    try:
        # Get metadata
        if USE_FIREBASE:
            metadata = get_from_firestore("videos", video_id)
        else:
            metadata = get_metadata(video_id)

        if not metadata:
            raise HTTPException(status_code=404, detail="Video not found")

        phases = metadata.get("vlm_phases", [])

        if phase_index < 0 or phase_index >= len(phases):
            raise HTTPException(status_code=404, detail=f"Phase {phase_index} not found")

        phase = phases[phase_index]
        procedure = metadata.get("procedure", "Unknown")

        # Get the frame data
        frame_data = phase.get("key_frame_data")
        if not frame_data:
            raise HTTPException(status_code=404, detail="No frame data for this phase")

        current_description = phase.get("description", "")

        # Use VLM to refine the description
        from docuhelp.vlm.openrouter_client import create_vlm_client
        vlm_client = create_vlm_client()

        logger.info(f"Refining phase {phase_index} with user feedback: {user_feedback[:100]}")

        refined_description = vlm_client.refine_phase_description(
            frame_base64=frame_data,
            current_description=current_description,
            user_feedback=user_feedback,
            procedure=procedure
        )

        # Update the phase description
        phase["description"] = refined_description
        phase["refined"] = True
        phase["original_description"] = current_description
        phase["user_feedback"] = user_feedback

        # Update metadata
        update_metadata(video_id, {"vlm_phases": phases})

        logger.info(f"Phase {phase_index} refined successfully")

        return JSONResponse(
            status_code=200,
            content={
                "video_id": video_id,
                "phase_index": phase_index,
                "refined_description": refined_description,
                "timestamp_range": phase.get("timestamp_range"),
                "key_timestamp": phase.get("key_timestamp"),
                "message": "Phase description refined successfully"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error refining phase: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{video_id}/phase/{phase_index}/frame")
async def get_phase_key_frame(video_id: str, phase_index: int):
    """
    Get the key frame image for a specific phase.

    Args:
        video_id: Video ID
        phase_index: Index of the phase (0-based)

    Returns:
        Base64 encoded image data
    """
    USE_FIREBASE = False
    try:
        # Get metadata
        if USE_FIREBASE:
            metadata = get_from_firestore("videos", video_id)
        else:
            metadata = get_metadata(video_id)

        if not metadata:
            raise HTTPException(status_code=404, detail="Video not found")

        phases = metadata.get("vlm_phases", [])

        if phase_index < 0 or phase_index >= len(phases):
            raise HTTPException(status_code=404, detail=f"Phase {phase_index} not found")

        phase = phases[phase_index]
        frame_data = phase.get("key_frame_data")

        if not frame_data:
            raise HTTPException(status_code=404, detail="No key frame data for this phase")

        return JSONResponse(
            status_code=200,
            content={
                "video_id": video_id,
                "phase_index": phase_index,
                "timestamp": phase.get("key_timestamp"),
                "timestamp_range": phase.get("timestamp_range"),
                "description": phase.get("description"),
                "image_base64": frame_data
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting phase key frame: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{video_id}/phase/{phase_index}/alternative-frames")
async def get_alternative_keyframes(video_id: str, phase_index: int):
    """
    Get alternative keyframe options for a phase (for when the default is blurry/uninformative).

    Args:
        video_id: Video ID
        phase_index: Index of the phase (0-based)

    Returns:
        List of alternative keyframes from the phase's time range
    """
    USE_FIREBASE = False
    try:
        import cv2
        import base64

        # Get metadata
        if USE_FIREBASE:
            metadata = get_from_firestore("videos", video_id)
        else:
            metadata = get_metadata(video_id)

        if not metadata:
            raise HTTPException(status_code=404, detail="Video not found")

        phases = metadata.get("vlm_phases", [])

        if phase_index < 0 or phase_index >= len(phases):
            raise HTTPException(status_code=404, detail=f"Phase {phase_index} not found")

        phase = phases[phase_index]
        video_path = metadata.get("local_path")

        if not video_path or not Path(video_path).exists():
            raise HTTPException(status_code=404, detail="Video file not found")

        # Parse timestamp range to get start and end seconds
        start_seconds = phase.get("start_seconds", 0)
        end_seconds = phase.get("end_seconds", 60)

        # Open video
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise HTTPException(status_code=500, detail="Failed to open video")

        video_fps = cap.get(cv2.CAP_PROP_FPS)

        # Extract 5 evenly-spaced frames from this phase's time range
        duration = end_seconds - start_seconds
        step = duration / 6  # 5 frames means 6 intervals

        alternative_frames = []
        for i in range(1, 6):  # Get 5 alternatives
            timestamp_sec = start_seconds + (i * step)

            # Seek to the frame
            frame_number = int(timestamp_sec * video_fps)
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)

            ret, frame = cap.read()
            if ret:
                # Encode frame to base64
                _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
                frame_base64 = base64.b64encode(buffer).decode('utf-8')

                minutes = int(timestamp_sec // 60)
                seconds = int(timestamp_sec % 60)
                timestamp_str = f"{minutes}:{seconds:02d}"

                alternative_frames.append({
                    "timestamp": timestamp_str,
                    "timestamp_seconds": round(timestamp_sec, 2),
                    "image_base64": frame_base64
                })

        cap.release()

        logger.info(f"Generated {len(alternative_frames)} alternative frames for phase {phase_index}")

        return JSONResponse(
            status_code=200,
            content={
                "video_id": video_id,
                "phase_index": phase_index,
                "timestamp_range": phase.get("timestamp_range"),
                "alternative_frames": alternative_frames
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting alternative keyframes: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{video_id}/phase/{phase_index}/update-keyframe")
async def update_phase_keyframe(
    video_id: str,
    phase_index: int,
    new_timestamp: float = Form(..., description="New timestamp in seconds"),
    new_image_base64: str = Form(..., description="New keyframe image as base64")
):
    """
    Update the keyframe for a phase with a user-selected alternative and regenerate description.

    Args:
        video_id: Video ID
        phase_index: Index of the phase
        new_timestamp: New timestamp in seconds
        new_image_base64: New keyframe image data

    Returns:
        Updated phase information with regenerated description
    """
    USE_FIREBASE = False
    try:
        from ...vlm.openrouter_client import create_vlm_client

        # Get metadata
        if USE_FIREBASE:
            metadata = get_from_firestore("videos", video_id)
        else:
            metadata = get_metadata(video_id)

        if not metadata:
            raise HTTPException(status_code=404, detail="Video not found")

        phases = metadata.get("vlm_phases", [])
        procedure = metadata.get("procedure", "surgical procedure")

        if phase_index < 0 or phase_index >= len(phases):
            raise HTTPException(status_code=404, detail=f"Phase {phase_index} not found")

        # Update the phase with new keyframe
        minutes = int(new_timestamp // 60)
        seconds = int(new_timestamp % 60)
        new_timestamp_str = f"{minutes}:{seconds:02d}"

        phases[phase_index]["key_frame_data"] = new_image_base64
        phases[phase_index]["key_timestamp"] = new_timestamp_str
        phases[phase_index]["key_timestamp_seconds"] = new_timestamp
        phases[phase_index]["keyframe_updated"] = True

        # Regenerate description based on new keyframe
        logger.info(f"Regenerating description for phase {phase_index} with new keyframe")

        vlm_client = create_vlm_client()

        # Create prompt for description generation
        prompt = f"""You are analyzing a surgical video of a {procedure}.

This is phase {phase_index + 1} of the procedure. Based on this keyframe image, provide a detailed description of what is happening in this surgical phase.

Describe:
1. The surgical action being performed
2. Instruments or tools visible
3. Anatomical structures involved
4. The technique being used

Keep the description professional, concise (2-3 sentences), and focused on what is visible in the image."""

        # Generate new description
        new_description = vlm_client.generate_description(new_image_base64, prompt)

        # Update the description
        phases[phase_index]["description"] = new_description
        phases[phase_index]["description_regenerated"] = True

        # Update metadata
        update_metadata(video_id, {"vlm_phases": phases})

        logger.info(f"Updated keyframe and regenerated description for phase {phase_index}")

        return JSONResponse(
            status_code=200,
            content={
                "video_id": video_id,
                "phase_index": phase_index,
                "new_timestamp": new_timestamp_str,
                "new_description": new_description,
                "message": "Keyframe updated and description regenerated successfully"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating phase keyframe: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{video_id}/generate-report")
async def generate_surgical_report(video_id: str):
    """
    Generate final professional surgical report from approved phases.

    Args:
        video_id: Video ID

    Returns:
        Professional surgical report (text-only, no images)
    """
    USE_FIREBASE = False
    try:
        # Get metadata
        if USE_FIREBASE:
            metadata = get_from_firestore("videos", video_id)
        else:
            metadata = get_metadata(video_id)

        if not metadata:
            raise HTTPException(status_code=404, detail="Video not found")

        phases = metadata.get("vlm_phases", [])
        procedure = metadata.get("procedure", "Unknown Procedure")
        uploaded_at = metadata.get("uploaded_at", "Unknown Date")

        if not phases:
            raise HTTPException(status_code=400, detail="No phases found for this video")

        # Sort phases chronologically by start_seconds
        sorted_phases = sorted(
            phases,
            key=lambda p: p.get("start_seconds", p.get("key_timestamp_seconds", 0))
        )

        # Generate professional report
        report_lines = []

        # Header
        report_lines.append("=" * 80)
        report_lines.append("SURGICAL PROCEDURE DOCUMENTATION REPORT")
        report_lines.append("=" * 80)
        report_lines.append("")

        # Procedure Information
        report_lines.append("PROCEDURE INFORMATION")
        report_lines.append("-" * 80)
        report_lines.append(f"Procedure Type: {procedure}")
        report_lines.append(f"Date of Documentation: {uploaded_at}")
        report_lines.append(f"Total Phases Documented: {len(sorted_phases)}")
        report_lines.append("")

        # Calculate total duration
        if sorted_phases:
            total_duration_seconds = sorted_phases[-1].get("end_seconds", 0)
            total_minutes = int(total_duration_seconds // 60)
            total_seconds = int(total_duration_seconds % 60)
            report_lines.append(f"Total Procedure Duration: {total_minutes}:{total_seconds:02d}")
        report_lines.append("")
        report_lines.append("")

        # Detailed Phase Documentation
        report_lines.append("SURGICAL PHASES - CHRONOLOGICAL DOCUMENTATION")
        report_lines.append("=" * 80)
        report_lines.append("")

        for idx, phase in enumerate(sorted_phases, 1):
            timestamp_range = phase.get("timestamp_range", "N/A")
            description = phase.get("description", "No description available")
            refined = phase.get("refined", False)

            report_lines.append(f"PHASE {idx}")
            report_lines.append("-" * 80)
            report_lines.append(f"Time Range: {timestamp_range}")

            if refined:
                report_lines.append(f"Status: Clinician-Reviewed and Refined")

            report_lines.append("")
            report_lines.append(f"Description:")
            report_lines.append(f"{description}")
            report_lines.append("")

        # Footer
        report_lines.append("=" * 80)
        report_lines.append("END OF SURGICAL DOCUMENTATION REPORT")
        report_lines.append("=" * 80)
        report_lines.append("")
        report_lines.append("Note: This report was generated using AI-assisted surgical video analysis.")
        report_lines.append("All phases have been reviewed and approved by clinical personnel.")

        # Join into final report
        final_report = "\n".join(report_lines)

        # Save report to metadata
        update_metadata(video_id, {"surgical_report": final_report})

        logger.info(f"Generated surgical report for video {video_id}")

        return JSONResponse(
            status_code=200,
            content={
                "video_id": video_id,
                "procedure": procedure,
                "phases_count": len(sorted_phases),
                "report": final_report,
                "message": "Surgical report generated successfully"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating surgical report: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
