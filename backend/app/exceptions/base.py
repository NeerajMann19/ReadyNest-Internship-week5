"""
Application-wide custom exception classes.
"""

class PrismIQException(Exception):
    """Base exception class for all custom application errors."""
    def __init__(self, message: str, status_code: int = 500, errors: list = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.errors = errors or []


class NotFoundException(PrismIQException):
    """Exception raised when a requested resource is not found."""
    def __init__(self, message: str = "Resource not found", errors: list = None):
        super().__init__(message, status_code=404, errors=errors)


class BadRequestException(PrismIQException):
    """Exception raised when client requests are malformed or invalid."""
    def __init__(self, message: str = "Bad request", errors: list = None):
        super().__init__(message, status_code=400, errors=errors)


class DatabaseException(PrismIQException):
    """Exception raised when database operations fail."""
    def __init__(self, message: str = "Database operation failed", errors: list = None):
        super().__init__(message, status_code=500, errors=errors)
