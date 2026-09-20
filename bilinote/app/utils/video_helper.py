import subprocess
import os
import uuid


def generate_screenshot(video_path: str, output_dir: str, timestamp: int, index: int) -> str:
    """
    使用 ffmpeg 生成截图，返回生成图片路径
    """
    os.makedirs(output_dir, exist_ok=True)
    ids=str(uuid.uuid4())
    output_path = os.path.join(output_dir, f"screenshot_{str(index)+ids}.jpg")

    command = [
        "ffmpeg",
        "-ss", str(timestamp),
        "-i", video_path,
        "-frames:v", "1",
        "-q:v", "2",  # 图像质量
        output_path,
        "-y"  # 覆盖
    ]

    subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return output_path

