"""Setup script for Deep Researcher Agent."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="deep-researcher-agent",
    version="0.1.0",
    author="Deep Researcher Team",
    author_email="team@deepresearcher.ai",
    description="A local AI-powered research system for comprehensive information analysis",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/deepresearcher/deep-researcher-agent",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Text Processing :: Indexing",
        "Topic :: Office/Business :: Office Suites",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "deep-researcher=deep_researcher.cli:cli",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)