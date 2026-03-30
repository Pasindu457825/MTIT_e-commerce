"""
MongoDB access using Motor (async driver).

We create one `AsyncIOMotorClient` per application lifecycle, ping it on startup,
and expose the database handle via `request.app.state` for route dependencies.
"""

from fastapi import FastAPI, HTTPException, Request, status
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.core.config import settings


async def connect_mongodb(app: FastAPI) -> None:
    """
    Build the Motor client, verify the server is reachable, and attach handles to `app.state`.

    Raises:
        Exception: If the ping command fails (wrong URL, server down, auth failure, etc.).
    """
    client = AsyncIOMotorClient(settings.mongodb_url)
    try:
        # Lightweight no-op command — fails fast if the cluster is not reachable.
        await client.admin.command("ping")
    except Exception:
        # Avoid leaving an open client if validation fails before `app.state` is set.
        client.close()
        raise
    app.state.mongodb_client = client
    app.state.mongodb = client[settings.database_name]


async def disconnect_mongodb(app: FastAPI) -> None:
    """Close sockets when the app shuts down."""
    client: AsyncIOMotorClient | None = getattr(app.state, "mongodb_client", None)
    if client is not None:
        client.close()


def get_database(request: Request) -> AsyncIOMotorDatabase:
    """
    FastAPI dependency: returns the shared database handle.

    Expects `connect_mongodb` to have run during app lifespan.
    """
    db: AsyncIOMotorDatabase | None = getattr(request.app.state, "mongodb", None)
    if db is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="MongoDB is not initialized — application lifespan may not have completed startup.",
        )
    return db
