"""application bootstrap"""

import asyncio
from os import environ

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from src.execute import run_command
from src.types import RequestData, ReturnMessage
from src.validate import ValidateRequest

UVICORN_PORT = int(environ.get("UVICORN_PORT", 8000))
SHOW_DOCS = bool(environ.get("SHOW_DOCS"))

app = FastAPI(
    version="v0.1.0",
    docs_url="/docs" if SHOW_DOCS else None,
    redoc_url="/redoc" if SHOW_DOCS else None,
    openapi_url="/openapi.json" if SHOW_DOCS else None,
)


async def validate_request(
    data: RequestData, request: Request
) -> tuple[str, str]:
    """validate request, return container_name and compose_file"""
    try:
        request_body = await request.body()
        headers = dict(request.headers)

        container_name, compose_file = await ValidateRequest(
            headers, data, request_body
        ).validate()
    except ValueError as err:
        raise HTTPException(status_code=403, detail=str(err)) from err

    return container_name, compose_file


@app.post("/pull")
async def pull_container(data: RequestData, request: Request) -> ReturnMessage:
    """endpoint to pull container"""

    container_name, compose_file = await validate_request(data, request)

    async def execute_docker_commands():
        await run_command(
            f"docker compose -f {compose_file} pull {container_name}"
        )
        await run_command(
            f"docker compose -f {compose_file} up -d {container_name}"
        )

    asyncio.create_task(execute_docker_commands())

    return ReturnMessage(
        message="pulling",
        container_name=container_name,
        compose_file=compose_file,
    )


@app.post("/build")
async def rebuild_container(
    data: RequestData, request: Request
) -> ReturnMessage:
    """endpoint to rebuild container"""

    container_name, compose_file = await validate_request(data, request)

    async def execute_docker_commands():
        await run_command(
            f"docker compose -f {compose_file} up -d --build {container_name}"
        )

    asyncio.create_task(execute_docker_commands())
    return ReturnMessage(
        message="building",
        container_name=container_name,
        compose_file=compose_file,
    )


# entry point
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=UVICORN_PORT)
