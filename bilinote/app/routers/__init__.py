import os

from fastapi import APIRouter
from starlette.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
index = APIRouter()
dist_dir = "dist"
@index.get("/", response_class=HTMLResponse)

async def read_index():
    try:
        print('请求页面')
        with open(os.path.join(dist_dir, "index.html"), "r", encoding="utf-8") as file:
            return HTMLResponse(content=file.read())
    except FileNotFoundError:
        return HTMLResponse(content="index.html not found", status_code=404)