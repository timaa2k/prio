import setuptools

with open("README.rst", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="prio",
    version="0.1.0",
    author="Tim Weidner",
    author_email="timaa2k@gmail.com",
    description="TaskPrio client library",
    long_description=long_description,
    long_description_content_type="text/x-rst",
    url="https://github.com/timaa2k/prio",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GPLv3 License",
        "Operating System :: OS Independent",
    ],
)
