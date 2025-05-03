from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

with open("requirements.txt", "r") as fh:
    requirements = fh.read().splitlines()

setup(
    name="message-database",
    version="1.0.0",
    description="A utility for retrieving, processing, and storing messages from the Hostaway API to MongoDB",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Hostaway",
    author_email="your.email@example.com",
    url="https://github.com/yourusername/message-database",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=[
        "python-dotenv>=1.0.0",
        "requests>=2.25.1",
        "pymongo[srv]>=4.3.3",
        "pydantic>=2.0.0",
        "certifi>=2023.5.7",
        "python-dateutil>=2.8.2"
    ],
    entry_points={
        "console_scripts": [
            "message-etl=message_database.main:main",
        ],
    },
) 