from setuptools import setup, find_packages

setup(
    name='isimws',
    packages=find_packages(),
    # Date of release used for version - please be sure to use YYYY.MM.DD.seq#, MM and DD should be two digits e.g.
    # 2017.02.05.0 seq# will be zero unless there are multiple release on a given day - then increment by one for
    # additional release for that date
    version='2019.12.12.0',
    description='Idempotent functions for IBM Security Identity Manager SOAP web services',
    author='IBM',
    author_email='griffins@au1.ibm.com',
    url='',
    classifiers=[
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.7',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Development Status :: 2 - Pre-Alpha',
        'Environment :: Console',
        'Intended Audience :: System Administrators',
        'Topic :: Software Development :: Build Tools'
    ],
    zip_safe=False,
    install_requires=[
        'requests',
        'zeep'
    ]
)
