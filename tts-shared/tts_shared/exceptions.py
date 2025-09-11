"""Exceptions for TTS clients"""


class TTSClientError(Exception):
    def __init__(self, message, original_exception=None):
        super().__init__(message)
        self.original_exception = original_exception


class CreateSpeechError(TTSClientError):
    pass


class WriteSpeechFileError(TTSClientError):
    pass


class PlaySpeechError(TTSClientError):
    pass


class ConfigError(TTSClientError):
    pass
