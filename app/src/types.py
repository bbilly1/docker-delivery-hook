"""describes static types"""

from typing import Optional

from pydantic import BaseModel


class ReturnMessage(BaseModel):
    """describe return message from endpoints"""

    message: str
    container_name: str
    compose_file: str | bool


class RequestData(BaseModel):
    """describes post request data"""

    container_name: str


class SwarmRequestData(BaseModel):
    """describes post request data to swarm endpoint"""

    container_name: str
    with_registry_auth: Optional[bool] = None


class ServiceJsonType(BaseModel):
    """describes a response type for services"""

    ID: str
    Image: str
    Mode: str
    Name: str
    Ports: str
    Replicas: str
