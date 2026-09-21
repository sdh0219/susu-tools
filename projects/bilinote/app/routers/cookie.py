import os

from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from app.services.cookie import CookieService, DownloadAuthError
from app.utils.response import ResponseWrapper as R

router = APIRouter()

COOKIE_PAGE_PATHS = [
    os.path.join("dist", "cookie.html"),
    os.path.join("static", "cookie.html"),
]


class CookieSaveRequest(BaseModel):
    cookie_text: str


@router.get("/cookie", response_class=HTMLResponse)
def cookie_settings_page():
    for path in COOKIE_PAGE_PATHS:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return HTMLResponse(content=f.read())
    return HTMLResponse(
        content="<h3>cookie.html 未找到</h3><p>请使用 API：GET/POST /api/cookie/bilibili</p>",
        status_code=404,
    )


@router.get("/api/cookie/{platform}")
def get_cookie_status(platform: str):
    try:
        return R.success(data=CookieService.get_status(platform))
    except Exception as e:
        return R.error(msg=str(e))


@router.post("/api/cookie/{platform}")
def save_cookie(platform: str, data: CookieSaveRequest):
    try:
        if not data.cookie_text or not data.cookie_text.strip():
            return R.error(msg="Cookie 内容不能为空")
        status = CookieService.save_cookie(platform, data.cookie_text)
        return R.success(msg="Cookie 已保存", data=status)
    except DownloadAuthError as e:
        return R.error(msg=str(e))
    except ValueError as e:
        return R.error(msg=str(e))
    except Exception as e:
        return R.error(msg=f"保存失败：{e}")


@router.delete("/api/cookie/{platform}")
def clear_cookie(platform: str):
    try:
        status = CookieService.clear_cookie(platform)
        return R.success(msg="Cookie 已清除", data=status)
    except Exception as e:
        return R.error(msg=f"清除失败：{e}")
