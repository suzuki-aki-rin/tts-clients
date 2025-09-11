"""Abstract classes for TTS clients"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path


@dataclass
class TTSConfig(ABC):
    @abstractmethod
    def validate_all(self) -> None:
        pass


class TTSClient(ABC):
    def __init__(self, config: TTSConfig):
        self.config = config

    @abstractmethod
    def update_config(self, **kwargs: TTSConfig) -> None:
        pass

    @abstractmethod
    async def create_speech(
        self, text: str, output_file: str | Path | None = None
    ) -> bytes:
        pass

    @abstractmethod
    async def play_speech(self, audio_binary: bytes) -> None:
        pass

    @abstractmethod
    async def create_play_speech(self, text: str) -> None:
        pass
