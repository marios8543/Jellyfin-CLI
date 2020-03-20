import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name='Jellyfin-CLI',
    version='1.2',
    scripts=['jellyfin-cli'],
    author="marios8543",
    author_email="marios8543@gmail.com",
    description="A Jellyfin command line client.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/marios8543/Jellyfin-CLI",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
         "License :: OSI Approved :: MIT License",
         "Operating System :: OS Independent",
    ],
    entry_points={
        "console_scripts": [
            "jellyfin-cli = jellyfin_cli.main:app"
        ]
    },
    install_requires=[
        "aiohttp",
        "urwid",
        "aio-mpv-jsonipc"
    ]
)
