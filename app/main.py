import logging
import random
import string
import time

from logging.config import dictConfig
from uuid import uuid4
from async_fastapi_jwt_auth.exceptions import AuthJWTException
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.utils import get_openapi
from fastapi.exceptions import RequestValidationError
from fastapi.encoders import jsonable_encoder

from app.config import settings, LogConfig
from app.routers import user, auth

dictConfig(LogConfig().dict())
logger = logging.getLogger("app")

app = FastAPI()

origins = [
    settings.CLIENT_ORIGIN,
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    req_id = uuid4()
    logger.info(f"rid={req_id} Start Request Path={request.url.path}")
    start_time = time.time()

    try:
        response = await call_next(request)
    except Exception as e:
        logger.error(e.args[0])
        raise e

    process_time = (time.time() - start_time) * 1000
    formatted_process_time = '{0:.2f}'.format(process_time)
    logger.info(f"rid={req_id} | completed_in={formatted_process_time}ms | status_code={response.status_code}")

    return response


@app.exception_handler(AuthJWTException)
def authjwt_exception_handler(request: Request, exc: AuthJWTException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message}
    )


@app.exception_handler(RequestValidationError)
def validation_exception_handler(request: Request, exc: RequestValidationError):
    readable_errors_format = []
    for error in exc.errors():
        readable_errors_format.append({
            "location": error.get("loc", ["", "unknown"])[1],
            "msg": error.get("msg", "")
        })
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=jsonable_encoder({"detail": readable_errors_format})
    )


@app.get('/api/healthchecker')
async def root():
    return {'message': 'Hello World'}


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="Documentation",
        version="1.0.0",
        description="Docs for Authentication App",
        routes=app.routes,
    )

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi
