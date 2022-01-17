from setuptools import find_packages
from setuptools import setup

setup(
    name="jupyterhub-multicluster-kubespawner",
    version="0.1",
    install_requires=[
        "escapism",
        "jupyterhub>=1.5",
        "jinja2",
        "ruamel.yaml",
        "traitlets",
    ],
    python_requires=">=3.9",
    description="JupyterHub Spawner for spawning into multiple kubernetes clusters",
    url="https://github.com/yuvipanda/jupyterhub-multicluster-kubespawner",
    author="Yuvi Panda",
    author_email="yuvipanda@gmail.com",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    license="3-BSD",
    packages=find_packages(),
    project_urls={
        "Source": "https://github.com/yuvipanda/jupyterhub-multicluster-kubespawner",
        "Tracker": "https://github.com/yuvipanda/jupyterhub-multicluster-kubespawner/issues",
    },
)
