"""Set up pydroid_ipcam package."""
from pathlib import Path

from setuptools import setup

PROJECT_DIR = Path(__file__).parent.resolve()
README_FILE = PROJECT_DIR / "README.md"
REQUIRES = ["aiohttp>=3.6.2"]


setup(
    name="pydroid-ipcam",
    version="2.0.0",
    license="Apache License 2.0",
    url="https://github.com/home-assistant-libs/pydroid-ipcam",
    author="Pascal Vizeli",
    author_email="pvizeli@syshack.ch",
    description="Library for handling the Android IP Webcam app",
    long_description=README_FILE.read_text(encoding="utf-8"),
    long_description_content_type="text/markdown",
    packages=["pydroid_ipcam"],
    package_data={"pydroid_ipcam": ["py.typed"]},
    python_requires=">=3.8",
    zip_safe=True,
    platforms="any",
    install_requires=REQUIRES,
    classifiers=[
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)
