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
'''命令行参数解析
'''

import sys
import re
import six

class Args(dict):
    '''@desc: 命令行参数解析为字典（支持格式:  -key "value" -key=value --key "value" --key=value）
    '''
    RegPattern1 = '^\-{1,2}\w+\=.+$'
    RegPattern2 = '^\-{1,2}\w+$'
    RegPatternAll = '|'.join([RegPattern1, RegPattern2])
    
    def __init__(self, keys_to_lower=True):
        dict.__init__(self)
        self.keys_to_lower = keys_to_lower
        self.parse()
    
    def __convert__(self, item):
        if re.match('^\d+\.\d+$', item)                          : return float(item)
        if re.match('^\d+$', item)                               : return int(item)
        if re.match('^True$', item, re.I)                        : return True
        if re.match('^False$', item, re.I)                       : return False
        if re.match('|'.join(['^None$', '^NULL$']), item, re.I)  : return None
        return item
    
    def update(self, _dict):
        if self.keys_to_lower:
            for (key, value) in six.iteritems(_dict):
                self[key.lower()] = value
        else:super(self.__class__, self).update(_dict)
    
    def parse(self):
        for i, item in enumerate(sys.argv):
            if re.match(self.RegPatternAll, item):
                if re.match(self.RegPattern1, item):
                    item = re.sub('^-+', '', item)
                    key = re.sub('=.+$', '', item)
                    value = re.sub('^\w+=', '', item)
                    if self.keys_to_lower : key = key.lower()
                    self.update({key:self.__convert__(value)})
                    continue
                if re.match(self.RegPattern2, item):
                    key = re.sub('^-+', '', item)
                    value = sys.argv[i + 1]
                    if self.keys_to_lower : key = key.lower()
                    self.update({key:self.__convert__(value)})
                    continue

