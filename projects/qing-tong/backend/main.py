"""
千瞳 - 视角转换器 Backend API
FastAPI server for video processing and depth estimation.
"""

import os
import shutil
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from depth_estimator import load_depth_model
from video_processor import (
    create_task,
    get_task_status,
    get_task_metadata,
    get_frame_paths,
    get_frame_image,
)

app = FastAPI(title="千瞳 - 视角转换器", version="0.1.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Upload directory
UPLOAD_DIR = Path(__file__).parent / 'uploads'
UPLOAD_DIR.mkdir(exist_ok=True)


@app.on_event("startup")
async def startup():
    """Load depth model on startup."""
    print("=" * 50)
    print("千瞳 - 视角转换器 Backend")
    print("=" * 50)
    print("Loading depth estimation model...")
    success = load_depth_model()
    if success:
        print("Depth model loaded. High-quality depth estimation available.")
    else:
        print("Using fallback depth estimation (gradient-based).")
        print("For better results, download Depth Anything V2 checkpoint to backend/checkpoints/")
    print("=" * 50)


@app.post("/api/video/upload")
async def upload_video(video: UploadFile = File(...)):
    """Upload a video and start processing."""
    if not video.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    # Save uploaded file
    file_ext = Path(video.filename).suffix or '.mp4'
    save_path = UPLOAD_DIR / f"{os.urandom(8).hex()}{file_ext}"

    with open(save_path, "wb") as f:
        shutil.copyfileobj(video.file, f)

    # Start processing task
    task_id = create_task(str(save_path))

    # Get initial metadata from video
    import cv2
    cap = cv2.VideoCapture(str(save_path))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or 1920
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) or 1080
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 0
    cap.release()

    return {
        "task_id": task_id,
        "fps": fps,
        "width": width,
        "height": height,
        "total_frames": total,
    }


@app.get("/api/video/status/{task_id}")
async def video_status(task_id: str):
    """Get processing status of a video task."""
    status = get_task_status(task_id)
    if status['status'] == 'not_found':
        raise HTTPException(status_code=404, detail="Task not found")
    return status


@app.get("/api/video/frames/{task_id}")
async def video_frames(task_id: str):
    """Get list of all frames for a processed video."""
    status = get_task_status(task_id)
    if status['status'] != 'completed':
        raise HTTPException(status_code=400, detail=f"Task not completed yet: {status['status']}")

    metadata = get_task_metadata(task_id)
    frames = get_frame_paths(task_id)

    return {
        "metadata": metadata,
        "frames": [{"index": f["index"]} for f in frames],
    }


@app.get("/api/video/frame/{task_id}/{frame_index}/rgb")
async def get_rgb_frame(task_id: str, frame_index: int):
    """Get RGB image for a specific frame."""
    path = get_frame_image(task_id, frame_index, 'rgb')
    if not path:
        raise HTTPException(status_code=404, detail="Frame not found")
    return FileResponse(path, media_type="image/jpeg")


@app.get("/api/video/frame/{task_id}/{frame_index}/depth")
async def get_depth_frame(task_id: str, frame_index: int):
    """Get depth map image for a specific frame."""
    path = get_frame_image(task_id, frame_index, 'depth')
    if not path:
        raise HTTPException(status_code=404, detail="Depth map not found")
    return FileResponse(path, media_type="image/png")


@app.get("/api/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "service": "千瞳视角转换器"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
