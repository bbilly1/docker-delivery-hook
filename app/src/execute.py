"""execute commands"""

import asyncio
import logging

logging.basicConfig(level=logging.INFO)


async def run_command(command):
    """execute command async"""
    # pylint: disable=broad-exception-raised
    logging.info("Running command: %s", command)
    process = await asyncio.create_subprocess_shell(
        command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()

    if process.returncode != 0:
        logging.error("Command failed: %s", stderr.decode())
        raise Exception(f"Command failed: {stderr.decode()}")

    logging.info("Command succeeded: %s", command)
    return stdout.decode()
