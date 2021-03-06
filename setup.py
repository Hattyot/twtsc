import setuptools

setuptools.setup(
    name="twtsc",
    version="0.0.4",
    author="Hattyot",
    description="Simple twitter scraper inspired and based on twint",
    url="https://github.com/Hattyot/twtsc",
    project_urls={
        "Bug Tracker": "https://github.com/Hattyot/twtsc/issues"
    },
    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src"),
    python_requires=">=3.9",
)