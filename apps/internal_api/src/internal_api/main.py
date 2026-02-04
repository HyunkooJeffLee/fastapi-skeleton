from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from common.lib.config import get_settings
from common.lib.exceptions import AppError
from common.lib.logging import configure_logging
from internal_api.routers.health import router as health_router


def create_app() -> FastAPI:
    configure_logging()
    settings = get_settings()
    app = FastAPI(title="internal-api", debug=not settings.is_production)
    app.include_router(health_router, tags=["health"])

    @app.exception_handler(AppError)
    async def app_error_handler(_: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content=exc.to_dict())

    return app


app = create_app()
