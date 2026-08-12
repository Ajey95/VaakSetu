from __future__ import annotations

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.config import Settings
from app.services.call_service import CallService
from app.telephony.twilio_service import TwilioService
from app.websocket.media import media_socket
from app.websocket.ui import ui_socket


def create_app(settings: Settings | None = None) -> FastAPI:
    selected = settings or Settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.settings = selected
        app.state.calls = CallService()
        app.state.twilio = TwilioService(selected)
        yield
        tasks = list(app.state.calls._tasks)
        if tasks:
            import asyncio
            await asyncio.gather(*tasks, return_exceptions=True)

    app = FastAPI(title="AI Sales Coach", version="0.1.0", lifespan=lifespan)
    app.add_middleware(CORSMiddleware, allow_origins=[selected.frontend_url], allow_credentials=True,
                       allow_methods=["*"], allow_headers=["*"])
    app.include_router(router)
    app.websocket("/ws/ui/{call_id}")(ui_socket)
    app.websocket("/ws/media/{call_id}")(media_socket)
    return app


app = create_app()
