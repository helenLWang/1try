"""Parse Kafka movielog lines into structured events.

The stream mixes three request types (see the I2 assignment):

    <time>,<userid>,GET /data/m/<movieid>/<minute>.mpg
    <time>,<userid>,GET /rate/<movieid>=<rating>
    <time>,<userid>,GET /create_account

Lines that do not match are ignored (recommendation-request logs, noise).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

WATCH_RE = re.compile(
    r"^(?P<ts>[^,]+),(?P<uid>\d+),GET /data/m/(?P<mid>[^/]+)/(?P<minute>\d+)\.mpg"
)
RATE_RE = re.compile(
    r"^(?P<ts>[^,]+),(?P<uid>\d+),GET /rate/(?P<mid>[^=]+)=(?P<rating>-?\d+)"
)
CREATE_RE = re.compile(
    r"^(?P<ts>[^,]+),(?P<uid>\d+),GET /create_account"
)


@dataclass(frozen=True)
class WatchEvent:
    timestamp: str
    user_id: int
    movie_id: str
    minute: int


@dataclass(frozen=True)
class RateEvent:
    timestamp: str
    user_id: int
    movie_id: str
    rating: int


@dataclass(frozen=True)
class CreateAccountEvent:
    timestamp: str
    user_id: int


def parse_line(line: str) -> Optional[WatchEvent | RateEvent | CreateAccountEvent]:
    """Parse one Kafka value. Returns None for unrecognized lines."""
    text = line.strip()
    if not text:
        return None

    match = WATCH_RE.match(text)
    if match:
        return WatchEvent(
            timestamp=match.group("ts"),
            user_id=int(match.group("uid")),
            movie_id=match.group("mid"),
            minute=int(match.group("minute")),
        )

    match = RATE_RE.match(text)
    if match:
        return RateEvent(
            timestamp=match.group("ts"),
            user_id=int(match.group("uid")),
            movie_id=match.group("mid"),
            rating=int(match.group("rating")),
        )

    match = CREATE_RE.match(text)
    if match:
        return CreateAccountEvent(
            timestamp=match.group("ts"),
            user_id=int(match.group("uid")),
        )

    return None
