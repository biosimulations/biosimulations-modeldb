import re
import setuptools
import subprocess
import sys
try:
    result = subprocess.run(
        [sys.executable, "-m", "pip", "show", "pkg_utils"],
        check=True, capture_output=True)
    match = re.search(r'\nVersion: (.*?)\n', result.stdout.decode(), re.DOTALL)
    assert match and tuple(match.group(1).split('.')) >= ('0', '0', '5')
except (subprocess.CalledProcessError, AssertionError):
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "-U", "pkg_utils"],
        check=True)
import os
import pkg_utils

name = 'biosimulations_modeldb'
dirname = os.path.dirname(__file__)
package_data = {
    name: [
        os.path.join('final', '*.yml'),
    ],
}

# get package metadata
md = pkg_utils.get_package_metadata(dirname, name, package_data_filename_patterns=package_data)

# install package
setuptools.setup(
    name='biosimulations-modeldb',
    version=md.version,
    description=(
        "Command-line program for publishing the ModelDB model repository to BioSimulations."
    ),
    long_description=md.long_description,
    url="https://github.com/biosimulations/biosimulations-modeldb",
    download_url='https://github.com/biosimulations/biosimulations-modeldb',
    author='Center for Reproducible Biomedical Modeling',
    author_email="info@biosimulations.org",
    license="MIT",
    keywords=[
        'neuroscience',
        'systems biology',
        'computational biology',
        'mathematical modeling',
        'numerical simulation',
        'XPP',
        'ModelDB',
    ],
    packages=setuptools.find_packages(exclude=['tests', 'tests.*']),
    package_data=md.package_data,
    install_requires=md.install_requires,
    extras_require=md.extras_require,
    tests_require=md.tests_require,
    dependency_links=md.dependency_links,
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Topic :: Scientific/Engineering :: Bio-Informatics',
    ],
    entry_points={
        'console_scripts': [
            'biosimulations-modeldb = biosimulations_modeldb.__main__:main',
        ],
    },
)
