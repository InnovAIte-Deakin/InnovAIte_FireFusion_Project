"""
FireFusion Data Engineering Setup
"""
from setuptools import setup, find_packages

setup(
    name="firefusion-de",
    version="0.1.0",
    description="FireFusion Data Engineering - MVP ETL Pipeline",
    author="FireFusion Data Engineering Team",
    author_email="deakin.firefusion@deakin.edu.au",
    python_requires=">=3.8",
    packages=find_packages(),
    install_requires=[
        "pandas>=1.3.0",
        "numpy>=1.21.0",
        "requests>=2.26.0",
    ],
    entry_points={
        "console_scripts": [
            "firefusion-pipeline=mvp_pipeline:main",
        ],
    },
)