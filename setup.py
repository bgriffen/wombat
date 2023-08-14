from setuptools import setup

setup(
    name="wombat",
    version="0.1",
    description="A Python toolkit designed help answer geospatial related questions about Australian cities and regions.",
    author="Brendan Griffen",
    author_email="@brendangriffen",
    packages=["wombat"],
    install_requires=['wget', 'tqdm'],
)
