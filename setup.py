from setuptools import setup

setup(
    name='rdsdbsnap',
    version='0.1.2',
    py_modules=['rdsdbsnap'],
    install_requires=[
        'Click',
        'boto3',
    ],
    entry_points='''
        [console_scripts]
        rdsdbsnap=rdsdbsnap:cli
    ''',

    # metadata for upload to PyPI
    author="Grzegorz Adamowicz",
    author_email="gadamowicz@gstlt.info",
    description="Tool for managing Amazon RDS snapshots",
    license="MIT",
    keywords="aws rds snapshot cli",
    url="https://github.com/gstlt/rdsdbsnap",
)

