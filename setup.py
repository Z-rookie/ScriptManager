#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

setup(
    name="script-manager",
    version="0.1.0",
    description="管理Ubuntu服务器上运行的脚本程序",
    author="ScriptManager",
    packages=find_packages(),
    install_requires=[
        "psutil>=5.9.0",
        "tabulate>=0.8.10",
    ],
    entry_points={
        "console_scripts": [
            "sm=script_manager:main",
        ],
    },
    python_requires=">=3.6",
)