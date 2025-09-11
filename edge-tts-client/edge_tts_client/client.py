import asyncio
import io
import logging
from dataclasses import asdict, dataclass
from pathlib import Path
import re

import edge_tts
import simpleaudio
from pydub import AudioSegment

from tts_shared.abstracts import TTSConfig, TTSClient
from tts_shared.exceptions import (
    ConfigError,
    CreateSpeechError,
    PlaySpeechError,
    WriteSpeechFileError,
)

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

SPEECH_FORMAT = "mp3"


@dataclass
class EdgeTTSConfig(TTSConfig):
    """Configuration for edge-tts"""

    voice: str = "en-US-ChristopherNeural"
    rate: str = "+0%"
    volume: str = "-30%"
    pitch: str = "+0Hz"

    def __post_init__(self):
        self.validate_all()

    def validate_all(self):
        """Validate all parameters"""
        if not re.match(r"[a-z]{2}-[A-Z]{2}-", self.voice):
            raise ConfigError(
                f"voice must start with the pattern like aa-AA-, got {self.voice}"
            )
        if not self.rate.endswith("%"):
            raise ConfigError(f"rate must end with %, got {self.rate}")
        if not self.volume.endswith("%"):
            raise ConfigError(f"volume must end with %, got {self.volume}")
        if not self.pitch.endswith("Hz"):
            raise ConfigError(f"pitch must end with Hz, got {self.pitch}")


class EdgeTTSClient(TTSClient):
    config: EdgeTTSConfig

    def __init__(self, config: EdgeTTSConfig = EdgeTTSConfig()) -> None:
        self.config = config
        logger.info(f"Initialized edg-tts client with voice: {self.config.voice}")

    async def create_speech(
        self, text: str, output_file: str | Path | None = None
    ) -> bytes:
        logger.info(f"Creating speech for text length: {len(text)}")
        logger.debug(f"Using config: {self.config}")

        communicate = edge_tts.Communicate(text, **asdict(self.config))
        audio_chunks: list[bytes] = []
        try:
            async for chunk in communicate.stream():
                if chunk["type"] == "audio" and "data" in chunk:
                    audio_chunks.append(chunk["data"])
        except httpx.HTTPStatusError as e:
            logger.error(
                f"Error response {e.response.status_code} while requesting {e.request.url}"
            )
            raise CreateSpeechError(
                f"Speech creation failed. Bad response {e.response.status_code} while requesting {e.request.url}",
                original_exception=e,
            ) from e
        except httpx.RequestError as e:
            logger.error(f"An error occurred while requesting {e.request.url}: {e}")
            raise CreateSpeechError(
                f"Speech creation failed. Bad request for {e.request.url}",
                original_exception=e,
            ) from e
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise CreateSpeechError(
                f"Speech creation failed. Unexpected error {e}",
                original_exception=e,
            ) from e

        # Combine all chunks into one audio file
        if audio_chunks:
            combined_audio_data = b"".join(audio_chunks)

            # Write file if specified
            if output_file is not None:
                try:
                    if isinstance(output_file, str):
                        output_file = Path(output_file)
                        output_file.write_bytes(combined_audio_data)
                except Exception as e:
                    logger.error(
                        f"Failed to write file: {str(output_file)}. error: {e}"
                    )
                    raise WriteSpeechFileError(
                        "Failed to write file: {str(output_file)}. error: {e}",
                        original_exception=e,
                    ) from e

            return combined_audio_data
        return b""

    def update_config(self, **kwargs: EdgeTTSConfig) -> None:
        """Update configuration parameters"""
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
                logger.debug(f"Updated {key} to {value}")

        self.config.validate_all()

    async def play_speech(
        self, speech_bytes: bytes, speech_format: str = SPEECH_FORMAT
    ):
        logger.debug("Playing audio")

        def _play_sync():
            audio = AudioSegment.from_file(
                io.BytesIO(speech_bytes), format=speech_format
            )
            play_obj = simpleaudio.play_buffer(
                audio.raw_data,
                num_channels=audio.channels,
                bytes_per_sample=audio.sample_width,
                sample_rate=audio.frame_rate,
            )
            play_obj.wait_done()

        # Run the blocking operation in a thread
        try:
            await asyncio.to_thread(_play_sync)
        except Exception as e:
            logger.error(f"Failed to play speech. error: {e}")
            raise PlaySpeechError(
                "Failed to play speech. error: {e}",
                original_exception=e,
            ) from e

        logger.debug("Audio playback completed")

    async def create_play_speech(self, text: str) -> None:
        audio_data: bytes | None = await self.create_speech(text)

        if audio_data:
            await self.play_speech(audio_data)


async def main():
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)s] %(name)s: %(funcName)s: line %(lineno)d: %(message)s",
    )
    try:
        tts_client = EdgeTTSClient()
        # Update config
        task1 = asyncio.create_task(tts_client.create_play_speech("hello"))
        await task1
        tts_client.update_config(voice="en-US-MonicaNeural")

        # create speech file
        # speech = await tts_client.create_speech(text="hello", output_file="hello.mp3")

        task2 = asyncio.create_task(tts_client.create_play_speech("hello"))
        await task2
    except (
        ConfigError,
        CreateSpeechError,
        WriteSpeechFileError,
        PlaySpeechError,
        Exception,
    ) as e:
        logger.error(f"{type(e).__name__}:{e}")


if __name__ == "__main__":
    asyncio.run(main())
