"""describes static types"""

from typing import Optional

from pydantic import BaseModel, Field, model_validator


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
    """Describes a response type for services"""

    ID: str
    Image: str
    Mode: str
    Name: str
    Ports: str
    Replicas: str

    ReplicasIs: Optional[int] = Field(default=None, exclude=True)
    ReplicasShould: Optional[int] = Field(default=None, exclude=True)

    @model_validator(mode="after")
    def parse_replicas(self):
        """split replicas into ints"""
        try:
            is_, should = self.Replicas.split("/")
            self.ReplicasIs = int(is_)
            self.ReplicasShould = int(should)
        except Exception as exc:
            raise ValueError(f"Invalid Replicas format: {self.Replicas}") from exc
        return self
