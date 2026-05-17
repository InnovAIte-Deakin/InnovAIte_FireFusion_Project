"""Task-specific inference entrypoints (misinformation, bushfire, ...)."""

from api.inference.misinformation import predict_misinformation

__all__ = ["predict_misinformation"]