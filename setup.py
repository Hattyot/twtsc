import setuptools

setuptools.setup(
    name="balance_snapshotter",
    version="0.0.2",
    author="Hattyot",
    description="Simple twitter scraper inspired and based on twint",
    url="https://github.com/Hattyot/twtsc",
    project_urls={
        "Bug Tracker": "https://github.com/Hattyot/twtsc/issues"
    },
    package_dir={"": "twtsc"},
    packages=setuptools.find_packages(where="twtsc"),
    python_requires=">=3.9",
)