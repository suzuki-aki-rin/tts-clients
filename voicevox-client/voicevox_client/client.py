import asyncio

import io
import logging
import re
import wave
from dataclasses import dataclass
from pathlib import Path

import httpx
import simpleaudio as sa

from tts_shared.abstracts import (
    TTSClient,
    TTSConfig,
)
from tts_shared.exceptions import (
    TTSClientError,
    ConfigError,
    CreateSpeechError,
    PlaySpeechError,
    WriteSpeechFileError,
)

#  SECTION:=============================================================
#            Logger
#  =====================================================================

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


#  SECTION:=============================================================
#            Exception class
#  =====================================================================


class GenerateQueryError(TTSClientError):
    pass


#  SECTION:=============================================================
#         Config class
#  =====================================================================


@dataclass
class VoicevoxConfig(TTSConfig):
    """Configuration for edge-tts"""

    speaker: int = 3
    speed: float = 1.0
    pitch: float = 0.0
    intonation: float = 1.0
    volume: float = 1.0
    host: str = "localhost"
    port: int = 50021
    base_url: str = f"http://{host}:{port}/"

    def __post_init__(self):
        self.validate_all()

    def validate_all(self):
        """Validate all parameters"""
        if self.host != "localhost" and not re.match(
            r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}", self.host
        ):
            raise ConfigError(
                f"host must be localhost or the pattern like 0.0.0.0, got {self.host}"
            )
        if self.port < 1000 or self.port > 99999:
            raise ConfigError(f"port must be 4 or 5 digit, got {self.port}")


#  SECTION:=============================================================
#            Main class
#  =====================================================================


class VoicevoxClient(TTSClient):
    """Class for text to speech by Voicevox"""

    config: VoicevoxConfig

    def __init__(self, config: VoicevoxConfig = VoicevoxConfig()):
        super().__init__(config)

    #  SECTION:=============================================================
    #            Functions, helper
    #  =====================================================================

    async def _generate_query(self, text: str) -> dict[str, dict]:
        params = {
            "text": text,
            "speaker": self.config.speaker,
        }

        try:
            async with httpx.AsyncClient() as client:
                query_response = await client.post(
                    f"{self.config.base_url}audio_query",
                    params=params,
                )
                query_response.raise_for_status()

                # Modify query_response by using self. parameters
                query_data = query_response.json()
                query_data["speedScale"] = self.config.speed
                query_data["witchScale"] = self.config.pitch
                query_data["intonationScale"] = self.config.intonation
                query_data["volumeScale"] = self.config.volume

                query = {"params": params, "json": query_data}
                # query = {"params": params, "json": json.dumps(query_data)}
                return query

        except httpx.HTTPStatusError as e:
            logger.error(
                f"Error response {e.response.status_code} while requesting {e.request.url}"
            )
            raise GenerateQueryError(
                f"Query generation failed. Bad response {e.response.status_code} while requesting {e.request.url}",
                original_exception=e,
            ) from e
        except httpx.RequestError as e:
            logger.error(f"An error occurred while requesting {e.request.url}: {e}")
            raise GenerateQueryError(
                f"Query generation failed. Bad request for {e.request.url}",
                original_exception=e,
            ) from e
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise GenerateQueryError(
                f"Query generation failed. Unexpected error {e}",
                original_exception=e,
            ) from e

    async def _synthesize_speech(
        self, query: dict[str, dict], output_file: str | Path | None = None
    ) -> bytes:
        try:
            async with httpx.AsyncClient() as client:
                synthesis = await client.post(
                    f"{self.config.base_url}synthesis",
                    headers={"Content-Type": "application/json"},
                    params=query["params"],
                    json=query["json"],
                )

        except httpx.HTTPStatusError as e:
            logger.error(
                f"Error response {e.response.status_code} while requesting {e.request.url}"
            )
            raise CreateSpeechError(
                f"Speech synthesis failed. Bad response {e.response.status_code} while requesting {e.request.url}",
                original_exception=e,
            ) from e
        except httpx.RequestError as e:
            logger.error(f"An error occurred while requesting {e.request.url}: {e}")
            raise CreateSpeechError(
                f"Speech synthesis failed. Bad request for {e.request.url}",
                original_exception=e,
            ) from e
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise CreateSpeechError(
                f"Speech synthesis failed. Unexpected error {e}",
                original_exception=e,
            ) from e
        # Write file if specified
        if output_file is not None:
            try:
                if isinstance(output_file, str):
                    output_file = Path(output_file)
                output_file.write_bytes(synthesis.content)
                logger.info(f"Create a speech file: {str(output_file)}.")
            except Exception as e:
                logger.error(f"Failed to write file: {str(output_file)}. error: {e}")
                raise WriteSpeechFileError(
                    "Failed to write file: {str(output_file)}. error: {e}",
                    original_exception=e,
                ) from e

        return synthesis.content

    #  SECTION:=============================================================
    #            Functions, Main
    #  =====================================================================

    def update_config(self, **kwargs: VoicevoxConfig) -> None:
        """Update configuration parameters"""
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
                logger.debug(f"Updated {key} to {value}")

        self.config.validate_all()

    async def create_speech(
        self, text: str, output_file: str | Path | None = None
    ) -> bytes:
        query = await self._generate_query(text)
        audio = await self._synthesize_speech(query, output_file)
        return audio

    async def play_speech(self, speech_bytes: bytes) -> None:
        # Use BytesIO to treat bytes as a file object
        def _play_sync():
            audio_io = io.BytesIO(speech_bytes)

            # Open the audio bytes as a wave file
            with wave.open(audio_io, "rb") as wave_read:
                # Extract audio parameters
                audio_data = wave_read.readframes(wave_read.getnframes())
                num_channels = wave_read.getnchannels()
                bytes_per_sample = wave_read.getsampwidth()
                sample_rate = wave_read.getframerate()

            # Create a WaveObject from the audio data and parameters
            wave_obj = sa.WaveObject(
                audio_data, num_channels, bytes_per_sample, sample_rate
            )

            # Play the audio
            play_obj = wave_obj.play()
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
        query = await self._generate_query(text)
        audio = await self._synthesize_speech(query)
        await self.play_speech(audio)


async def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(funcName)s: line %(lineno)d: %(message)s",
    )
    try:
        client = VoicevoxClient()
        await client.create_play_speech("hello")

    except (
        ConfigError,
        GenerateQueryError,
        CreateSpeechError,
        WriteSpeechFileError,
        PlaySpeechError,
        Exception,
    ) as e:
        logger.error(f"{type(e).__name__}:{e}")


if __name__ == "__main__":
    asyncio.run(main())
