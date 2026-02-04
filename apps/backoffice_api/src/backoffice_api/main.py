from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from common.lib.config import get_settings
from common.lib.exceptions import AppError
from common.lib.logging import configure_logging
from backoffice_api.routers.google_oauth import router as google_oauth_router
from backoffice_api.routers.health import router as health_router


def create_app() -> FastAPI:
    configure_logging()
    settings = get_settings()
    app = FastAPI(title="backoffice-api", debug=not settings.is_production)
    app.include_router(health_router, tags=["health"])
    app.include_router(google_oauth_router, prefix="/auth/google", tags=["auth"])

    @app.exception_handler(AppError)
    async def app_error_handler(_: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content=exc.to_dict())

    return app


app = create_app()
