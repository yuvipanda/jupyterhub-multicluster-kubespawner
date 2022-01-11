from setuptools import find_packages
from setuptools import setup

setup(
    name='jupyterhub-multicluster-kubespawner',
    version='0.1',
    install_requires=[
        'escapism',
        'python-slugify',
        'jupyterhub>=2.0',
        'jinja2',
        'ruamel.yaml',
    ],
    python_requires='>=3.6',
    description='JupyterHub Spawner for spawning into multiple kubernetes clusters',
    url='http://github.com/jupyterhub/kubespawner',
    author='Yuvi Panda',
    author_email='yuvipanda@gmail.com',
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    license='3-BSD',
    packages=find_packages(),
    project_urls={
        'Documentation': 'https://jupyterhub-kubespawner.readthedocs.io',
        'Source': 'https://github.com/jupyterhub/kubespawner',
        'Tracker': 'https://github.com/jupyterhub/kubespawner/issues',
    },
)
