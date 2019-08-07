import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="sensirion sps030",
    version="0.0.7",
    author="Florentin Bulot",
    author_email="f.bulot@soton.ac.uk",
    description="An interface for Sensirion SPS030 particulate matter sensors",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/FEEprojects/sensirion-sps030",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
     python_requires='>=3.3, <4',
     install_requires=['pyserial']
)
