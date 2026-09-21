import json
from dataclasses import asdict

from app.enmus.task_status_enums import TaskStatus
import os
from typing import Union, Optional

from pydantic import HttpUrl

from app.db.video_task_dao import insert_video_task, delete_task_by_video
from app.downloaders.base import Downloader
from app.downloaders.bilibili_downloader import BilibiliDownloader
from app.downloaders.douyin_downloader import DouyinDownloader
from app.downloaders.youtube_downloader import YoutubeDownloader
from app.gpt.base import GPT
from app.gpt.deepseek_gpt import DeepSeekGPT
from app.gpt.gpt_factory import GPTFactory
from app.gpt.openai_gpt import OpenaiGPT
from app.gpt.qwen_gpt import QwenGPT
from app.models.gpt_model import GPTSource
from app.models.model_config import ModelConfig
from app.models.notes_model import NoteResult
from app.models.notes_model import AudioDownloadResult
from app.enmus.note_enums import DownloadQuality
from app.models.transcriber_model import TranscriptResult, TranscriptSegment

from app.services.provider import ProviderService
from app.services.cookie import DownloadAuthError
from app.transcriber.base import Transcriber
from app.transcriber.transcriber_provider import get_transcriber,_transcribers
from app.transcriber.whisper import WhisperTranscriber
import re

from app.utils.note_helper import replace_content_markers
from app.utils.video_helper import generate_screenshot

# from app.services.whisperer import transcribe_audio
# from app.services.gpt import summarize_text
from dotenv import load_dotenv
from app.utils.logger import get_logger
from events import transcription_finished

logger = get_logger(__name__)
load_dotenv()
api_path = os.getenv("API_BASE_URL", "http://localhost")
BACKEND_PORT= os.getenv("BACKEND_PORT", 8000)

BACKEND_BASE_URL = f"{api_path}:{BACKEND_PORT}"
output_dir = os.getenv('OUT_DIR','./static/screenshots')
image_base_url = os.getenv('IMAGE_BASE_URL','/static/screenshots')
logger.info("starting up")

NOTE_OUTPUT_DIR = "note_results"

class NoteGenerator:
    def __init__(self):
        self.model_size: str = 'base'
        self.device: Union[str, None] = None
        self.transcriber_type = os.getenv('TRANSCRIBER_TYPE','fast-whisper')
        self.transcriber = self.get_transcriber()
        self.video_path = None
        logger.info("初始化NoteGenerator")

    import logging

    logger = logging.getLogger(__name__)

    @staticmethod
    def update_task_status(task_id: str, status: Union[str, TaskStatus], message: Optional[str] = None):
        os.makedirs(NOTE_OUTPUT_DIR, exist_ok=True)
        path = os.path.join(NOTE_OUTPUT_DIR, f"{task_id}.status.json")
        content = {"status": status.value if isinstance(status, TaskStatus) else status}
        if message:
            content["message"] = message
        with open(path, "w", encoding="utf-8") as f:
            json.dump(content, f, ensure_ascii=False, indent=2)

    def get_gpt(self, model_name: str = None, provider_id: str = None) -> GPT:
        provider = ProviderService.get_provider_by_id(provider_id)
        if not provider:
            logger.error(f"[get_gpt] 未找到对应的模型供应商: provider_id={provider_id}")
            raise ValueError(f"未找到对应的模型供应商: provider_id={provider_id}")

        gpt = GPTFactory().from_config(
            ModelConfig(
                api_key=provider.get('api_key'),
                base_url=provider.get('base_url'),
                model_name=model_name,
                provider=provider.get('type'),
                name=provider.get('name')
            )
        )
        return gpt

    def get_downloader(self, platform: str) -> Downloader:
        if platform == "bilibili":
            logger.info("下载 Bilibili 平台视频")
            return BilibiliDownloader()
        elif platform == "youtube":
            logger.info("下载 YouTube 平台视频")
            return YoutubeDownloader()
        elif platform == 'douyin':
            logger.info("下载 Douyin 平台视频")
            return DouyinDownloader()
        else:
            logger.warning("不支持的平台")
            raise ValueError(f"不支持的平台：{platform}")

    def get_transcriber(self) -> Transcriber:
        '''

        :param transcriber: 选择的转义器
        :return:
        '''
        if self.transcriber_type in _transcribers.keys():
            logger.info(f"使用{self.transcriber_type}转义器")
            return get_transcriber(transcriber_type=self.transcriber_type)
        else:
            logger.warning("不支持的转义器")
            raise ValueError(f"不支持的转义器：{self.transcriber}")

    def save_meta(self, video_id, platform, task_id):
        logger.info(f"记录已经生成的数据信息")
        insert_video_task(video_id=video_id, platform=platform, task_id=task_id)

    def insert_screenshots_into_markdown(self, markdown: str, video_path: str, image_base_url: str,
                                         output_dir: str,_format:list) -> str:
        """
        扫描 markdown 中的 *Screenshot-xx:xx，生成截图并插入 markdown 图片
        :param markdown:
        :param image_base_url: 最终返回给前端的路径前缀（如 /static/screenshots）
        """
        matches = self.extract_screenshot_timestamps(markdown)
        new_markdown = markdown
        print(f"匹配到的截图：{matches}")
        logger.info(f"开始为笔记生成截图")
        try:
            for idx, (marker, ts) in enumerate(matches):
                image_path = generate_screenshot(video_path, output_dir, ts, idx)
                image_relative_path = os.path.join(image_base_url, os.path.basename(image_path)).replace("\\", "/")
                image_url = f"{BACKEND_BASE_URL.rstrip('/')}/{image_relative_path.lstrip('/')}"
                replacement = f"![]({image_url})"
                new_markdown = new_markdown.replace(marker, replacement, 1)
            print(f"替换后的 markdown：{new_markdown}")

            return new_markdown
        except Exception as e:
            logger.error(f"截图生成失败：{e}")
            raise e

    @staticmethod
    def delete_note(video_id: str, platform: str):
        logger.info(f"删除生成的笔记记录")
        return delete_task_by_video(video_id, platform)

    import re

    def extract_screenshot_timestamps(self, markdown: str) -> list[tuple[str, int]]:
        """
        从 Markdown 中提取 Screenshot 时间标记（如 *Screenshot-03:39 或 Screenshot-[03:39]），
        并返回匹配文本和对应时间戳（秒）
        """
        logger.info(f"开始提取截图时间标记")
        pattern = r"(?:\*Screenshot-(\d{2}):(\d{2})|Screenshot-\[(\d{2}):(\d{2})\])"
        matches = list(re.finditer(pattern, markdown))
        results = []
        for match in matches:
            mm = match.group(1) or match.group(3)
            ss = match.group(2) or match.group(4)
            total_seconds = int(mm) * 60 + int(ss)
            results.append((match.group(0), total_seconds))
        return results

    def generate(
            self,
            video_url: Union[str, HttpUrl],
            platform: str,
            quality: DownloadQuality = DownloadQuality.medium,
            task_id: Union[str, None] = None,
            model_name: str = None,
            provider_id: str = None,
            link: bool = False,
            screenshot: bool = False,
            _format: list = None,
            style: str = None,
            extras: str = None,
            path: Union[str, None] = None
    ) -> NoteResult:
        try:
            logger.info(f"🎯 开始解析并生成笔记，task_id={task_id}")
            self.update_task_status(task_id, TaskStatus.PARSING)
            _path=''
            downloader = self.get_downloader(platform)
            gpt = self.get_gpt(model_name=model_name, provider_id=provider_id)

            audio_cache_path = os.path.join(NOTE_OUTPUT_DIR, f"{task_id}_audio.json")
            transcript_cache_path = os.path.join(NOTE_OUTPUT_DIR, f"{task_id}_transcript.json")
            markdown_cache_path = os.path.join(NOTE_OUTPUT_DIR, f"{task_id}_markdown.md")

            # -------- 1. 下载音频 --------
            try:
                self.update_task_status(task_id, TaskStatus.DOWNLOADING)
                if os.path.exists(audio_cache_path):
                    logger.info(f"检测到已有音频缓存，直接读取，task_id={task_id}")
                    with open(audio_cache_path, "r", encoding="utf-8") as f:
                        audio_data = json.load(f)
                    audio = AudioDownloadResult(**audio_data)
                else:
                    if 'screenshot' in _format:
                        video_path = downloader.download_video(video_url)
                        self.video_path = video_path
                        logger.info(f"成功下载视频文件: {video_path}")
                    screenshot= 'screenshot' in _format
                    audio: AudioDownloadResult = downloader.download(
                        video_url=video_url,
                        quality=quality,
                        output_dir=path,
                        need_video=screenshot
                    )
                    _path=audio.raw_info.get('path')
                    with open(audio_cache_path, "w", encoding="utf-8") as f:
                        json.dump(asdict(audio), f, ensure_ascii=False, indent=2)
                    logger.info(f"音频下载并缓存成功，task_id={task_id}")
            except Exception as e:
                logger.error(f"❌ 下载音频失败，task_id={task_id}，错误信息：{e}")
                msg = str(e) if isinstance(e, DownloadAuthError) else f"下载音频失败：{e}"
                self.update_task_status(task_id, TaskStatus.FAILED, message=msg)
                raise e

            # -------- 2. 转写文字 --------
            try:
                self.update_task_status(task_id, TaskStatus.TRANSCRIBING)
                if os.path.exists(transcript_cache_path):
                    logger.info(f"检测到已有转写缓存，直接读取，task_id={task_id}")
                    try:
                        with open(transcript_cache_path, "r", encoding="utf-8") as f:
                            transcript_data = json.load(f)
                        transcript = TranscriptResult(
                            language=transcript_data["language"],
                            full_text=transcript_data["full_text"],
                            segments=[TranscriptSegment(**seg) for seg in transcript_data["segments"]]
                        )
                    except (json.JSONDecodeError, KeyError) as e:
                        logger.warning(f"⚠️ 读取转录缓存失败，重新转录，task_id={task_id}，错误信息：{e}")
                        transcript: TranscriptResult = self.transcriber.transcript(file_path=audio.file_path)
                        with open(transcript_cache_path, "w", encoding="utf-8") as f:
                            json.dump(asdict(transcript), f, ensure_ascii=False, indent=2)
                else:
                    transcript: TranscriptResult = self.transcriber.transcript(file_path=audio.file_path)
                    with open(transcript_cache_path, "w", encoding="utf-8") as f:
                        json.dump(asdict(transcript), f, ensure_ascii=False, indent=2)
                    logger.info(f"文字转写并缓存成功，task_id={task_id}")
            except Exception as e:
                logger.error(f"❌ 转写文字失败，task_id={task_id}，错误信息：{e}")
                self.update_task_status(task_id, TaskStatus.FAILED, message=f"转写文字失败：{e}")
                raise e

            # -------- 3. 总结内容 --------
            try:
                self.update_task_status(task_id, TaskStatus.SUMMARIZING)
                if os.path.exists(markdown_cache_path):
                    logger.info(f"检测到已有总结缓存，直接读取，task_id={task_id}")
                    with open(markdown_cache_path, "r", encoding="utf-8") as f:
                        markdown = f.read()
                else:
                    source = GPTSource(
                        title=audio.title,
                        segment=transcript.segments,
                        tags=audio.raw_info.get('tags'),
                        screenshot=screenshot,
                        link=link,
                        _format=_format,
                        style=style,
                        extras=extras
                    )

                    markdown: str = gpt.summarize(source)
                    with open(markdown_cache_path, "w", encoding="utf-8") as f:
                        f.write(markdown)
                    logger.info(f"GPT总结并缓存成功，task_id={task_id}")
            except Exception as e:
                logger.error(f"❌ 总结内容失败，task_id={task_id}，错误信息：{e}")
                self.update_task_status(task_id, TaskStatus.FAILED, message=f"总结内容失败：{e}")
                raise e

            # -------- 4. 插入截图 --------
            if _format and 'screenshot' in _format:
                try:
                    markdown = self.insert_screenshots_into_markdown(markdown, self.video_path, image_base_url, output_dir,_format)
                except Exception as e:
                    logger.warning(f"⚠️ 插入截图失败，跳过处理，task_id={task_id}，错误信息：{e}")
            if _format and 'link' in _format:
                try:
                    markdown = replace_content_markers(markdown, video_id=audio.video_id,platform=platform)
                except Exception as e:
                    logger.warning(f"⚠️ 插入链接失败，跳过处理，task_id={task_id}，错误信息：{e}")
                # 注意：截图失败不终止整体流程

            # -------- 5. 保存数据库记录 --------
            self.update_task_status(task_id, TaskStatus.SAVING)
            self.save_meta(video_id=audio.video_id, platform=platform, task_id=task_id)

            # -------- 6. 完成 --------
            self.update_task_status(task_id, TaskStatus.SUCCESS)
            logger.info(f"✅ 笔记生成成功，task_id={task_id}")
            transcription_finished.send({
                "file_path": audio.file_path,
            })
            return NoteResult(
                markdown=markdown,
                transcript=transcript,
                audio_meta=audio
            )

        except DownloadAuthError as e:
            logger.error(f"❌ 下载需要登录/Cookie，task_id={task_id}，{e}")
            self.update_task_status(task_id, TaskStatus.FAILED, message=str(e))
            raise RuntimeError(str(e)) from e
        except Exception as e:
            logger.error(f"❌ 笔记生成流程异常终止，task_id={task_id}，错误信息：{e}")
            cause = e
            friendly = None
            seen = set()
            while cause is not None and id(cause) not in seen:
                seen.add(id(cause))
                if isinstance(cause, DownloadAuthError):
                    friendly = str(cause)
                    break
                cause = cause.__cause__ or cause.__context__
            msg = friendly or str(e)
            self.update_task_status(task_id, TaskStatus.FAILED, message=msg)
            raise RuntimeError(msg) from e




