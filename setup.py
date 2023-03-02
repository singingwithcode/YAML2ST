from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

classifiers = [
    "Programming Language :: Python :: 3",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent"
]

setup(
    name="YAML2ST",
    version="1.0.20",
    description="YAML2ST automates streamlit input widgets from a YAML.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/singingwithcode/YAML2ST",
    author="Matthew Klich, Kelly Anderson",
    author_email="m@matthewklich.com",
    package_dir={"": "app/src"},
    packages=find_packages(),
    py_modules=["YAML2ST"], 
    install_requires=[
        'PyYAML'
    ],
    classifiers=classifiers,
)