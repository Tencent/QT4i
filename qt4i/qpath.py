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
# 2014/05/11    celery      完成App的定义
# 2014/07/22    cherry    增加警告QPath是否含有中文关系运算符

# -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*-

import re, sys
from tuia.qpathparser import QPathParser

# -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*- -*-

class QPath(str):
    '''QPath基类
    '''
    parser = QPathParser()
    
    def __init__(self, qpath=None):
        '''构造函数
        
        :param qpath: QPath字符串
        :type qpath: string
        '''
        # -*-
        pattern = '|'.join(['＝', '～', '！'])
        result = re.search(pattern, qpath, re.I)
        if result : sys.stderr.write('警告: QPath中含有中文关系运算符 [%s] in [ %s ]\n' % (result.group(), qpath))
        # -*-
        # if qpath:
        #     parsed_qpath, _ = self.parser.parse(qpath)
        #     locators = []
        #     for locator in parsed_qpath:
        #         props = []
        #         for propname in locator:
        #             prop = locator[propname]
        #             props.append('%s%s\'%s\''%(propname, prop[0], prop[1]))
        #         locators.append(' && '.join(props))
        #     qpath = '/' + ' /'.join(locators)
        self._qpath = qpath


    def __str__(self):
        '''获取qpath字符串，实例化控件时调用server.find时传参为qpath字符串
        '''
        return self._qpath