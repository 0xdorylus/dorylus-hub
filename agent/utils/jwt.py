from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi_jwt_auth import AuthJWT
from fastapi_jwt_auth.exceptions import AuthJWTException

from agent.main import app
from agent.config import CONFIG
@AuthJWT.load_config
def get_config():
    """Load AuthJWT settings"""
    return CONFIG


@agent.exception_handler(AuthJWTException)
def jwt_exception_handler(request: Request, exc: AuthJWTException):
    """Returns any authentication failures"""
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})