from setuptools import setup

setup(
    name='burp2json',
    version='1.0',    
    description='Burp2Json Python Module',
    url='https://github.com/gremwell/burp2json',
    author='Alla Bezroutchko',
    author_email='alla@gremwell.com',
    license='GNU GPL',
    packages=['burp2json'],
    install_requires=[
                      'requests',
                      'urllib3'                     
                      ],

    classifiers=[
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
)
