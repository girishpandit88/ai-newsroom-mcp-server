from __future__ import annotations

from typing import Dict


def deliver_digest(
    digest: str,
    delivery_channel: str,
    user_id: str,
    dry_run: bool = True,
) -> Dict[str, str]:
    """Deliver a digest to a channel.

    The demo implementation only simulates delivery and returns a preview payload so the
    MCP interaction stays safely side-effect free.
    """

    status = "queued" if not dry_run else "simulated"
    preview = digest.split("\n", 1)[0] if digest else ""
    return {
        "status": status,
        "delivery_channel": delivery_channel,
        "user_id": user_id,
        "preview": preview,
    }
