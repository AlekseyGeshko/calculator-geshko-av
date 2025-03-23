from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import structlog
import json
import asyncio
from logging_conf import configure_logging

logger = configure_logging()
app = FastAPI()


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error("validation_error", detail=str(exc))
    return JSONResponse(
        status_code=400,
        content={"error": "Invalid JSON or missing body"},
    )


@app.post("/calc")
async def calculate(request: Request, float: bool = False):
    logger.info("request_received", method="POST", url=str(request.url), float=float)

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
        return JSONResponse(content=output)

    except Exception as e:
        logger.exception("subprocess_error", error=str(e))
        return JSONResponse(status_code=500, content={"error": f"Subprocess error: {e}"})
