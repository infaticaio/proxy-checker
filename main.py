import asyncio

import aiohttp
import uvicorn
from aiohttp import ClientTimeout
from fastapi import FastAPI, Request, UploadFile, File, Form
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from aiosocks.connector import ProxyConnector, ProxyClientRequest

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


class Body(BaseModel):
    proxy_list: str
    threads: int


@app.post("/checking/")
async def check_proxies(body: Body):
    proxy_list = [proxy.strip() for proxy in body.proxy_list.split("\n")]
    sem = asyncio.Semaphore(value=body.threads)
    conn = ProxyConnector(remote_resolve=False, verify_ssl=False)

    async with aiohttp.ClientSession(
        timeout=ClientTimeout(15), connector=conn, request_class=ProxyClientRequest
    ) as session:
        checker = ProxyChecker(session, sem, set(proxy_list))
        data = await checker.execute()

    return JSONResponse(data)


if __name__ == "__main__":
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])
    uvicorn.run(app, host="127.0.0.1", port=8000, http="h11", loop="asyncio")
