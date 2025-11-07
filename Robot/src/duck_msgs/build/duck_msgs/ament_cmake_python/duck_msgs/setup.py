from setuptools import find_packages
from setuptools import setup

setup(
    name='duck_msgs',
    version='0.0.0',
    packages=find_packages(
        include=('duck_msgs', 'duck_msgs.*')),
)
