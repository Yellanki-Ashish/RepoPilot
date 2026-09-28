"""Application errors. main.py converts them into clean JSON responses."""


class AppError(Exception):
    status_code = 500
    code = "app_error"

    def __init__(self, message: str, status_code: int | None = None, code: str | None = None):
        super().__init__(message)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        if code is not None:
            self.code = code


class GitHubError(AppError):
    status_code = 502
    code = "github_error"


class OllamaError(AppError):
    status_code = 503
    code = "ollama_error"


class EmbeddingError(AppError):
    status_code = 500
    code = "embedding_error"


class AnalysisError(AppError):
    status_code = 422
    code = "analysis_error"


class NotFoundError(AppError):
    status_code = 404
    code = "not_found"
