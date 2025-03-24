# server/server.py

import json
import asyncio
import structlog

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi import WebSocket, WebSocketDisconnect

from logging_conf import configure_logging
from .database import init_db, add_record, get_all_records

logger = configure_logging()

app = FastAPI()

# Храним активные WebSocket'ы
connected_clients = set()

@app.on_event("startup")
async def on_startup():
    # При старте приложения инициализируем БД
    logger.info("startup_init_db")
    init_db()

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error("validation_error", detail=str(exc))
    return JSONResponse(
        status_code=400,
        content={"error": "Invalid JSON or missing body"},
    )

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    connected_clients.add(ws)

    # Например, высылаем сразу всю историю из БД
    all_records = get_all_records()  # Возвращает список dict'ов
    await ws.send_json({"history": all_records})

    try:
        while True:
            # Сервер ждёт сообщения (если нужно), иначе просто висит
            msg = await ws.receive_text()
            print("Получено сообщение:", msg)
    except WebSocketDisconnect:
        connected_clients.remove(ws)

@app.post("/calc")
async def calculate(request: Request, float: bool = False):
    logger.info("request_received", method="POST", url=str(request.url), float=float)

    # Проверка контента
    if request.headers.get("content-type") != "application/json":
        logger.error("invalid_content_type", content_type=request.headers.get("content-type"))
        return JSONResponse(status_code=400, content={"error": "Invalid content type, must be application/json"})

    try:
        body = await request.body()
        if not body:
            raise ValueError("Empty body")

        expression = json.loads(body.decode("utf-8"))
        if not isinstance(expression, str):
            expression = str(expression)

    except Exception as e:
        logger.exception("invalid_json", error=str(e))
        return JSONResponse(status_code=400, content={"error": f"Invalid JSON: {e}"})

    # Собираем команду для C-приложения
    cmd = ["./build/app.exe"]
    if float:
        cmd.append("--float")

    logger.info("executing_subprocess_async", cmd=cmd, expression=expression)
    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate(input=expression.encode())

        if process.returncode != 0:
            logger.error("calc_error", stderr=stderr.decode().strip())
            return JSONResponse(
                status_code=500,
                content={"error": stderr.decode().strip()}
            )

        output = stdout.decode().strip()
        logger.info("calc_success", output=output)

        # Сохраняем в БД
        add_record(expression, output, float)

        # Рассылаем всем WebSocket-клиентам (новая корутина)
        asyncio.create_task(broadcast_new_record(expression, output, float))

        return JSONResponse(content=output)

    except Exception as e:
        logger.exception("subprocess_error", error=str(e))
        return JSONResponse(status_code=500, content={"error": f"Subprocess error: {e}"})


async def broadcast_new_record(expression: str, result: str, float_mode: bool):
    """Рассылает всем подключённым WebSocket'ам новое вычисление и очищает мёртвые сокеты."""
    message = {
        "expression": expression,
        "result": result,
        "float_mode": float_mode,
    }
    to_remove = set()

    for ws in connected_clients.copy():
        try:
            await ws.send_json(message)
        except Exception as e:
            logger.warning("websocket_broadcast_failed", error=str(e))
            to_remove.add(ws)

    connected_clients.difference_update(to_remove)
