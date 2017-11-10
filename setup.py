#!/usr/bin/env python3

import os
from setuptools import setup
import tenzing

packages = ['infernalis','infernalis/cli','infernalis/core']
package_dir = {p: 'src/' + p for p in packages}

scripts = [os.path.join('scripts', f) for f in os.listdir('scripts') if not '~' in f and not '#' in f]

setup(name='infernalis',
      version='0.0.1',
      description='Interactive shell daemonizer.',
      author='Steve Norum',
      author_email='stevenorum@gmail.com',
      url='www.stevenorum.com',
      packages=packages,
      package_dir=package_dir,
      scripts=scripts,
      test_suite='tests',
      cmdclass = {'upload':tenzing.Upload},
      install_requires=[
          'pexpect',
          'calvin'
      ]
)
