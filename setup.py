from distutils.core import setup

setup(
    name = 'nicm',
    version = '0.1',
    author = 'Caleb Wang',
    author_email = 'cw@berkeley.edu',
    packages = ['nicm', 'nicm.tests'],
    scripts = ['scripts/nicm_cmd.py'],
    license = 'LICENSE.txt',
    install_requires = ['nibabel', 'nipype']
)
