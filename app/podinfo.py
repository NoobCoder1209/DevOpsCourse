"""Read pod identity from the Kubernetes Downward API.

Falls back to local-friendly values when the env vars aren't set so
`docker compose up` and `pytest` work without any cluster wiring.
"""

from __future__ import annotations

import os
import socket
from datetime import UTC, datetime


def podinfo() -> dict[str, str]:
    return {
        "podName": os.environ.get("POD_NAME", socket.gethostname()),
        "podIP": os.environ.get("POD_IP", "127.0.0.1"),
        "nodeName": os.environ.get("NODE_NAME", "local-node"),
        "hostname": socket.gethostname(),
        "timestamp": datetime.now(UTC).isoformat(),
    }
