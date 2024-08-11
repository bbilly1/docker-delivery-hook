"""test validator"""

import hashlib
import hmac
import time
from os import environ
from unittest.mock import patch

import pytest
from src.types import RequestData
from src.validate import ValidateRequest

SECRET_KEY = environ["SECRET_KEY"]


def generate_signature(secret_key, body, timestamp):
    """helper function to generate a valid HMAC signature"""
    message = body + str(timestamp).encode()
    return hmac.new(
        secret_key.encode(), msg=message, digestmod=hashlib.sha256
    ).hexdigest()


def test_validate_timestamp_valid():
    """expected timestamp"""
    headers = {"x-timestamp": str(int(time.time()))}
    request_body = b""
    json_data = {}

    validator = ValidateRequest(headers, json_data, request_body)
    try:
        validator.validate_timestamp()
    except ValueError:
        pytest.fail("Unexpected ValueError raised")


def test_validate_timestamp_missing():
    """no timestamp"""
    headers = {}
    request_body = b""
    json_data = {}

    validator = ValidateRequest(headers, json_data, request_body)
    with pytest.raises(ValueError, match="missing x-timestamp in header"):
        validator.validate_timestamp()


def test_validate_timestamp_invalid_format():
    """not a real time stamp"""
    headers = {"x-timestamp": "invalid-timestamp"}
    request_body = b""
    json_data = {}

    validator = ValidateRequest(headers, json_data, request_body)
    with pytest.raises(
        ValueError, match="expected x-timestamp to be epoch int"
    ):
        validator.validate_timestamp()


def test_validate_timestamp_out_of_range():
    """future timestamp"""
    future_timestamp = int(time.time()) + 1000
    headers = {"x-timestamp": str(future_timestamp)}
    request_body = b""
    json_data = {}

    validator = ValidateRequest(headers, json_data, request_body)
    with pytest.raises(
        ValueError, match="Request is too old or too far in the future"
    ):
        validator.validate_timestamp()


def test_validate_signature_valid():
    """expected signature"""
    timestamp = str(int(time.time()))
    request_body = b"test body"
    headers = {
        "x-timestamp": timestamp,
        "x-signature": generate_signature(SECRET_KEY, request_body, timestamp),
    }
    json_data = {}

    with patch.dict("os.environ", {"SECRET_KEY": SECRET_KEY}):
        validator = ValidateRequest(headers, json_data, request_body)
        try:
            validator.validate_signature()
        except ValueError:
            pytest.fail("Unexpected ValueError raised")


def test_validate_signature_missing():
    """no signature"""
    timestamp = str(int(time.time()))
    request_body = b"test body"
    headers = {"x-timestamp": timestamp}
    json_data = {}

    validator = ValidateRequest(headers, json_data, request_body)
    with pytest.raises(ValueError, match="missing x-signature in header"):
        validator.validate_signature()


def test_validate_signature_invalid():
    """invalid signature"""
    timestamp = str(int(time.time()))
    request_body = b"test body"
    headers = {"x-timestamp": timestamp, "x-signature": "invalid-signature"}
    json_data = {}

    with patch.dict("os.environ", {"SECRET_KEY": SECRET_KEY}):
        validator = ValidateRequest(headers, json_data, request_body)
        with pytest.raises(ValueError, match="invalid signature"):
            validator.validate_signature()


def test_get_container_name_valid():
    """expected container_name in json_data"""
    headers = {}
    request_body = b""
    data = RequestData(container_name="test-container")

    validator = ValidateRequest(headers, data, request_body)
    container_name = validator.get_container_name()

    assert container_name == "test-container"
