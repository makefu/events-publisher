import sys
from setuptools import setup

setup(
    name='shack_announce',
    version='0.0.8',

    description='announce event-o-mat events',
    long_description=open("README.md").read(),
    license='WTFPL',
    url='http://krebsco.de/',
    author='makefu',
    author_email='spam@krebsco.de',
    install_requires = [
            "Mastodon.py",
            "facebook-sdk",
            "requests",
            "twitter",
            "docopt",
            "pytz"
        ],
    setup_requires = [
        "black"
    ],
    packages=['shack_announce','shack_announce.announce'],
    entry_points={
        'console_scripts' : [
            'announce-daemon = shack_announce.daemon:main'
            ]
        },

    classifiers=[
        "Intended Audience :: Developers",
        "Natural Language :: English",
        "Operating System :: POSIX :: Linux",
        "Development Status :: 3 - Alpha",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: Implementation :: CPython",
    ],
)

