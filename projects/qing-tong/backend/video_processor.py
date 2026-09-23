"""
Video processing module: extract frames, estimate depth, serve results.
"""

import os
import cv2
import json
import uuid
import threading
import numpy as np
from pathlib import Path
from depth_estimator import estimate_depth

# Storage for processing tasks
TASKS_DIR = Path(__file__).parent / 'tasks'

# In-memory task status
_tasks: dict = {}
_tasks_lock = threading.Lock()


def process_video(task_id: str, video_path: str, max_frames: int = 50):
    """Process video: extract frames + estimate depth maps."""
    try:
        with _tasks_lock:
            _tasks[task_id]['status'] = 'processing'

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Cannot open video: {video_path}")

        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        # Calculate frame skip to stay within max_frames
        skip = max(1, total_frames // max_frames)

        task_dir = TASKS_DIR / task_id
        rgb_dir = task_dir / 'rgb'
        depth_dir = task_dir / 'depth'
        rgb_dir.mkdir(parents=True, exist_ok=True)
        depth_dir.mkdir(parents=True, exist_ok=True)

        frame_index = 0
        saved_index = 0

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            if frame_index % skip == 0:
                # Save RGB frame
                rgb_path = rgb_dir / f'{saved_index:05d}.jpg'
                cv2.imwrite(str(rgb_path), frame, [cv2.IMWRITE_JPEG_QUALITY, 90])

                # Estimate and save depth map
                depth_map = estimate_depth(frame)
                depth_path = depth_dir / f'{saved_index:05d}.png'
                cv2.imwrite(str(depth_path), depth_map)

                saved_index += 1

                # Update progress
                progress = int((frame_index / total_frames) * 100) if total_frames > 0 else 0
                with _tasks_lock:
                    _tasks[task_id]['current_frame'] = saved_index
                    _tasks[task_id]['progress'] = progress

            frame_index += 1

        cap.release()

        # Save metadata
        metadata = {
            'task_id': task_id,
            'total_frames': saved_index,
            'fps': fps,
            'width': width,
            'height': height,
            'original_total_frames': total_frames,
        }
        with open(task_dir / 'metadata.json', 'w') as f:
            json.dump(metadata, f)

        with _tasks_lock:
            _tasks[task_id]['status'] = 'completed'
            _tasks[task_id]['total_frames'] = saved_index
            _tasks[task_id]['progress'] = 100

    except Exception as e:
        with _tasks_lock:
            _tasks[task_id]['status'] = 'failed'
            _tasks[task_id]['error'] = str(e)
        raise


def create_task(video_path: str) -> str:
    """Create a new processing task and start it in background."""
    task_id = str(uuid.uuid4())[:8]

    with _tasks_lock:
        _tasks[task_id] = {
            'status': 'queued',
            'progress': 0,
            'current_frame': 0,
            'total_frames': 0,
            'video_path': video_path,
        }

    # Start processing in background thread
    thread = threading.Thread(target=process_video, args=(task_id, video_path))
    thread.daemon = True
    thread.start()

    return task_id


def get_task_status(task_id: str) -> dict:
    """Get current status of a processing task."""
    with _tasks_lock:
        task = _tasks.get(task_id)
        if not task:
            return {'status': 'not_found'}

        return {
            'status': task['status'],
            'progress': task.get('progress', 0),
            'current_frame': task.get('current_frame', 0),
            'total_frames': task.get('total_frames', 0),
            'error': task.get('error'),
        }


def get_task_metadata(task_id: str) -> dict | None:
    """Get task metadata from disk."""
    metadata_path = TASKS_DIR / task_id / 'metadata.json'
    if metadata_path.exists():
        with open(metadata_path) as f:
            return json.load(f)
    return None


def get_frame_paths(task_id: str) -> list[dict]:
    """Get list of all frame paths for a task."""
    rgb_dir = TASKS_DIR / task_id / 'rgb'
    if not rgb_dir.exists():
        return []

    frames = []
    for f in sorted(rgb_dir.glob('*.jpg')):
        index = int(f.stem)
        frames.append({
            'index': index,
            'rgb_path': str(f),
            'depth_path': str(TASKS_DIR / task_id / 'depth' / f'{f.stem}.png'),
        })

    return frames


def get_frame_image(task_id: str, frame_index: int, image_type: str = 'rgb') -> str | None:
    """Get path to a specific frame image."""
    ext = 'jpg' if image_type == 'rgb' else 'png'
    path = TASKS_DIR / task_id / image_type / f'{frame_index:05d}.{ext}'
    return str(path) if path.exists() else None
