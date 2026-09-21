import os
import sys
import webbrowser

sys.path.append(os.getcwd())

import uvicorn
from starlette.staticfiles import StaticFiles
from dotenv import load_dotenv

from app.db.cookie_dao import init_cookie_table
from app.db.model_dao import init_model_table
from app.db.provider_dao import init_provider_table
from app.utils.logger import get_logger
from app import create_app
from app.db.video_task_dao import init_video_task_table
from app.transcriber.transcriber_provider import get_transcriber
from events import register_handler
from ffmpeg_helper import ensure_ffmpeg_or_raise

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'app')))
logger = get_logger(__name__)
load_dotenv()

# 本地桌面工具默认只监听本机，避免局域网内他人访问 API/密钥/Cookie 配置
DEFAULT_HOST = "127.0.0.1"

static_dir = "static"
dist_dir = "dist/assets/"
dist_dir2 = "dist"
if not os.path.exists(static_dir):
    os.makedirs(static_dir)

out_dir = os.path.abspath(os.getenv('OUT_DIR', './static'))
if not os.path.exists(out_dir):
    os.makedirs(out_dir)

app = create_app()
app.mount("/assets", StaticFiles(directory=dist_dir), name="static")
app.mount("/static", StaticFiles(directory='./static'), name="staticss")
app.mount("/", StaticFiles(directory=dist_dir2), name="static2")

os.environ["FFMPEG_BINARY"] = os.getenv("FFMPEG_BINARY", os.path.abspath("bin/ffmpeg.exe"))
logger.info(f"FFMPEG 路径: {os.getenv('FFMPEG_BINARY')}")

@app.on_event("startup")
async def startup_event():
    register_handler()
    ensure_ffmpeg_or_raise()
    get_transcriber(transcriber_type=os.getenv("TRANSCRIBER_TYPE", "fast-whisper"))
    init_video_task_table()
    init_provider_table()
    init_model_table()
    init_cookie_table()

if __name__ == "__main__":
    port = int(os.getenv("BACKEND_PORT", 8000))
    host = os.getenv("BACKEND_HOST", DEFAULT_HOST) or DEFAULT_HOST
    if host == "0.0.0.0":
        logger.warning(
            "BACKEND_HOST=0.0.0.0 将对局域网开放，API Key / Cookie 配置接口可被同网访问；"
            "若非本机自用请改为 127.0.0.1"
        )
    if os.path.exists("cookies.txt"):
        logger.warning(
            "检测到根目录 cookies.txt。分发安装包前请删除该文件，并清空 .env 中的 COOKIE_FILE，"
            "避免把个人 B 站 Cookie带给使用者。"
        )
    url = f'http://127.0.0.1:{port}'
    logger.info(f"Starting server on {host}:{port}")
    logger.info(f"打开浏览器输入 {url}")
    logger.info(f"B站 Cookie 自助配置页: {url}/cookie.html（公开视频无需 Cookie）")
    logger.warning("首次启动可能需要下载 Whisper 模型，下载完成后刷新网页即可")
    webbrowser.open(url)
    uvicorn.run(app, host=host, port=port)
