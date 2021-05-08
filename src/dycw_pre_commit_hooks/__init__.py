from __future__ import annotations

from sys import stdout

from loguru import logger


logger.remove()
logger.add(stdout, format="<bold><red>{time:%H:%M:%S}</red>: {message}</bold>")
