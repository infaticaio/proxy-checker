import asyncio
import csv
import io

import aiohttp
import uvicorn
from aiohttp import ClientTimeout
from fastapi import FastAPI, Request, UploadFile, File, Form
from starlette.responses import StreamingResponse
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates

from checker import ProxyChecker

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})


@app.post("/")
async def load_file(request: Request, uploaded_file: UploadFile = File(...)):
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "data": (await uploaded_file.read()).decode("utf-8")},
    )


@app.post("/checking/")
async def check_proxies(proxy_list: str = Form(...), threads: int = Form(...)):
    proxy_list = [proxy.strip() for proxy in proxy_list.split("\n")]
    sem = asyncio.Semaphore(value=threads)
    async with aiohttp.ClientSession(
        timeout=ClientTimeout(15), connector=aiohttp.TCPConnector(ssl=False)
    ) as session:
        checker = ProxyChecker(session, sem, set(proxy_list))
        data = await checker.execute()

    fieldnames = ["host", "port", "timeout", "status_code"]
    f = io.StringIO()
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    for i in data:
        if not i:
            continue
        writer.writerow(i)
    f.seek(0)

    return StreamingResponse(
        f,
        media_type="text/csv",
        headers={"Content-Disposition": "inline; filename=result.csv"},
    )


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
