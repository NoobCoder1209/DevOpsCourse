"""Read pod identity from the Kubernetes Downward API.

Falls back to local-friendly values when the env vars aren't set so
`docker compose up` and `pytest` work without any cluster wiring.

Contract with the Helm chart (phase 3): the Deployment MUST inject these
exact env-var names from the Downward API or the localhost fallback values
will silently win — making the demo look broken even when it isn't.

  POD_NAME  ← metadata.name
  POD_IP    ← status.podIP
  NODE_NAME ← spec.nodeName

The `/` route is intentionally non-opaque (it's the demo endpoint and pod
identity is the point). Only `/healthz` must stay information-free.
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
