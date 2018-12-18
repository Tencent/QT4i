# -*- coding: utf-8 -*-
#
# Tencent is pleased to support the open source community by making QTA available.
# Copyright (C) 2016THL A29 Limited, a Tencent company. All rights reserved.
# Licensed under the BSD 3-Clause License (the "License"); you may not use this 
# file except in compliance with the License. You may obtain a copy of the License at
# 
# https://opensource.org/licenses/BSD-3-Clause
# 
# Unless required by applicable law or agreed to in writing, software distributed 
# under the License is distributed on an "AS IS" basis, WITHOUT WARRANTIES OR CONDITIONS
# OF ANY KIND, either express or implied. See the License for the specific language
# governing permissions and limitations under the License.
#

import os
from setuptools import setup, find_packages, Command
from setuptools.command.bdist_egg import bdist_egg as orig_bdist_egg

DATA_PACKAGES = ["qt4i.driver"]
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def generate_version():
    version = '1.0.1'
    if os.path.isfile(os.path.join(BASE_DIR, "version.txt")):
        with open("version.txt", "r") as fd:
            content = fd.read().strip()
            if content:
                version = content
    return version


def parse_requirements():
    reqs = []
    if os.path.isfile(os.path.join(BASE_DIR, "requirements.txt")):
        with open(os.path.join(BASE_DIR, "requirements.txt"), 'r') as fd:
            for line in fd.readlines():
                line = line.strip()
                if line:
                    reqs.append(line)
    return reqs 


def get_description():
    with open(os.path.join(BASE_DIR, "README.md"), "r") as fh:
        return fh.read()


class bdist_egg(Command):
    """automatically update version number before build
    """
    user_options = []
    boolean_options = []
          
    def initialize_options (self):
        pass
    
    def finalize_options(self):
        pass

    def run(self):
        version = self.distribution.metadata.get_version()
        with open(os.path.join("qt4i", "version.py"), "w") as fd:
            fd.write('version = "%s"\n' % version)
        self.run_command("orig_bdist_egg")
   

if __name__ == "__main__":
    
    setup(
      version=generate_version(),
      name="qt4i",
      cmdclass={
        "bdist_egg": bdist_egg,
        "orig_bdist_egg": orig_bdist_egg,},      
      packages=find_packages(exclude=('tests','tests.*', 'debug', 'debug.*')),
      py_modules=["__main__"],
      include_package_data = True,
      data_files=[(".", ["requirements.txt", "version.txt"])],
      description="QTA driver for iOS app",
      long_description=get_description(),
      long_description_content_type="text/markdown",
      author="Tencent",
      license="Copyright(c)2010-2018 Tencent All Rights Reserved. ",
      install_requires=parse_requirements(),
      entry_points={
            'console_scripts': ['qt4i-manage = qt4i.cmds:qt4i_manage_main'],
      },
      classifiers=[
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
      ],
      url="https://github.com/Tencent/QT4i",
      project_urls={
        "QT4i Documentation":"https://qt4i.readthedocs.io/zh_CN/latest/"
      },
    )
