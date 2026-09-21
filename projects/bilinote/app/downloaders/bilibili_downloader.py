import os
from abc import ABC
from typing import Union, Optional, Tuple, Any

import yt_dlp

from app.downloaders.base import Downloader, DownloadQuality
from app.models.notes_model import AudioDownloadResult
from app.services.cookie import CookieService, DownloadAuthError, is_auth_error
from app.utils.logger import get_logger
from app.utils.path_helper import get_data_dir

logger = get_logger(__name__)


class BilibiliDownloader(Downloader, ABC):
    def __init__(self):
        super().__init__()
        self.platform = "bilibili"
        self.cookies_from_browser = os.getenv("COOKIES_FROM_BROWSER", "")
        self.cookie_file = os.getenv("COOKIE_FILE", "")

    def _build_opts(self, output_path: str, need_video: bool = False) -> dict:
        if need_video:
            return {
                'format': 'bv*[ext=mp4]/bestvideo+bestaudio/best',
                'outtmpl': output_path,
                'noplaylist': True,
                'quiet': False,
                'merge_output_format': 'mp4',
            }
        return {
            'format': 'bestaudio[ext=m4a]/bestaudio/best',
            'outtmpl': output_path,
            'postprocessors': [
                {
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '64',
                }
            ],
            'noplaylist': True,
            'quiet': False,
        }

    @staticmethod
    def _apply_cookiefile(ydl_opts: dict, cookiefile: Optional[str]):
        if cookiefile and os.path.exists(cookiefile):
            ydl_opts['cookiefile'] = cookiefile

    @staticmethod
    def _apply_browser(ydl_opts: dict, browser: Optional[str]):
        if browser:
            ydl_opts['cookiesfrombrowser'] = (browser,)

    def _resolve_fallback_cookie(self) -> Tuple[Optional[str], Optional[str]]:
        """失败后的兜底 Cookie：用户自助配置优先，其次环境变量。"""
        cookiefile = CookieService.resolve_cookiefile(self.platform, prefer_user=True)
        if cookiefile:
            return cookiefile, None
        env_file = self.cookie_file
        if env_file and os.path.exists(env_file):
            return env_file, None
        browser = CookieService.resolve_cookiesfrombrowser() or self.cookies_from_browser
        return None, (browser or None)

    @staticmethod
    def _extract(video_url: str, ydl_opts: dict) -> Any:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            return ydl.extract_info(video_url, download=True)

    def _download_auth_aware(self, video_url: str, output_path: str, need_video: bool = False) -> dict:
        """
        无 Cookie 优先：
        1) 先匿名下载（公开视频通常足够）
        2) 若因登录/风控失败，再用用户配置或环境变量里的 Cookie 重试
        3) 仍失败且未配置 Cookie → 抛出可操作的中文错误
        """
        base_opts = self._build_opts(output_path, need_video=need_video)

        try:
            logger.info(f"[bilibili] 尝试无 Cookie 下载: {video_url}")
            return self._extract(video_url, dict(base_opts))
        except Exception as e:
            if not is_auth_error(e):
                raise
            logger.warning(f"[bilibili] 无 Cookie 下载失败，准备带 Cookie 重试: {e}")
            first_err = e

        cookiefile, browser = self._resolve_fallback_cookie()
        if not cookiefile and not browser:
            raise DownloadAuthError(
                CookieService.auth_error_message(self.platform),
                platform=self.platform,
            ) from first_err

        retry_opts = dict(base_opts)
        if cookiefile:
            logger.info(f"[bilibili] 使用 Cookie 文件重试: {cookiefile}")
            self._apply_cookiefile(retry_opts, cookiefile)
        elif browser:
            logger.info(f"[bilibili] 使用浏览器 Cookie 重试: {browser}")
            self._apply_browser(retry_opts, browser)

        try:
            return self._extract(video_url, retry_opts)
        except Exception as e:
            if is_auth_error(e):
                raise DownloadAuthError(
                    CookieService.auth_error_message(self.platform),
                    platform=self.platform,
                ) from e
            raise

    @staticmethod
    def _pick_video_path(output_dir: str, video_id: str) -> str:
        for ext in ("mp4", "mkv", "flv"):
            path = os.path.join(output_dir, f"{video_id}.{ext}")
            if os.path.exists(path):
                return path
        return os.path.join(output_dir, f"{video_id}.mp4")

    def download(
        self,
        video_url: str,
        output_dir: Union[str, None] = None,
        quality: DownloadQuality = "fast",
        need_video: Optional[bool] = False
    ) -> AudioDownloadResult:
        if output_dir is None:
            output_dir = get_data_dir()
        if not output_dir:
            output_dir = self.cache_data
        os.makedirs(output_dir, exist_ok=True)

        output_path = os.path.join(output_dir, "%(id)s.%(ext)s")
        info = self._download_auth_aware(video_url, output_path, need_video=False)

        video_id = info.get("id")
        title = info.get("title")
        duration = info.get("duration", 0)
        cover_url = info.get("thumbnail")
        audio_path = os.path.join(output_dir, f"{video_id}.mp3")

        return AudioDownloadResult(
            file_path=audio_path,
            title=title,
            duration=duration,
            cover_url=cover_url,
            platform="bilibili",
            video_id=video_id,
            raw_info=info,
            video_path=None
        )

    def download_video(
        self,
        video_url: str,
        output_dir: Union[str, None] = None,
    ) -> str:
        if output_dir is None:
            output_dir = get_data_dir()

        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, "%(id)s.%(ext)s")
        info = self._download_auth_aware(video_url, output_path, need_video=True)

        video_id = info.get("id")
        video_path = self._pick_video_path(output_dir, video_id)
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"视频文件未找到: {video_path}")
        return video_path

    def delete_video(self, video_path: str) -> str:
        if os.path.exists(video_path):
            os.remove(video_path)
            return f"视频文件已删除: {video_path}"
        return f"视频文件未找到: {video_path}"
