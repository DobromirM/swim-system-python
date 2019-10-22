import setuptools

with open('README.md', 'r') as fh:
    long_description = fh.read()

setuptools.setup(
    name='swim',
    version='0.0.1.dev1',
    author='Dobromir Marinov',
    author_email='dobromir@swim.it',
    description='Standalone Python framework for building massively real-time streaming WARP clients.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/DobromirM/swim-system-python',
    packages=setuptools.find_packages(exclude=['test']),
    classifiers=[
        'Programming Language :: Python :: 3',
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
    ],
    keywords='swim client',
    install_requires=['websockets==8.0.2'],
)