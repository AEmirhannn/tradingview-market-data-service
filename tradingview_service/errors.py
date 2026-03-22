class AppError(Exception):
    status_code = 500
    code = "INTERNAL_ERROR"

    def __init__(self, message: str, *, status_code: int = None, code: str = None) -> None:
        super().__init__(message)
        if status_code is not None:
            self.status_code = status_code
        if code is not None:
            self.code = code
        self.message = message


class ValidationError(AppError):
    status_code = 400
    code = "VALIDATION_ERROR"


class AuthenticationError(AppError):
    status_code = 503
    code = "AUTHENTICATION_ERROR"


class UpstreamError(AppError):
    status_code = 502
    code = "UPSTREAM_ERROR"

