# Always prefer setuptools over distutils
from setuptools import setup, find_packages

requires = ["cairosvg", "pycairo"]

VERSION = "1.1.1"
setup(
    name="ascidia",
    packages=find_packages(exclude=["contrib", "docs", "tests"]),
    version=VERSION,  # Ideally should be same as your GitHub release tag varsion
    description="A command-line utility for rendering technical diagrams from ASCII art",
    author="Mark Frimston; Kazuki Yamamoto",
    author_email="Frimkron@github.com; k.yamamoto.08136891@gmail.com",
    url="https://github.com/K4zuki/Ascidia",
    license="MIT",
    install_requires=requires,
    keywords=["pandoc", "markdown", "blockdiag"],
    classifiers=["Development Status :: 4 - Beta",
                 "Programming Language :: Python :: 3.5",
                 "Programming Language :: Python :: 3.6",
                 ],
    python_requires=">=3.5,!=3.0.*,!=3.1.*,!=3.2.*",
    # To provide executable scripts, use entry points in preference to the
    # "scripts" keyword. Entry points provide cross-platform support and allow
    # pip to create the appropriate form of executable for the target platform.
    entry_points={
        "console_scripts": [
            "ascidia=ascidia.ascidia:main",
        ],
    },
)
