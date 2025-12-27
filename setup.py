"""Setup configuration for chromecast_agc package."""

from setuptools import find_packages, setup

setup(
    name="chromecast-agc",
    version="0.1.0",
    description="Automatic Gain Control for Chromecast based on audio analysis",
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=[
        "numpy",
        "sounddevice",
        "pychromecast",
    ],
)

