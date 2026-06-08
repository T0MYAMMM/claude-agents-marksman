"""FastAPI application factory and router wiring."""

from fastapi import FastAPI

from app.api.v1 import (
    agents,
    artifacts,
    chat,
    commits,
    projects,
    sessions,
    stats,
    webhooks,
)


def create_app() -> FastAPI:
    """Build and configure the FastAPI application."""
    app = FastAPI(
        title="AI Agent Orchestration API",
        version="0.1.0",
        description="Tracks plans, progress, and Markdown artifacts of AI agents.",
    )

    api_prefix = "/api/v1"
    app.include_router(agents.router, prefix=api_prefix)
    app.include_router(projects.router, prefix=api_prefix)
    app.include_router(sessions.router, prefix=api_prefix)
    app.include_router(commits.router, prefix=api_prefix)
    app.include_router(artifacts.router, prefix=api_prefix)
    app.include_router(chat.router, prefix=api_prefix)
    app.include_router(stats.router, prefix=api_prefix)
    app.include_router(webhooks.router, prefix=api_prefix)

    @app.get("/health", tags=["meta"])
    async def health() -> dict[str, str]:
        """Liveness probe."""
        return {"status": "ok"}

    return app


app = create_app()
