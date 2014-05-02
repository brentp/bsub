from setuptools import setup

def get_version(path):
    """Get the version info from the mpld3 package without importing it"""
    import ast

    with open(path) as init_file:
        module = ast.parse(init_file.read())

    version = (ast.literal_eval(node.value) for node in ast.walk(module)
               if isinstance(node, ast.Assign)
               and node.targets[0].id == "__version__")
    try:
        return next(version)
    except StopIteration:
        raise ValueError("version could not be located")


setup(
    name = "bsub",
    version = get_version("bsub/__init__.py"),
    author = "Brent Pedersen, Joe Brown",
    author_email = "bpederse@gmail.com",
    description = ("submit jobs to LSF with python"),
    license = "MIT",
    keywords = "cluster lsf bsub",
    url = "https://github.com/brentp/bsub",
    packages=['bsub'],
    requires=['six'],
    long_description=open('README.md').read(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Topic :: Utilities",
        "License :: OSI Approved :: MIT License",
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3'
    ],
)
