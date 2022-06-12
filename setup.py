# coding: utf-8

from setuptools import setup
import karas

with open("README.md", "r") as f:
    readme = f.read()

setup(
    name="karas_py",
    version=karas.__version__,
    author="ShiroDoMain",

    keywords="qqbot async",
    long_description=readme,
    long_description_content_type="text/markdown",

    author_email="b1808107177@gmail.com",
    url='https://github.com/ShiroDoMain/Karas',
    license='GNU Affero General Public License v3.0',
    description="一个基于mirai-api-http的高性能qq机器人框架",
    packages=["karas", "karas.util"],
    install_requires=[
        "aiohttp>=3.8.1"
    ],
    classifiers=[
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ]
)
