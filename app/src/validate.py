"""validate requests"""

import hashlib
import hmac
import json
import logging
import time
from os import environ

from src.execute import run_command
from src.types import RequestData

logging.basicConfig(level=logging.INFO)


class ValidateRequest:
    """validate"""

    TIME_WINDOW = 300  # 5 minutes
    SECRET_KEY = environ["SECRET_KEY"]

    def __init__(
        self, headers: dict, data: RequestData, request_body: bytes
    ) -> None:
        self.headers = headers
        self.data = data
        self.request_body = request_body

    async def validate(self) -> tuple[str, str]:
        """validate request"""
        self.validate_timestamp()
        self.validate_signature()
        container_name = self.get_container_name()
        await self.validate_container_name(container_name)
        compose_file = await self.get_compose_file(container_name)
        logging.info("validation passed")

        return container_name, compose_file

    def validate_timestamp(self) -> None:
        """raise valueerror on invalid timestamp"""
        timestamp = self.headers.get("x-timestamp")
        if not timestamp:
            raise ValueError("missing x-timestamp in header")

        if not timestamp.isdigit():
            raise ValueError("expected x-timestamp to be epoch int")

        current_time = int(time.time())
        if int(timestamp) - current_time > self.TIME_WINDOW:
            raise ValueError("Request is too old or too far in the future")

    def validate_signature(self):
        """check headers"""
        signature = self.headers.get("x-signature")

        if not signature:
            raise ValueError("missing x-signature in header")

        message = self.request_body + str(self.headers["x-timestamp"]).encode()
        computed_signature = hmac.new(
            key=self.SECRET_KEY.encode(), msg=message, digestmod=hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(computed_signature, signature):
            raise ValueError("invalid signature")

    def get_container_name(self) -> str:
        """extract container name from data"""
        container_name = dict(self.data).get("container_name")
        if not container_name:
            raise ValueError("no container name defined")

        logging.info("got container name %s", container_name)
        return container_name

    async def validate_container_name(self, container_name: str):
        """validate container_name exists"""
        all_containers = await run_command("docker ps -a --format=json")
        for container in all_containers.split("\n"):
            container_json = json.loads(container)
            if container_json.get("Names") == container_name:
                return

        raise ValueError("container_name not found")

    async def get_compose_file(self, container_name: str) -> str:
        """get absolute compose file path from container config"""
        try:
            inspect = await run_command(f"docker inspect {container_name}")
        except Exception as err:
            message = f"couldn't find compose file for {container_name}"
            raise ValueError(message) from err

        inspect_json = json.loads(inspect)
        try:
            compose_file = inspect_json[0]["Config"]["Labels"][
                "com.docker.compose.project.config_files"
            ]
        except (IndexError, KeyError) as err:
            raise ValueError(err) from err

        logging.info("got compose file %s", compose_file)
        return compose_file
