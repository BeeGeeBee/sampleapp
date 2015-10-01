#from distutils.core import setup
from setuptools import setup, find_packages

setup(
    name='Components',
    version='0.1',
    packages = find_packages(),
    url='',
    license='',
    author='bernie',
    author_email='',
    description='',
    include_package_data = True,
    package_data = {
        '': ['*.html', '*.db'],
        'docs': ['*.pdf']
    },
    install_requires = ['Flask',
        'Flask-Script',
        'Flask-SQLAlchemy',
        'WTForms'
        ]

)
