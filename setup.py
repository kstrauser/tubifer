from setuptools import setup

setup(
    name='tubifer',
    version='0.0.1',
    description='Calculate ISP data costs, including overages',
    author='Kirk Strauser',
    author_email='kirk@strauser.com',
    license='MIT',
    packages=['tubifer'],
    package_data={
        'tubifer': ['data/providers.json'],
    },
    entry_points={
        'console_scripts': {
            'show-data-prices = tubifer.evaluate:show_data_prices',
        }
    },
    test_suite='tests',
    zip_safe=True,
)
