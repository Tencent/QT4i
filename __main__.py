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
'''QT4i egg命令行接口(仅供UISpy使用)
'''


import sys
import os


proj_root = os.path.dirname(os.path.abspath(__file__))
pythonpaths = []
srcpypath = os.environ.get('PYTHONPATH', '')
exlib_dir = os.path.dirname(proj_root)
for filename in os.listdir(exlib_dir):
    if filename.endswith('.egg'):
        lib_path = os.path.join(exlib_dir, filename)
        if os.path.isfile(lib_path) and lib_path not in sys.path:
            sys.path.insert(0, lib_path)
            pythonpaths.append(lib_path)

os.environ['PYTHONPATH'] = srcpypath + ':'.join(pythonpaths)


if __name__ == '__main__':
    from testbase.management import ManagementTools
    ManagementTools().run()