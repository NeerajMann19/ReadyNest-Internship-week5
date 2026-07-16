"""
FastAPI custom exception handler registration.
"""
import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.exceptions.base import PrismIQException
from app.core.config import settings

logger = logging.getLogger(__name__)

async def prismiq_exception_handler(request: Request, exc: PrismIQException) -> JSONResponse:
    """
    Handles custom application-level exceptions.
    """
    logger.error("Application error: %s (Status: %d)", exc.message, exc.status_code)
    
    # In local environment, pass down custom errors list
    errors_list = exc.errors if settings.ENVIRONMENT == "local" else []
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "message": exc.message,
            "data": None,
            "errors": errors_list
        }
    )

async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Catch-all exception handler for unexpected server errors.
    Hides internal details from clients unless running locally.
    """
    logger.error("Unhandled server exception: %s", str(exc), exc_info=True)
    
    errors_list = [str(exc)] if settings.ENVIRONMENT == "local" else []
    
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "An unexpected server error occurred",
            "data": None,
            "errors": errors_list
        }
    )

def register_exception_handlers(app: FastAPI) -> None:
    """
    Registers the custom exception handlers onto the FastAPI application.
    """
    app.add_exception_handler(PrismIQException, prismiq_exception_handler)
    app.add_exception_handler(Exception, global_exception_handler)
