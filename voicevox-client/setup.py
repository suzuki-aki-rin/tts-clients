from setuptools import setup, find_packages

setup(
    name="voicevox-tts-client",
    version="1.0.1",
    license="MIT",
    url="https://github.com/suzuki-aki-rin/tts-clients/voicevox-client",
    packages=find_packages(),
    install_requires=[
        "simpleaudio-patched~=1.0.5",
        "httpx~=0.28.1",
        "tts-shared @ git+https://github.com/suzuki-aki-rin/tts-clients.git@main#egg=tts-shared&subdirectory=tts-shared",
    ],
    python_requires="~=3.13",
)
