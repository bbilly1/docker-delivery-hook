"""application bootstrap"""

import asyncio
import logging
from os import environ

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from src.execute import run_command
from src.types import (
    RequestData,
    ReturnMessage,
    ServiceJsonType,
    SwarmRequestData,
)
from src.validate import ValidateRequest

logging.basicConfig(level=logging.INFO)

UVICORN_PORT = int(environ.get("UVICORN_PORT", 8000))
SHOW_DOCS = bool(environ.get("SHOW_DOCS"))
HOOK_VERSION = environ.get("HOOK_VERSION", "dev")

app = FastAPI(
    version=HOOK_VERSION,
    docs_url="/docs" if SHOW_DOCS else None,
    redoc_url="/redoc" if SHOW_DOCS else None,
    openapi_url="/openapi.json" if SHOW_DOCS else None,
)


async def validate_request(data: RequestData, request: Request) -> tuple[str, str]:
    """validate request, return container_name and compose_file"""
    try:
        request_body = await request.body()
        headers = dict(request.headers)

        container_name, compose_file = await ValidateRequest(headers, request_body).validate(data)
    except ValueError as err:
        raise HTTPException(status_code=403, detail=str(err)) from err

    return container_name, compose_file


async def validate_swarm_request(data: SwarmRequestData, request: Request) -> list[ServiceJsonType]:
    """validate request, return container_name and compose_file"""
    try:
        request_body = await request.body()
        headers = dict(request.headers)

        services_json: list[ServiceJsonType] = await ValidateRequest(headers, request_body).validate_swarm(data)
    except ValueError as err:
        raise HTTPException(status_code=403, detail=str(err)) from err

    return services_json


@app.post("/pull")
async def pull_container(data: RequestData, request: Request) -> ReturnMessage:
    """endpoint to pull container"""

    container_name, compose_file = await validate_request(data, request)

    async def execute_docker_commands():
        await run_command(f"docker compose -f {compose_file} pull {container_name}")
        await run_command(f"docker compose -f {compose_file} up -d {container_name}")

    asyncio.create_task(execute_docker_commands())

    return ReturnMessage(
        message="pulling",
        container_name=container_name,
        compose_file=compose_file,
    )


@app.post("/build")
async def rebuild_container(data: RequestData, request: Request) -> ReturnMessage:
    """endpoint to rebuild container"""

    container_name, compose_file = await validate_request(data, request)

    async def execute_docker_commands():
        await run_command(f"docker compose -f {compose_file} up -d --build {container_name}")

    asyncio.create_task(execute_docker_commands())
    return ReturnMessage(
        message="building",
        container_name=container_name,
        compose_file=compose_file,
    )


@app.post("/swarm")
async def rebuild_sarm_container(data: SwarmRequestData, request: Request) -> ReturnMessage:
    """endpoint for swarm container rebuild"""

    services_json: list[ServiceJsonType] = await validate_swarm_request(data, request)
    registry_auth = "--with-registry-auth" if data.with_registry_auth else ""

    async def execute_docker_commands():
        for service_json in services_json:
            image = service_json.Image
            name = service_json.Name
            replicas_is = service_json.ReplicasIs
            detach = "true" if replicas_is == 0 else "false"

            await run_command(
                ("docker service update " f"--image {image} {registry_auth} " f"--force {name} --detach={detach}")
            )

    container_name = services_json[0].Name if len(services_json) == 1 else services_json[0].Image

    asyncio.create_task(execute_docker_commands())
    return ReturnMessage(
        message="pulling",
        container_name=container_name,
        compose_file=False,
    )


# entry point
if __name__ == "__main__":
    logging.info("Starting Docker Delivery Hook: %s", HOOK_VERSION)
    uvicorn.run(app, host="0.0.0.0", port=UVICORN_PORT)
