"""
Tencent Speech SDK Local Package

本地包装包，用于安装和管理腾讯语音SDK
"""
from setuptools import setup, find_packages
import os

# 获取项目根目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(BASE_DIR))

setup(
    name="tencent-speech-sdk",
    version="1.0.0",
    description="Tencent Cloud Speech SDK wrapper (local package)",
    long_description="""
    腾讯云语音SDK的本地包装包。
    
    此包将vendor目录中的腾讯语音SDK包装为可安装的Python包，
    方便在项目中使用。
    """,
    author="CozyChat Team",
    packages=find_packages(),
    install_requires=[
        "websocket-client==0.48",  # 必须0.48版本
        "requests>=2.28.0",
    ],
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)

