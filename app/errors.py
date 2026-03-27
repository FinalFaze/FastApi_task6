class InfrastructureError(Exception):
    def __init__(
        self,
        message: str,
        entity: str,
        operation: str,
        details: dict | None = None,
    ):
        super().__init__(message)
        self.message = message
        self.entity = entity
        self.operation = operation
        self.details = details or {}


class InfrastructureNotFoundError(InfrastructureError):
    pass


class InfrastructureConflictError(InfrastructureError):
    pass


class InfrastructureIntegrityError(InfrastructureError):
    pass


class InfrastructureDatabaseError(InfrastructureError):
    pass
