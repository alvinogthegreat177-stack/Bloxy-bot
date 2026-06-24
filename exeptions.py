class ValidationError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class AuthenticationError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)
