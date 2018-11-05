# -*- coding:utf-8 -*-
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
'''QPath
'''


import re, sys


class QPath(str):
    '''QPath基类
    '''
    
    def __init__(self, qpath=None):
        '''构造函数
        
        :param qpath: QPath字符串
        :type qpath: string
        '''
        # -*-
        pattern = '|'.join(['＝', '～', '！'])
        result = re.search(pattern, qpath, re.I)
        if result : 
            sys.stderr.write('警告: QPath中含有中文关系运算符 [%s] in [ %s ]\n' % (result.group(), qpath))
        self._qpath = qpath


    def __str__(self):
        '''获取qpath字符串，实例化控件时调用server.find时传参为qpath字符串
        '''
        return self._qpath