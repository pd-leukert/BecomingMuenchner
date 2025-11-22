from setuptools import setup

setup(
    name="verity_check",
    version="0.1.0",
    packages=["verity_check"],
    package_dir={"verity_check": "."},
    install_requires=[
        "networkx",
        "pdf2image",
        "Pillow",
        "requests",
    ],
)
