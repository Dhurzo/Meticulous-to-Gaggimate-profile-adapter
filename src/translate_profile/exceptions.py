"""Custom exceptions for the profile translator."""


class TranslationError(Exception):
    """Base exception for translation errors."""

    def __init__(self, message: str, details: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details


class FileNotFoundTranslationError(TranslationError):
    """Raised when the input file cannot be found."""

    def __init__(self, file_path: str) -> None:
        self.file_path = file_path
        message = f"Input file not found: {file_path}"
        super().__init__(message, f"File '{file_path}' does not exist or is not accessible.")


class InvalidJSONSyntaxError(TranslationError):
    """Raised when the input file contains invalid JSON syntax."""

    def __init__(self, file_path: str, json_error: str) -> None:
        self.file_path = file_path
        self.json_error = json_error
        message = f"Invalid JSON syntax in {file_path}"
        details = f"JSON parsing error: {json_error}"
        super().__init__(message, details)


class UndefinedVariableError(TranslationError):
    """Raised when a variable reference ($var_name) cannot be resolved."""

    def __init__(self, variable_name: str, location: str) -> None:
        self.variable_name = variable_name
        self.location = location
        message = f"Undefined variable: {variable_name}"
        details = f"Variable '${variable_name}' referenced at {location}"
        super().__init__(message, details)
