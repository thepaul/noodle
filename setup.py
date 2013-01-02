# setup.py for Noodle

from distutils.core import setup, Distribution
from distutils.command import install, install_lib, build_py
import sys, os

class NoodleDistribution(Distribution):
    def __init__(self, *args, **kwargs):
        Distribution.__init__(self, *args, **kwargs)
        self.cmdclass['install'] = NoodleInstall
        self.cmdclass['install_nu'] = NoodleInstallNu
        self.cmdclass['build_nu'] = NoodleBuild

class NoodleInstall(install.install):
    def run(self):
        install.install.run(self)
        self.run_command('install_nu')

class NoodleInstallNu(install_lib.install_lib):
    description = "byte-compile noodle modules"
    user_options = []
    boolean_options = []
    negative_opt = []

    def run(self):
        self.run_command('build_ext')
        self.run_command('build_nu')
        noodledir = os.path.join(self.install_dir, 'Noodle')
        sys.path.insert(0, self.install_dir)
        import Noodle
        from Noodle import nucfiles, NoodleMain
        for nuc in self.distribution.nuc_files:
            if nuc.endswith(Noodle.extension):
                infile = os.path.join(noodledir, nuc)
                print "byte-compiling %s" % infile
                outfile = nucfiles.nuc_filename(infile)
                NoodleMain.noodle_to_nuc(infile, outfile)

class NoodleBuild(build_py.build_py):
    description = "collect noodle module filenames"
    user_options = []
    boolean_options = []
    negative_opt = []

    def run(self):
        self.distribution.nuc_files = []
        for pkg, src_dir, build_dir, filenames in self.data_files:
            if pkg == 'Noodle':
                self.distribution.nuc_files.extend(filenames)

setup(
    name='Noodle',
    version='0.1.0a1',
    description='Noodle Compiler and Runtime',
    author='paul cannon',
    author_email='paul@nafpik.com',
    packages=['Noodle'],
    package_data={'Noodle': ['*.nu']},
    scripts=[
        'scripts/noodle',
        'scripts/disnoodle',
        'scripts/dispyc',
        'scripts/runnable_nuc',
        'scripts/readnoodle'
    ],
    distclass=NoodleDistribution
)
