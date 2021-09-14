from setuptools import setup, find_packages
from pathlib import Path

with open(Path(__file__).parent / "requirements.in") as f:
    requirements = [l.strip() for l in f.readlines() if not l.strip().startswith("#")]

setup(
    name="docker-image-cleaner",
    version="1.0.0",
    python_requires=">=3.6",
    author="Project Jupyter Contributors",
    author_email="jupyter@googlegroups.com",
    license="BSD",
    packages=find_packages(),
    url="https://github.com/jupyterhub/docker-image-cleaner",
    description="Cleanup old docker images to free up disk space and inodes",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "docker-image-cleaner = docker_image_cleaner.__main__:main",
        ]
    },
)
