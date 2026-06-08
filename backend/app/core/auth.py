"""Layered authentication: Tailscale source-network guard + per-agent API key.

Security model: the Tailscale ACL enforces network isolation at the infrastructure
layer, but we re-validate the source IP here so a leaked API key used from off-tailnet
still cannot reach the API. Both checks must pass.
"""

import ipaddress

from fastapi import Depends, Header, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.security import verify_api_key
from app.database import get_db
from app.models.agent import Agent
from app.models.enums import AgentStatus


def require_tailscale(request: Request) -> None:
    """Reject requests whose client IP is outside the configured trusted CIDR(s).

    ``tailscale_cidr`` may hold a comma-separated list, so a containerised frontend on
    the Docker bridge network can be trusted alongside the Tailscale CGNAT range.
    Disabled when the setting is empty (test environments only).
    """
    raw = get_settings().tailscale_cidr
    if not raw:
        return
    networks = [ipaddress.ip_network(c.strip()) for c in raw.split(",") if c.strip()]
    client = request.client
    if client is None:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Unable to determine client address")
    try:
        client_ip = ipaddress.ip_address(client.host)
    except ValueError as exc:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Malformed client address") from exc
    if not any(client_ip in net for net in networks):
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, "Requests must originate from a trusted network"
        )


async def authenticate_agent(
    request: Request,
    x_agent_key: str = Header(..., alias="X-Agent-Key"),
    db: AsyncSession = Depends(get_db),
) -> Agent:
    """Resolve and authenticate the calling agent from the X-Agent-Key header.

    Verifies the Tailscale source first, then matches the key against stored Argon2
    hashes. Returns the authenticated Agent or raises 401/403.
    """
    require_tailscale(request)

    # Argon2 hashes are salted, so we cannot look the key up directly; verify against
    # candidate agents. Volume is low (operator-registered agents), so this is fine.
    result = await db.execute(select(Agent))
    for agent in result.scalars():
        if verify_api_key(x_agent_key, agent.api_key_hash):
            if agent.status == AgentStatus.REVOKED:
                raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Agent key has been revoked")
            return agent

    raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid agent API key")
