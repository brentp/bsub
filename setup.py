from setuptools import setup

setup(
    name = "bsub",
    version = "0.2",
    author = "Brent Pedersen, Joe Brown",
    author_email = "bpederse@gmail.com",
    description = ("submit jobs to LSF with python"),
    license = "MIT",
    keywords = "cluster lsf bsub",
    url = "https://github.com/brentp/bsub",
    packages=['bsub'],
    long_description=open('README.md').read(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Topic :: Utilities",
        "License :: OSI Approved :: MIT License",
    ],
)
