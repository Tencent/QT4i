# coding: UTF-8
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
# -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*-
'''Base API'''
# 2014/08/30    cherry    创建
# -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*-
import re
# -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*-

class Register(object):
    
    def __init__(self, _server=None):
        self._server = _server

    def _register_functions(self, _api_prefix, _ignore_name_patterns=[]):
        _ignore_name_patterns = '|'.join(['^_.+$', '^register$'] + _ignore_name_patterns)
        for _name in dir(self):
            _item = getattr(self, _name)
            if callable(_item) and False == bool(re.match(_ignore_name_patterns, _name)):
                if self._server is not None and hasattr(self._server, 'register_function'):
                    self._server.register_function(_item, '%s.%s' % (_api_prefix, _name))

    def register(self):pass
