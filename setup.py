import os
from setuptools import setup

here = os.path.abspath(os.path.dirname(__file__))

def read(fname):
    return open(os.path.join(here, fname)).read()

setup(
    name="pyscatter3d",
    version="0.0.0",
    author="Vlas Sokolov",
    author_email="vlas145@gmail.com",
    description=("Visualize csv files in 3D with plotly and matplotlib."),
    long_description=read('README.md'),
    license="MIT",
    url="https://github.com/vlas-sokolov/pyscatter3d",
    packages=["pyscatter3d", "examples"],
)
