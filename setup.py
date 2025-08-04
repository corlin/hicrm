"""
HiCRM项目安装配置
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="hicrm",
    version="0.1.0",
    author="HiCRM Team",
    author_email="team@hicrm.com",
    description="对话式智能CRM系统 - 基于LLM和RAG技术的智能客户关系管理平台",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/corlin/hicrm",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Framework :: FastAPI",
        "Topic :: Office/Business :: Financial :: Point-Of-Sale",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    python_requires=">=3.11",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.4.3",
            "pytest-asyncio>=0.21.1",
            "pytest-cov>=4.1.0",
            "black>=23.11.0",
            "isort>=5.12.0",
            "flake8>=6.1.0",
            "mypy>=1.7.1",
        ],
        "docs": [
            "mkdocs>=1.5.3",
            "mkdocs-material>=9.4.8",
        ],
    },
    entry_points={
        "console_scripts": [
            "hicrm=src.main:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)