"""describes static types"""

from pydantic import BaseModel


class ReturnMessage(BaseModel):
    """describe return message from endpoints"""

    message: str
    container_name: str
    compose_file: str


class RequestData(BaseModel):
    """describes post request data"""

    container_name: str
