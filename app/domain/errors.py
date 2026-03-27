class DomainError(Exception):
    def __init__(
        self,
        message: str,
        entity: str,
        operation: str,
        status_code: int,
        details: dict | None = None,
    ):
        super().__init__(message)
        self.message = message
        self.entity = entity
        self.operation = operation
        self.status_code = status_code
        self.details = details or {}

    def to_dict(self) -> dict:
        return {
            "message": self.message,
            "entity": self.entity,
            "operation": self.operation,
            "details": self.details,
        }


class DomainNotFoundError(DomainError):
    def __init__(
        self,
        message: str,
        entity: str,
        operation: str,
        details: dict | None = None,
    ):
        super().__init__(
            message=message,
            entity=entity,
            operation=operation,
            status_code=404,
            details=details,
        )


class DomainConflictError(DomainError):
    def __init__(
        self,
        message: str,
        entity: str,
        operation: str,
        details: dict | None = None,
    ):
        super().__init__(
            message=message,
            entity=entity,
            operation=operation,
            status_code=409,
            details=details,
        )


class DomainValidationError(DomainError):
    def __init__(
        self,
        message: str,
        entity: str,
        operation: str,
        details: dict | None = None,
    ):
        super().__init__(
            message=message,
            entity=entity,
            operation=operation,
            status_code=400,
            details=details,
        )


class DomainUnauthorizedError(DomainError):
    def __init__(
        self,
        message: str,
        entity: str,
        operation: str,
        details: dict | None = None,
    ):
        super().__init__(
            message=message,
            entity=entity,
            operation=operation,
            status_code=401,
            details=details,
        )


class DomainDatabaseError(DomainError):
    def __init__(
        self,
        message: str,
        entity: str,
        operation: str,
        details: dict | None = None,
    ):
        super().__init__(
            message=message,
            entity=entity,
            operation=operation,
            status_code=500,
            details=details,
        )
