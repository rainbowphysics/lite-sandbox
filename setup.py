import setuptools
from setuptools import setup

with open('requirements.txt', 'r') as fd:
    requirements = fd.readlines()

setup(
    name='lite-sandbox',
    version='0.0.1',
    description='Lightweight sandboxing in Python for Python script test',
    url='https://github.com/rainbowphysics/lite-sandbox',
    author='Physics System',
    author_email='rainbowphysicsystem@gmail.com',
    license='MIT License',
    packages=setuptools.find_packages(),
    install_requires=requirements,

    # https://pypi.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        'Development Status :: 1 - Planning',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: POSIX :: Linux',
        'Operating System :: Microsoft :: Windows',
        'Programming Language :: Python :: 3',
        'Topic :: Security',
        'Environment :: Plugins',
    ]
)