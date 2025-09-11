from setuptools import setup, find_packages

setup(
    name="edge-tts-client",
    version="1.0.1",
    license="MIT",
    url="https://github.com/suzuki-aki-rin/tts-clients/edge-tts-client",
    packages=find_packages(),
    install_requires=[
        "edge-tts~=7.2.3",
        "audioop-lts~=0.2.2",
        "pydub~=0.25.1",
        "simpleaudio-patched~=1.0.5",
        "tts-shared @ git+https://github.com/suzuki-aki-rin/tts-clients.git@main#egg=tts-shared&subdirectory=tts-shared",
    ],
    python_requires="~=3.13",
)
