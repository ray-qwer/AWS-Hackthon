from setuptools import setup, find_packages

setup(
    name="aws-hackathon",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "boto3>=1.28.0",
        "aws-lambda-powertools>=2.30.0",
        "line-bot-sdk>=3.0.0",
        "requests>=2.31.0",
        "python-dotenv>=1.0.0",
        "tenacity>=8.2.3",
        "numpy>=1.24.0",
        "pandas>=2.0.0",
        "pydub>=0.25.1",
        "librosa>=0.10.0",
        "Pillow>=10.0.0",
        "opencv-python>=4.8.0",
    ],
    python_requires=">=3.11",
) 