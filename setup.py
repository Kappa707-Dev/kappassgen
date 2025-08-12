from setuptools import setup, find_packages

setup(
    name="kappassgen",
    version="0.5.6",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    install_requires=[
        "PyGObject",
    ],
    entry_points={
        "console_scripts": [
            "kappassgen = kappassgen.main:main",
        ],
    },
    author="Kappa707-Dev",
    author_email="kappa707@proton.me",
    description="Generador de contraseñas con GTK4 y libadwaita",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/Kappa707-Dev/kappassgen",
    license="MIT",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Environment :: X11 Applications :: GTK",
        "Operating System :: POSIX :: Linux",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.8",
    include_package_data=True,
    package_data={
        "kappassgen": ["data/*.txt"],
    },
)

