
import sys
from os import path

from setuptools import setup, find_packages

this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()


install_requires = [
    "wheel",
    "PyQt5==5.15.4",
    "pyqt-darktheme==1.2.3"
]

# Require python 3.7
if sys.version_info.major != 3 and sys.version_info.minor < 7:
    sys.exit("'Ayolo' requires Python >= 3.7!")

setup(
    name="ayolo",
    version="0.1.1",
    author="Paaksing",
    author_email="paaksingtech@gmail.com",
    url="https://github.com/paaksing/ayolo",
    description="PyQt5 based annotation tool for yolov4 datasets, providing fast and easy ways of annotating.",
    long_description=long_description,
    long_description_content_type='text/markdown',
    keywords=["yolov4", "annotating", "annotations", "DNN", "deep learning"],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Programming Language :: Python :: 3.7",
        "Environment :: X11 Applications :: Qt",
        "Operating System :: OS Independent",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Topic :: Multimedia :: Graphics :: Editors",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Scientific/Engineering :: Image Recognition",
        "Topic :: Scientific/Engineering :: Image Processing",
        "Topic :: Utilities",
        "Natural Language :: English",
    ],
    license="MIT",
    packages=find_packages(exclude=("sample_dir")),
    zip_safe=True,
    install_requires=install_requires,
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'ayolo=ayolo.commands:execute_from_cmd'
        ]
    }
)
