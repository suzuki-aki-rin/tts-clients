# tts-clients

Clients for TTS services

## CLients

### edge-tts-client

- pydub may need ffmpeg.
- install

```bash
pip install git+https://github.com/suzuki-aki-rin/tts-clients.git#subdirectory=edge-tts-client
```

- Check the available voice list

```bash
edge-tts --list-voices
```

### voicevox-client

  Needs Voicevox engine server.
  See <https://github.com/VOICEVOX/voicevox_engine> .

- install

```bash
pip install git+https://github.com/suzuki-aki-rin/tts-clients.git#subdirectory=voicevox-client
```

## Requirements

See each setup.py

## Usage

```python
# An example for EdgeTTSClient.
# If VoicevoxClient, use VoicevoxClient and VoicevoxConfig
# Function names are common.

# Initiate
config = EdgeTTSConfig(voice="en-US-ChristopherNeural")
tts_client = EdgeTTSClient(config)

# Create and play speech
await tts_client.create_play_speech("hello")

# Update config
tts_client.update_config(voice="en-US-MonicaNeural")

# Create speech file
speech = await tts_client.create_speech(text="hello", output_file="hello.mp3")

# Play speech
await tts_client.play_speech(speech)
```
