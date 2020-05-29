import setuptools

with open('README.md', 'r') as fh:
    long_description = fh.read()

setuptools.setup(
    name='hyperband-snakemake',
    version='0.0.1',
    author='e-dorigatti',
    author_email='emilio.dorigatti@gmail.com',
    description='Orchestrate hyper-parameters search with snakemake',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/e-dorigatti/hyperband-snakemake/',
    packages=setuptools.find_packages(),
    package_data={'hyperband_snakemake': ['templates/*']},
    install_requires=[
        'click>=7.1.2',
        'jinja2>=2.11.2',
    ],
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
)

